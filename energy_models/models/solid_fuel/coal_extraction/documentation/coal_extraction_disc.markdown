# Coal Extraction

**Definition:**

Coal extraction is the process to extract coal from natural ressources. After this extraction, coal can be used in different way.
The main process to extract coal is mining. As every industrial process, coal mining has energy demand and wastes, which lead to the cost of the coal. Moreover, as coal is a fossil ressource, the amount is limited.


**Price:**

To compute the cost of coal extraction, a certain amount of datas is needed.
Concerning the mining itself, the document [^1] gives informations about lifetime, production rate, Capex and Opex for 20 coal mines in Australia. From these data the following average are assumed :
Lifetime : 35 years, Capex : 0.00081 USD/kWh, Opex : 0.2*Capex
The exchange rate between AU.D and US.D is assumed as follow : 1AU.D = 0.77 US.D
![](mines_data.PNG) 

Moreover, extracting coal needs motored engines, and theses engine need fuel.
the chart below [^2] gives the average cost of fuel for 1 short ton of coal extracted
![](Fuel_for_coal.PNG) 

**Coal properties:**

Concerning coal itself, calorific value need to be determine. Depending on their quality, coal is referenced by different name, such as coking coal, bituminous coal or lignite. As these coal are different, their use are also different. According to the picture below, extracted from [^3], it is assumed that the coal use for electricity production is a 17.435MJ/kg coal. This lead to 4.86kWh/kg for the calorific value.
![](coal_qualities.PNG) 

**World production:**

Lignite, sub and other bituminous coal are used for electricity generation. Summed up, the world production in 2019 is 3.25 million ktoe [^4] (petrol equivalent ton), according to IEA, 1 toe corresponding to 11630 kWh, so the global production for 2019 is 37800 Twh.
![](Coal_prod.PNG)

**CO2 impact:**

According to [^5], the full combustion of 1 short ton of coal emits 2.86 short tons of CO2.


[^1]:https://www.researchgate.net/publication/43527638_Estimating_average_total_cost_of_open_pit_coal_mines_in_Australia
[^2]:https://www.iea.org/data-and-statistics/charts/average-fuel-costs-and-share-in-total-coal-mining-costs-in-selected-countries-2018-2020
[^3]:https://iea.blob.core.windows.net/assets/imports/events/243/09_IEA_Energy_R.Quadrelli.pdf
[^4]:Coal - Fuels & Technologies, IEA, https://www.iea.org/fuels-and-technologies/coal
[^5]:https://www.eia.gov/coal/production/quarterly/co2_article/co2.html#:~:text=For%20example%2C%20coal%20with%20a,million%20Btu%20when%20completely%20burned.&text=Complete%20combustion%20of%201%20short,short%20tons)%20of%20carbon%20dioxide.