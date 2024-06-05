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


