
## FORMULA

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

if  Carbon\_prod - Carbon\_demand > 0 : 
    
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Carbon\_storage = Carbon\_prod - Carbon\_demand

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; if  Carbon\_storage < Carbon\_storage\_max :

$$X = \dfrac {H2\_prod * H2\_price}{[H2\_prod * H2\_price ]+[Carbon\_demand * Carbon\_price]+ [\dfrac {(Carbon\_prod -Carbon\_demand)* Carbon\_mol * CO2\_credit}{CO2\_mol}]}$$

$$= \dfrac {H2\_prod * H2\_price}{[H2\_prod * H2\_price ] 	+  [\dfrac {Carbon\_prod* Carbon\_mol * CO2\_credit}{CO2\_mol}]+ [Carbon\_demand * (Carbon\_price- \dfrac {Carbon\_mol * CO2\_credit}{CO2\_mol})]}$$

$$= \dfrac {H2\_revenue}{H2\_revenue +  A}$$


&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; if  Carbon\_storage > Carbon\_storage\_max :

$$X = \dfrac {H2\_prod * H2\_price}{[H2\_prod * H2\_price ]+[Carbon\_demand * Carbon\_price]+ [\dfrac {(Carbon\_storage\_max)* Carbon\_mol * CO2\_credit}{CO2\_mol}]}$$

\
\
### Gradient computation:

if  Carbon\_prod < Carbon\_demand : 

$$X = \dfrac {H2\_prod * H2\_price}{[H2\_prod * H2\_price ]+ [Carbon\_prod * Carbon\_price]}$$

#### energy_prices:

$$\dfrac {\partial X}{\partial energy\_prices} =\dfrac {[ \dfrac {\partial H2\_price}{\partial energy\_prices} * H2\_prod * [H2\_prod * H2\_price+ Carbon\_prod * Carbon\_price] -[    \dfrac {\partial H2\_price} {\partial energy\_prices} * H2\_prod *    (H2\_prod * H2\_price)]}{[H2\_prod * H2\_price+ Carbon\_prod * Carbon\_price]^2}$$

$$= \dfrac {\dfrac {\partial H2\_price}{\partial energy\_prices} * H2\_prod * Carbon\_prod * Carbon\_price]}{[H2\_prod * H2\_price+ Carbon\_prod * Carbon\_price]^2}$$


$$= \dfrac {\dfrac {\partial H2\_price}{\partial energy\_prices} * H2\_prod * Carbon\_sold\_revenue]}{[H2\_revenue+ Carbon\_sold\_revenue]^2}$$


#### invest:
$$\dfrac {\partial X}{\partial invest} =\dfrac {[ \dfrac {\partial H2\_prod}{\partial invest} * H2\_price * [H2\_prod * H2\_price+ Carbon\_prod * Carbon\_price]] -[    \dfrac {\partial H2\_prod} {\partial invest} * H2\_price    +    \dfrac {\partial Carbon\_prod} {\partial invest} *    Carbon\_price] *(H2\_prod * H2\_price)}{[H2\_prod * H2\_price+ Carbon\_prod * Carbon\_price]^2}$$


$$=\dfrac {[ \dfrac {\partial H2\_prod}{\partial invest} * H2\_price * ( Carbon\_prod * Carbon\_price) ]-[\dfrac {\partial Carbon\_prod} {\partial invest} *  Carbon\_price *(H2\_prod * H2\_price)]}{[H2\_prod * H2\_price+ Carbon\_prod * Carbon\_price]^2}$$


$$=\dfrac {[ \dfrac {\partial H2\_prod}{\partial invest} * H2\_price * Carbon\_sold\_revenue ]-[\dfrac {\partial Carbon\_prod} {\partial invest} * Carbon\_price *H2\_revenue]}{[H2\_revenue+ Carbon\_sold\_revenue]^2}$$

\
\
\
\
\

