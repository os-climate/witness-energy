# Coal Extraction

**Definition:**

Coal extraction is the process to extract coal from natural ressources. After this extraction, coal can be used in different way.
The main process to extract coal is mining. As every industrial process, coal mining has energy demand and wastes, which lead to the cost of the coal. Moreover, as coal is a fossil ressource, the amount is limited.

No any heat production in coal extraction process.

**Price:**

To compute the cost of coal extraction, a certain amount of datas is needed.
Concerning the mining itself, the document [^1] gives informations about lifetime, production rate, Capex and Opex for 20 coal mines in Australia. From these data the following average are assumed :
Lifetime : 35 years, Capex : 0.00081 USD/kWh, Opex : 0.2*Capex
The exchange rate between AU.D and US.D is assumed as follow : 1AU.D = 0.77 US.D
Additional datas can be found in [^3].

![](mines_data.PNG) 



**World production:**

Lignite, sub and other bituminous coal are used for electricity generation. China is the most important producer for coal with around 50% of the world production. Summed up, the world production in 2019 is 43752 Twh. [^2]

![](coal_production_by_country.PNG) (credit OurWorldinData [^2])

**Green House Gases impact:**

According to [^5], the full combustion of 1 short ton of coal emits 2.86 short tons of CO2.

The emission of methane is a big issue for coal extraction mines. A lot of methane gas is immersed in coal seams and is leaking into the atmosphere via mineshafts the whole time the coal is mined. But that is not all. Methane leaks for decades into the atmosphere after mining from abandoned mines. Consequently, the global methane emissions from coal mining could continue groing even with declining coal production. [^4]

The Model for Calculating Coal Mine Methane (MC2M) developed by [^4] and used by IPCC models computed the annual CH4 emissions from coal mines with the equation : 

$$CH4\_emissions (m^3) = coal\_production (t) *gas\_content(mine\_depth,coal\_type)*ef\_coefficient$$ 

with $ef\_coefficient$ the emission factor coefficient equals to 1.7 in [^4] ans 1.6 in the Global Coal Mine Tracker [^6] and gas\_content(mine\_depth,coal\_type) the equivalent of CH4 emissions per ton of coal mined in $m^3/t$ :

$$ gas\_content(mine\_depth,coal\_type) = \frac{VL_{coal} depth}{PL_{coal}+depth}$$

with $VL_{coal}$ and $PL_{coal}$ the Langmuir volume and pressure of the coal type (different for anthracite or subbituminous).

![](Gas_content_by_coal.jpg) (credit GEM wiki [^7])

The model is simplified to only take account two types of mining depth : surface and underground mining. Underground mining accounts for around 60% of coal production worldwide [^8] and gas contents for underground mining is around $11.5m^3/t$ and surface mining around $2.25m^3/t$. [^9]

Finally, an additional CH4 emissions of $15 Mt$ is added to take into account all abandoned mines in the world (not varying along the years for now).[^4]

In 2020, the MC2M model estimates that around 70 Mt of CH4 emissions are coming from coal mines which is around twice the 39 Mt estimated by the IEA, and higher than the 52.3 Mt of the Global Energy Monitor (GEM) [^6].


**References**
[^1]:https://www.researchgate.net/publication/43527638_Estimating_average_total_cost_of_open_pit_coal_mines_in_Australia
[^2]: Coal Production, Our World in Data, https://ourworldindata.org/grapher/coal-production-by-country
[^3]: Pandey, B., Gautam, M. and Agrawal, M., 2018. Greenhouse gas emissions from coal mining activities and their possible mitigation strategies. In Environmental carbon footprints (pp. 259-294). Butterworth-Heinemann.
[^4]: Kholod, N., Evans, M., Pilcher, R.C., Roshchanka, V., Ruiz, F., Cote, M. and Collings, R., 2020. Global methane emissions from coal mining to continue growing even with declining coal production. Journal of cleaner production, 256, p.120489.
[^5]:https://www.eia.gov/coal/production/quarterly/co2_article/co2.html#:~:text=For%20example%2C%20coal%20with%20a,million%20Btu%20when%20completely%20burned.&text=Complete%20combustion%20of%201%20short,short%20tons)%20of%20carbon%20dioxide.
[^6]: https://globalenergymonitor.org/projects/global-coal-mine-tracker
[^7]:https://gem.wiki/File:Gas_content_by_coal_rank_and_mining_depth.jpg
[^8]: Wikipedia page : https://en.wikipedia.org/wiki/Coal_mining
[^9]: https://globalenergymonitor.org/wp-content/uploads/2021/03/Coal-Mine-Methane-On-the-Brink.pdf
