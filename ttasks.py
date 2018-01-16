"""Script for performing common tasks for the tt project."""

from __future__ import print_function

import doctest
import os
import platform
import subprocess
import sys
import tt
import unittest

from argparse import ArgumentParser, RawTextHelpFormatter
from contextlib import contextmanager


HERE = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(HERE, 'dist')
DOCS_DIR = os.path.join(HERE, 'docs')
USER_GUIDE_DIR = os.path.join(DOCS_DIR, 'user_guide')
TT_DIR = os.path.join(HERE, 'tt')
TESTS_DIR = os.path.join(TT_DIR, 'tests')


class AppVeyorApiError(Exception):
    """An exception type for failed interactions with the AppVeyor API."""


class SubprocessFailureError(Exception):
    """An exception type for a subprocess exiting with a non-zero exit code."""


class TestFailureError(Exception):
    """An exception type for failed tests."""


@contextmanager
def _cwd(new_cwd):
    """Context manager for temporarily changing the cwd."""
    old_cwd = os.getcwd()
    os.chdir(new_cwd)
    yield
    os.chdir(old_cwd)


def _print_sys_info():
    """Print a formatted notice of the current Python/system info to stdout."""
    py_runtime = ' '.join((platform.python_implementation(),
                           platform.python_version()))
    py_build_info = ', '.join(platform.python_build())
    os_info = ' '.join((platform.system(), platform.version()))

    print()
    print('System info')
    print('-----------')
    print('Runtime:', py_runtime)
    print('Build:', py_build_info)
    print('OS:', os_info)
    print()


def pull_latest_win_wheels():
    """Download the latest artifact Windows wheels from AppVeyor."""
    import requests

    token = os.environ.get('APPVEYOR_TOKEN')
    if token is None:
        print('You must set the APPVEYOR_TOKEN environment variable;',
              'quitting now', file=sys.stderr)
        raise AppVeyorApiError

    headers = {
        'Authorization': 'Bearer ' + token,
        'Content-type': 'application/json'
    }
    base_url = 'https://ci.appveyor.com/api'
    project_url = base_url + '/projects/welchbj/tt'
    artifacts_url_template = base_url + '/buildjobs/{}/artifacts'
    single_artifact_url_template = artifacts_url_template + '/{}'

    r = requests.get(project_url, headers=headers)
    if r.status_code != 200:
        print('Non-200 status code received from AppVeyor API; quitting now')
        raise AppVeyorApiError

    for job_dict in r.json()['build']['jobs']:
        job_id, job_name = job_dict['jobId'], job_dict['name']
        print('Processing job "', job_name, '"', sep='')

        r = requests.get(artifacts_url_template.format(job_id),
                         headers=headers)
        if r.status_code != 200:
            print('Non-200 status code received from AppVeyor API;',
                  'quitting now')
            raise AppVeyorApiError

        artifact_remote_path = r.json()[0]['fileName']
        artifact_filename = artifact_remote_path.split('/')[1]
        local_filename = os.path.join(DIST_DIR, artifact_filename)
        artifact_url = single_artifact_url_template.format(
            job_id, artifact_remote_path)

        print('Downloading', artifact_url, 'into', local_filename)
        r = requests.get(artifact_url, headers=headers)
        with open(local_filename, 'wb') as f:
            f.write(r.content)

        print('Done')
        print()

    print('All done!')


def build_docs():
    """Build the documentation from source into HTML."""
    with _cwd(DOCS_DIR):
        exit_code = subprocess.call('make html', shell=True)

    if exit_code:
        print('Something went wrong building the docs', file=sys.stderr)
        raise SubprocessFailureError


def serve_docs():
    """Serve the documentation on a local livereload server."""
    from livereload import Server
    server = Server()

    watch_patterns = ['docs/*.rst',
                      'docs/**/*.rst',
                      'docs/conf.py',
                      'README.rst',
                      'tt/**/*.py']
    for pattern in watch_patterns:
        server.watch(pattern, build_docs)

    server.serve(root='docs/_build/html', host='127.0.0.1', port=5000)


def test():
    """Run tt tests."""
    _print_sys_info()

    suite = unittest.defaultTestLoader.discover(
        TESTS_DIR,
        pattern='test_*.py',
        top_level_dir=HERE)

    doctest_modules = [
        tt.definitions.operands,
        tt.definitions.operators,
        tt.expressions.bexpr,
        tt.errors.arguments,
        tt.errors.evaluation,
        tt.errors.grammar,
        tt.errors.state,
        tt.errors.symbols,
        tt.satisfiability.picosat,
        tt.tables.truth_table,
        tt.transformations.bexpr,
        tt.transformations.utils,
        tt.trees.tree_node
    ]

    doctest_files = [
        os.path.join(USER_GUIDE_DIR, 'expression_basics.rst'),
        os.path.join(USER_GUIDE_DIR, 'table_basics.rst')
    ]

    if sys.version_info.major >= 3:
        # only test the readme in Python 3
        doctest_files.append(os.path.join(HERE, 'README.rst'))

    common_doctest_kwargs = dict(
        optionflags=doctest.IGNORE_EXCEPTION_DETAIL
    )

    for module in doctest_modules:
        suite.addTests(
            doctest.DocTestSuite(
                module,
                **common_doctest_kwargs))

    for file in doctest_files:
        suite.addTests(
            doctest.DocFileSuite(
                file,
                module_relative=False,
                **common_doctest_kwargs))

    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    if not result.wasSuccessful():
        raise TestFailureError


TASKS = {
    'build-docs': build_docs,
    'pull-latest-win-wheels': pull_latest_win_wheels,
    'serve-docs': serve_docs,
    'test': test
}


def get_parsed_args(args=None):
    """Get the parsed command line arguments.

    :param args: The command-line args to parse; if omitted,
        :data:`sys.argv <python:sys.argv>` will be used.
    :type args: List[:class:`str <python:str>`], optional

    :return: The :class:`Namespace <python:argparse.Namespace>` object holding
        the parsed args.
    :rtype: :class:`argparse.Namespace <python:argparse.Namespace>`

    """
    parser = ArgumentParser(
        prog='ttasks.py',
        description='Helper script for running tt project tasks (ttasks)',
        formatter_class=RawTextHelpFormatter)

    parser.add_argument(
        'task',
        action='store',
        metavar='TASK',
        type=str,
        choices=sorted(TASKS.keys()),
        help='the ttask to run')

    if args is None:
        args = sys.argv[1:]

    return parser.parse_args(args)


def main(args=None):
    """Main routine for running this script.

    :param args: The command-line arguments.
    :type args: List[:class:`str <python:str>`], optional

    :returns: The exit code of the program.
    :rtype: :class:`int <python:int>`

    """
    try:
        opts = get_parsed_args()
        task = TASKS[opts.task]
        task()
        return 0
    except (AppVeyorApiError, SubprocessFailureError, TestFailureError):
        return 1
    except Exception as e:
        print('Received unexpected exception; re-raising it.', file=sys.stderr)
        raise e


if __name__ == '__main__':
    sys.exit(main())
