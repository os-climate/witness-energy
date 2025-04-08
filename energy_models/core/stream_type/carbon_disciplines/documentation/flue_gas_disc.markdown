**Definition[^1] :**
Flue gas is the gas exiting to the atmosphere via a flue, which is a pipe or channel for conveying exhaust gases from a fireplace, oven, furnace, boiler or steam generator. Quite often, the flue gas refers to the combustion exhaust gas produced at power plants. Its composition depends on what is being burned, but it will usually consist of mostly nitrogen (typically more than two-thirds) derived from the combustion of air, carbon dioxide (CO2), and water vapor as well as excess oxygen (also derived from the combustion air). It further contains a small percentage of a number of pollutants, such as particulate matter (like soot), carbon monoxide, nitrogen oxides, and sulfur oxides.

Flue gas from London's Bankside Power Station, 1975[^1]
![](flue_gas.PNG)


Flue gas composition[^2]
![](flue_gas_composition.PNG)

In the model, we focus on C02 concentration in the flue gas to calculate costs variation of CAPEX and electricity needs. The table below describes common flue gases from industries and their related concentration of CO2.

CO2 concentration in different flue gases[^3]
![](co2_concentration_flue_gas.PNG)

Once each energy production flue gases specified, the model calculates average CO2 concentration in flue gas stream and applies variations.

The total flue gas production is finally computed and send to the carbon capture model to get the potential fluegas to be captured.

CO2 concentration and evolution of costs related to capture[^4]
![](co2_cost_evolution_by_concentration.PNG)


[^1]: Robin Webster, Bankside power station and St George the Martyr church, licensed under [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0/), https://en.wikipedia.org/wiki/Flue_gas
[^2]: Constituents of flue gas, https://www.sciencedirect.com/topics/earth-and-planetary-sciences/flue-gas
[^3]: Wang, X. and Song, C., 2020. Carbon Capture From Flue Gas and the Atmosphere: A Perspective. Frontiers in Energy Research, 8, p.265. Licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), https://www.frontiersin.org/articles/10.3389/fenrg.2020.560849/full
[^4]: IEM capture cost estimates for representative oil sands flue gas streams according to CO2 concentration, https://www.researchgate.net/figure/IEM-capture-cost-estimates-for-representative-oil-sands-flue-gas-streams-according-to_tbl4_251711920
