import unittest
from tt.eqtools import transform_eq_to_generic_schema

class TestTransformEqToGenericSchema(unittest.TestCase):

    def test_single_symbol_not(self):
        logically_equivalent_eqs = ["F = NOT A",
                                    "F = not A",
                                    "F = ~A",
                                    "F = ~ A",
                                    "F = !A",
                                    "F = ! A"]
        tt_schema_eq = "F=~A"
        for eq in logically_equivalent_eqs:
            transformed_eq = transform_eq_to_generic_schema(eq)
            self.assertEqual(transformed_eq, tt_schema_eq)
    
    def test_single_symbol_not_whitespace(self):
        logically_equivalent_eqs = ["F    =   NOT  A",
                                    "F=   not  A  ",
                                    "F  =    ~   A",
                                    "F=~A",
                                    "F = !    A   ",
                                    "F =      !A"]
        tt_schema_eq = "F=~A"
        for eq in logically_equivalent_eqs:
            transformed_eq = transform_eq_to_generic_schema(eq)
            self.assertEqual(transformed_eq, tt_schema_eq)
    
    def dtest_two_symbol_and(self):
        pass
    
    def dtest_two_symbol_and_parens(self):
        pass
    
    def dtest_two_symbol_or(self):
        pass
    
    def dtest_two_symbol_or_parens(self):
        pass
    
if __name__ == "__main__":
    unittest.main()