if  Carbon\_prod > Carbon\_demand : 


$$X = \dfrac {H2\_prod * H2\_price}{[H2\_prod * H2\_price ] 	+  [\dfrac {Carbon\_prod* Carbon\_mol * CO2\_credit}{CO2\_mol}]+ [Carbon\_demand * (Carbon\_price- \dfrac {Carbon\_mol * CO2\_credit}{CO2\_mol})]}$$

$$= \dfrac {H2\_prod * H2\_price}{H2\_revenue 	+  A}$$

with:

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Carbon\_storage = Carbon\_prod - Carbon\_demand

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; if  Carbon\_storage < Carbon\_storage\_max :

$$A = [\dfrac {Carbon\_prod* Carbon\_mol * CO2\_credit}{CO2\_mol}]+ [Carbon\_demand * (Carbon\_price- \dfrac {Carbon\_mol * CO2\_credit}{CO2\_mol})]$$

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; if  Carbon\_storage > Carbon\_storage\_max :

$$A = [Carbon\_demand * Carbon\_price]+ [\dfrac {(Carbon\_storage\_max)* Carbon\_mol * CO2\_credit}{CO2\_mol}]$$

#### energy_prices:

$$\dfrac {\partial X}{\partial energy\_prices} =\dfrac {\dfrac {\partial H2\_price}{\partial energy\_prices} * H2\_prod *A}{[H2\_revenue	+ A ]^2}$$





#### invest:
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Carbon\_storage = Carbon\_prod - Carbon\_demand

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; if  Carbon\_storage < Carbon\_storage\_max :
$$\dfrac {\partial X}{\partial invest} =\dfrac {[ \dfrac {\partial H2\_prod}{\partial invest} * H2\_price * [H2\_revenue + A] -[    \dfrac {\partial H2\_prod} {\partial invest} * H2\_price    +    \dfrac {\partial Carbon\_prod} {\partial invest} *    \dfrac {Carbon\_mol * CO2\_credit}{CO2\_mol}] *H2\_revenue}{[H2\_revenue	+ A ]^2}$$

$$=\dfrac {[ \dfrac {\partial H2\_prod}{\partial invest} * H2\_price * A ]    -  [  \dfrac {\partial Carbon\_prod} {\partial invest} *    \dfrac {Carbon\_mol * CO2\_credit}{CO2\_mol} * H2\_revenue]}{[H2\_revenue	+ A ]^2}$$

with:
$$A = [\dfrac {Carbon\_prod* Carbon\_mol * CO2\_credit}{CO2\_mol}]+ [Carbon\_demand * (Carbon\_price- \dfrac {Carbon\_mol * CO2\_credit}{CO2\_mol})]$$

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; if  Carbon\_storage > Carbon\_storage\_max :
$$\dfrac {\partial X}{\partial invest} =\dfrac {[ \dfrac {\partial H2\_prod}{\partial invest} * H2\_price * A ]}{[H2\_revenue	+ A ]^2}$$

with:
$$A = [Carbon\_demand * Carbon\_price]+ [\dfrac {(Carbon\_storage\_max)* Carbon\_mol * CO2\_credit}{CO2\_mol}]$$
\
\
\
### Other gradients already computed:

* $$\dfrac {\partial H2\_prod}{\partial invest} = computed\_value1$$
* $$\dfrac {\partial Carbon\_prod}{\partial invest} = computed\_value2$$

* $$\dfrac {\partial PC_{cost}}{\partial invest} = already\_computed\_value 1$$

* $$\dfrac {\partial PC_{cost}}{\partial energy\_prices} = already\_computed\_value 2$$

* $$\dfrac {\partial PC_{cost}}{\partial energy\_CO2\_emission} = already\_computed\_value 3$$

finally, the only gradient to compute is:

$$\dfrac {\partial H2\_price}{\partial energy\_prices} = (Id_{H2\_column}, Zero_{other\_column})$$