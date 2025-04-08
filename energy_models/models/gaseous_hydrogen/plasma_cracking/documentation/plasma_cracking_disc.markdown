# PlasmaCracking

## Introduction
The plasma cracking process consists in breaking the connection between the carbon and the hydrogen of the methane using high frequency microwaves. The reaction is the following:

$$CH_4  --> C + 2H_2$$




This process allows to extract solid carbon out of methane and if used with biomethane and electricity from renewable sources, it leads to negative $CO_2$ emissions.




![](plasmacracking.png)

## Gradient computation - Summary

H2_price : techno price \
X : percentage resource \
PC_cost : Plasma Cracking cost

### Formula:

$$H2_{price}= PC_{cost} * Margin * X$$

$$H2_{price}= PC_{cost}(invest, energy\_prices,energy\_CO2\_emission) * Margin$$
$$* X(invest, energy\_prices, all\_stream\_demand\_ratio, resources\_price)$$



### Gradients to compute:

  $$\dfrac {\partial H2_{price}}{\partial invest}= Margin * X * \dfrac {\partial PC_{cost}}{\partial invest}
  + PC_{cost} * Margin * \dfrac {\partial X}{\partial invest}$$

 $$\dfrac {\partial H2_{price}}{\partial energy\_prices}= Margin * X * \dfrac {\partial PC_{cost}}{\partial energy\_prices}
 + PC_{cost} * Margin * \dfrac {\partial X}{\partial energy\_prices}$$

 $$\dfrac {\partial H2_{price}}{\partial energy\_CO2\_emission}= Margin * X * \dfrac {\partial PC_{cost}}{\partial energy\_CO2\_emission}
 + 0$$

$$\dfrac {\partial H2_{price}}{\partial all\_stream\_demand\_ratio}= PC_{cost} * Margin * \dfrac {\partial X}{\partial all\_stream\_demand\_ratio}$$

$$\dfrac {\partial H2_{price}}{\partial resources\_price}= PC_{cost} * Margin * \dfrac {\partial X}{\partial resources\_price}$$

### X computation:

$$X = \dfrac {H2\_revenue}{H2\_revenue
+  A
}$$

with:

if  Carbon\_prod < Carbon\_demand :

$$A = Carbon\_sold\_revenue$$

if  Carbon\_prod > Carbon\_demand :

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Carbon\_storage = Carbon\_prod - Carbon\_demand


$${\footnotesize A = [\dfrac {Carbon\_prod* Carbon\_mol * CO2\_credit}{CO2\_mol}]+ [Carbon\_demand * (Carbon\_price
    - \dfrac {Carbon\_mol * CO2\_credit}{CO2\_mol})]}$$



### energy_prices gradient computation:

$$\dfrac {\partial X}{\partial energy\_prices} =
\dfrac {
    \dfrac {\partial H2\_price}{\partial energy\_prices} * H2\_prod *
    A
}{[H2\_revenue
	+ A ]^2
}
$$

with:

if  Carbon\_prod < Carbon\_demand :

$$A = Carbon\_sold\_revenue$$

if  Carbon\_prod > Carbon\_demand :

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Carbon\_storage = Carbon\_prod - Carbon\_demand

$${\footnotesize A = [\dfrac {Carbon\_prod* Carbon\_mol * CO2\_credit}{CO2\_mol}]+ [Carbon\_demand * (Carbon\_price
    - \dfrac {Carbon\_mol * CO2\_credit}{CO2\_mol})]}$$
\


### invest gradient computation:

$$\dfrac {\partial X}{\partial invest} =
\dfrac {
    [ \dfrac {\partial H2\_prod}{\partial invest} * H2\_price * A ]
    -
    [\dfrac {\partial Carbon\_prod} {\partial invest} * B *
    H2\_revenue]
}{[H2\_revenue
    + A]^2}
$$

with:

if  Carbon\_prod < Carbon\_demand :

$$A = Carbon\_sold\_revenue$$

$$B = Carbon\_price$$

if  Carbon\_prod > Carbon\_demand :

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Carbon\_storage = Carbon\_prod - Carbon\_demand

$${\footnotesize A = [\dfrac {Carbon\_prod* Carbon\_mol * CO2\_credit}{CO2\_mol}]+ [Carbon\_demand * (Carbon\_price
    - \dfrac {Carbon\_mol * CO2\_credit}{CO2\_mol})]}$$

$$B = \dfrac {Carbon\_mol * CO2\_credit}{CO2\_mol}$$
\



### all stream demand ratio computation:

$${\footnotesize\dfrac {\partial X}{\partial all\_stream\_demand\_ratio} =
\dfrac {
    [ \dfrac {\partial H2\_prod}{\partial all\_stream\_demand\_ratio} * H2\_price * A ]
    -
    [\dfrac {\partial Carbon\_prod} {\partial all\_stream\_demand\_ratio} * B *
    H2\_revenue]
}{[H2\_revenue
    + A]^2}}
