# Investments Distribution

The distribution of investments is made according to the investments level mix dataframe in input. Each coefficient for each energy/technology over the years is normalized by the sum of coefficients for one year and multiplied by the total investments level : 

$$energy\_investment = total\_investment * \frac{energy\_mix\_coefficient}{\sum energy\_mix\_coefficient}$$

