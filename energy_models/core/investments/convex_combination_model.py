import numpy as np
import pandas as pd


class ConvexCombinationModel:
    def __init__(self):
        self.postive_coefficients: dict[str: float] = {}
        self.convex_coefficients: dict[str: float] = {}
        self.dataframes: list[pd.DataFrame] = []
        self.convex_combination_df: pd.DataFrame = None
        self.coeffs_sum : float = 0.

    def store_inputs(self,
                     positive_coefficients: dict[str: float],
                     dataframes: list[pd.DataFrame]):
        self.postive_coefficients = positive_coefficients
        self.dataframes = dataframes

    def compute_convex_coefficients(self):
        self.coeffs_sum = sum(self.postive_coefficients.values())
        if self.coeffs_sum <= 0:
            raise ValueError('Sum of the coefficients is non-positive')
        for coeff_name, coeff_val in self.postive_coefficients.items():
            if coeff_val < 0:
                raise ValueError(f'{coeff_name} is negative')
            self.convex_coefficients[coeff_name] = coeff_val / self.coeffs_sum

    def compute_convex_combination(self):
        values_to_sum = []
        for (coeff_name, coeff_val), df in zip(self.convex_coefficients.items(), self.dataframes):
            values_to_sum.append(coeff_val * df.values)

        convex_combination = np.sum(values_to_sum, axis=0)

        self.convex_combination_df = pd.DataFrame({
            'years': self.dataframes[0]['years'],
            **dict(zip(self.dataframes[0].columns, convex_combination.T)) # demander à Antoine
        })

    def compute(self):
        self.compute_convex_coefficients()
        self.compute_convex_combination()

    def _d_convex_coeff_d_linear_coeff(self, coeff_in: str, coeff_out: str):
        if coeff_in != coeff_out:
            derivative = - 1 / self.coeffs_sum ** 2
        else:
            derivative = (self.coeffs_sum - self.postive_coefficients[coeff_in]) / self.coeffs_sum ** 2

        return derivative

    def d_convex_combination_d_coeff_in(self, column: str, coeffname: str):
        derivatives = [self._d_convex_coeff_d_linear_coeff(coeff_in=coeffname, coeff_out=coeff_out) * df[column].values
                       for df, coeff_out in zip(self.dataframes, self.convex_coefficients)]
        derivative = np.sum(derivatives, axis=0)
        return derivative