$$

with:

if  Carbon\_prod < Carbon\_demand :

$$A = Carbon\_sold\_revenue$$

$$B = Carbon\_price$$

if  Carbon\_prod > Carbon\_demand :

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Carbon\_storage = Carbon\_prod - Carbon\_demand

$${\footnotesize A = [\dfrac {Carbon\_prod* Carbon\_mol * CO2\_credit}{CO2\_mol}]+ [Carbon\_demand * (Carbon\_price
    - \dfrac {Carbon\_mol * CO2\_credit}{CO2\_mol})]}$$

$$B = \dfrac {Carbon\_mol * CO2\_credit}{CO2\_mol}$$


### resources price computation:

$${\footnotesize\dfrac {\partial X}{\partial resources\_price} =
\dfrac {
    -
    [\dfrac {\partial Carbon\_price} {\partial resources\_price} * B *
    H2\_revenue]
}{[H2\_revenue
    + A]^2}}
$$

with:

if  Carbon\_prod < Carbon\_demand :

$$A = Carbon\_sold\_revenue$$

$$B = Carbon\_sold\_revenue$$

if  Carbon\_prod > Carbon\_demand :

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Carbon\_storage = Carbon\_prod - Carbon\_demand

$${\footnotesize A = [\dfrac {Carbon\_prod* Carbon\_mol * CO2\_credit}{CO2\_mol}]+ [Carbon\_demand * (Carbon\_price
    - \dfrac {Carbon\_mol * CO2\_credit}{CO2\_mol})]}$$

$$B = Carbon\_demand$$


## Gradient computation - More details


$$H2_{price}= PC_{cost} * Margin * X$$

### Gradients to compute:

 $$\dfrac {\partial H2_{price}}{\partial invest}= Margin * X * \dfrac {\partial PC_{cost}}{\partial invest}+ PC_{cost} * Margin * \dfrac {\partial X}{\partial invest}$$

$$\dfrac {\partial H2_{price}}{\partial energy\_prices}= Margin * X * \dfrac {\partial PC_{cost}}{\partial energy\_prices}+  PC_{cost} * Margin * \dfrac {\partial X}{\partial energy\_prices}$$

$$\dfrac {\partial H2_{price}}{\partial energy\_CO2\_emission}= Margin * X * \dfrac {\partial PC_{cost}}{\partial energy\_CO2\_emission}+ 0$$

### X computation:

$$X = \dfrac {H2\_revenue}{SUM\_revenues}$$

$$= \dfrac {H2\_revenue}{H2\_revenue+ Carbon\_sold\_revenue+Carbon\_storage\_revenue}$$

if  Carbon\_prod - Carbon\_demand < 0:

$$X = \dfrac {H2\_revenue}{H2\_revenue+ Carbon\_sold\_revenue+ 0}$$

$$= \dfrac {H2\_prod * H2\_price}{[H2\_prod * H2\_price ]+ [Carbon\_prod * Carbon\_price]}$$

if  Carbon\_prod > Carbon\_demand :

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Carbon\_storage = Carbon\_prod - Carbon\_demand

$${\scriptsize X = \dfrac {H2\_prod * H2\_price}{[H2\_prod * H2\_price ]+[Carbon\_demand * Carbon\_price]+ [\dfrac {(Carbon\_prod -Carbon\_demand)* Carbon\_mol * CO2\_credit}{CO2\_mol}]}}$$

$${\scriptsize = \dfrac {H2\_prod * H2\_price}{[H2\_prod * H2\_price ] 	+  [\dfrac {Carbon\_prod* Carbon\_mol * CO2\_credit}{CO2\_mol}]+ [Carbon\_demand * (Carbon\_price- \dfrac {Carbon\_mol * CO2\_credit}{CO2\_mol})]}}$$


$$= \dfrac {H2\_revenue}{H2\_revenue +  A}$$



### Gradient computation:

if  Carbon\_prod < Carbon\_demand :

$$X = \dfrac {H2\_prod * H2\_price}{[H2\_prod * H2\_price ]+ [Carbon\_prod * Carbon\_price]}$$

#### energy_prices:

$$\dfrac {\partial X}{\partial energy\_prices} =\dfrac {[ \dfrac {\partial H2\_price}{\partial energy\_prices} * H2\_prod * [H2\_prod * H2\_price+ Carbon\_prod * Carbon\_price]}{[H2\_prod * H2\_price+ Carbon\_prod * Carbon\_price]^2}$$

$$\dfrac { -[    \dfrac {\partial H2\_price} {\partial energy\_prices} * H2\_prod *    (H2\_prod * H2\_price)]}{[H2\_prod * H2\_price+ Carbon\_prod * Carbon\_price]^2}$$

$$= \dfrac {\dfrac {\partial H2\_price}{\partial energy\_prices} * H2\_prod * Carbon\_prod * Carbon\_price]}{[H2\_prod * H2\_price+ Carbon\_prod * Carbon\_price]^2}$$


