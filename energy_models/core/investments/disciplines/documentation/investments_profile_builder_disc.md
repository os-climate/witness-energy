# Investments Profile Builder

The Investments Profile Builder uses the following formulas :

1. Normalizing the coefficients:
    $$
    \text{coeff\_name} = \frac{\text{coeff\_val}}{\text{coeffs\_sum}}
    $$

2. Calculating the values to sum:
    $$
    \text{values\_to\_sum.append}(\text{coeff\_val} \times \text{df.values})
    $$

3. Computing the convex combination:
    $$
    \text{convex\_combination} = \sum \text{values\_to\_sum}
    $$

These calculations ensure that the investments are proportionally distributed based on the given coefficients.
The output investment profile can be exported either as a dataframe 'invest_mix' where the values of the variables
are provided for each year or as a 1D array per variable (named 'variable_array_mix') where the values are provided
only for a selected number of years referred to as the poles.
Therefore, the number of poles have to be provided by the user in the second case. To activate the second case,
the user must set to True the input variable 'export_invest_profiles_at_poles'