$$= \dfrac {\dfrac {\partial H2\_price}{\partial energy\_prices} * H2\_prod * Carbon\_sold\_revenue]}{[H2\_revenue+ Carbon\_sold\_revenue]^2}$$


#### invest:
$$\dfrac {\partial X}{\partial invest} =\dfrac {[ \dfrac {\partial H2\_prod}{\partial invest} * H2\_price * [H2\_prod * H2\_price+ Carbon\_prod * Carbon\_price]]}{[H2\_prod * H2\_price+ Carbon\_prod * Carbon\_price]^2}$$

$$\dfrac { -[    \dfrac {\partial H2\_prod} {\partial invest} * H2\_price    +    \dfrac {\partial Carbon\_prod} {\partial invest} *    Carbon\_price] *(H2\_prod * H2\_price)}{[H2\_prod * H2\_price+ Carbon\_prod * Carbon\_price]^2}$$


$$=\dfrac {[ \dfrac {\partial H2\_prod}{\partial invest} * H2\_price * ( Carbon\_prod * Carbon\_price) ]}{[H2\_prod * H2\_price+ Carbon\_prod * Carbon\_price]^2}$$

$$\dfrac {-[\dfrac {\partial Carbon\_prod} {\partial invest} *  Carbon\_price *(H2\_prod * H2\_price)]}{[H2\_prod * H2\_price+ Carbon\_prod * Carbon\_price]^2}$$


$$=\dfrac {[ \dfrac {\partial H2\_prod}{\partial invest} * H2\_price * Carbon\_sold\_revenue ]-[\dfrac {\partial Carbon\_prod} {\partial invest} * Carbon\_price *H2\_revenue]}{[H2\_revenue+ Carbon\_sold\_revenue]^2}$$





if  Carbon\_prod > Carbon\_demand :

$${\scriptsize X = \dfrac {H2\_prod * H2\_price}{[H2\_prod * H2\_price ]    +  [\dfrac {Carbon\_prod* Carbon\_mol * CO2\_credit}{CO2\_mol}]+ [Carbon\_demand * (Carbon\_price- \dfrac {Carbon\_mol * CO2\_credit}{CO2\_mol})]} }$$

$$= \dfrac {H2\_prod * H2\_price}{H2\_revenue + A}$$

with:

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Carbon\_storage = Carbon\_prod - Carbon\_demand

$${\small A = [\dfrac {Carbon\_prod* Carbon\_mol * CO2\_credit}{CO2\_mol}]+ [Carbon\_demand * (Carbon\_price- \dfrac {Carbon\_mol * CO2\_credit}{CO2\_mol})]}$$

$${ = [\dfrac {Carbon\_prod* Carbon\_mol * CO2\_credit}{CO2\_mol}]+ [Carbon\_demand * (Carbon\_price- \dfrac {Carbon\_mol * CO2\_credit}{CO2\_mol})]}$$


#### energy_prices:

$$\dfrac {\partial X}{\partial energy\_prices} =\dfrac {\dfrac {\partial H2\_price}{\partial energy\_prices} * H2\_prod *A}{[H2\_revenue	+ A ]^2}$$





#### invest:

$$\dfrac {\partial X}{\partial invest} =\dfrac {[ \dfrac {\partial H2\_prod}{\partial invest} * H2\_price * [H2\_revenue + A]}{[H2\_revenue	+ A ]^2}$$

$$\dfrac { -[    \dfrac {\partial H2\_prod} {\partial invest} * H2\_price    +    \dfrac {\partial Carbon\_prod} {\partial invest} *    \dfrac {Carbon\_mol * CO2\_credit}{CO2\_mol}] *H2\_revenue}{[H2\_revenue	+ A ]^2}$$

$$=\dfrac {[ \dfrac {\partial H2\_prod}{\partial invest} * H2\_price * A ]    -  [  \dfrac {\partial Carbon\_prod} {\partial invest} *    \dfrac {Carbon\_mol * CO2\_credit}{CO2\_mol} * H2\_revenue]}{[H2\_revenue	+ A ]^2}$$

with:

$${\small A = [\dfrac {Carbon\_prod* Carbon\_mol * CO2\_credit}{CO2\_mol}]+ [Carbon\_demand * (Carbon\_price- \dfrac {Carbon\_mol * CO2\_credit}{CO2\_mol})]}$$
