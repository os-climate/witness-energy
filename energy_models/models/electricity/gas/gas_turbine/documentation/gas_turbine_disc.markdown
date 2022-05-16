# Gas Electricity


**Definition:**
Gas power plants generate electricity by burning gas. There exists different types of gas power plant to generate electricity. All of them use a gas turbine: "natural gas is added, along with a stream of air, which combusts and expands through this turbine causing a generator to spin a magnet, making electricity."[^1]. Within this process, waste heat is generated. Some types of plant use this waste heat (see below).  
Natural gas power plants are cheap and quick to build. They also have very high thermodynamic efficiencies compared to other power plants.    
There are two types of natural gas power plants: **Simple cycle gas plants** and **combined cycle gas plants**. The former consists of a gas turbine connected to a generator and the latter consists of a simple cycle plant, combined with another external combustion engine.

## Simple Cycle 
"The simple cycle is simpler but less efficient than the combined cycle. However, simple cycle plants are able to dispatch faster than coal-fired power plants or nuclear plants. This means they can be turned on or off faster in order to meet societies electricity needs. Often needed on the grid with wind power and solar power, its purpose is to meet the fluctuating electricity needs of society, known as peaking power."[^1]

## Combined Cycle Gas Plant
"Combined cycle plants are more efficient because it makes use of the hot exhaust gases that would otherwise be dispelled from the system. These exhaust gases are used to boil water into steam which can then spin another turbine and generate more electricity. The thermal efficiency of the combined cycle can get up to 60%. Moreover, these plants produce one third of the waste heat of a plant with a 33% efficiency (like a typical nuclear power plant or an older coal power plant). The cost of a combined cycle plants is generally higher since they cost more to build and run."[^1]



## Data     
The data used for this model is extracted from World Bank[^2], the International Energy Agency[^3], the Energy Information Administration[^4], Lazard[^5] and Fraunhofer[^6].  
In its document[^2], the World Bank gather data from several sources to compute the Levelized Cost of Energy and compare the different results. 

### GHG emissions 

The GAINS model predicts methane fugitive emissions from gas energy. Emission factors from gas production are adapted from IPCC guidelines and a mean value has been taken for the leakage at industrial and power plants of 0.1025 kt/PJ [^8].

The GAINS model also predicts N2O fugitive emissions from gas energy. The emission factor is equal to 0.0001 kt/PJ. [^7]

### Hypotheses
For global investment and production we only have data for gas electricity without the detail for each technology. For the production, the Energy Information Agency[^3] explains that in 2017, 53% of the gas electricity was produced by Combined Cycle Gas Plant and the left 47% by gas turbine. This information was used for our assumption that 55% of global production comes from CCGT and 45% from GT.  
Regarding investment, the only information we found is also from the Energy Information Agency[^3]. It states that the majority of the investment goes into CCGT plant. Our hypothesis is that 75% of investment of the 2 past years in gas plant was for CCGT plant and 25% for GT plant. 

## Some insight on gas Electricity evolution


Global electricity generation by source and scenario (TWh)[^3]

![Global electricity generation by source and scenario (TWh)[^3]](electricitybysourceIEA.PNG)  
Global power generation capacity by source and scenario[^3]
![](byscenarioprodelecIEA.PNG)  

Global annual average power sector investment, historical and
by scenario, 2019-2040[^3]

![](investIEA.PNG)

[^1]: [Energy Education. Natural gas power plant.](https://energyeducation.ca/encyclopedia/Natural_gas_power_plant)

[^2]: [Timilsina, G.R., 2020. Demystifying the Costs of Electricity Generation Technologies.](https://openknowledge.worldbank.org/handle/10986/34018)

[^3]: IEA 2022, [International Energy Agency. (2019). World Energy Outlook 2019, IEA, Paris.](https://www.iea.org/reports/world-energy-outlook-2019), License: CC BY 4.0.

[^4]: [Energy Information Agency. (2017).](Natural gas generators make up the largest share of overall U.S. generation capacity.](https://www.eia.gov/todayinenergy/detail.php?id=30872)

[^5]: [Lazard. (2020). Levelized cost of energy analysis.](https://www.lazard.com/media/451419/lazards-levelized-cost-of-energy-version-140.pdf)

[^6]: [Kost, C., Mayer, J.N., Thomsen, J., Hartmann, N., Senkpiel, C., Philipps, S., Nold, S., Lude, S., Saad, N. and Schlegl, T. (2013). Levelized cost of electricity renewable energy technologies. Fraunhofer Institute for Solar Energy Systems ISE, 144.](https://www.ise.fraunhofer.de/content/dam/ise/en/documents/publications/studies/EN2018_Fraunhofer-ISE_LCOE_Renewable_Energy_Technologies.pdf)

[^7]: Winiwarter, W., 2005. The GAINS model for greenhouse gases-version 1.0: nitrous oxide (N2O).https://previous.iiasa.ac.at/web/home/research/researchPrograms/air/IR55-GAINS-N2O.pdf
[^8]: Höglund-Isaksson, L. and Mechler, R., 2005. The GAINS Model for Greenhouse gases–Version 1.0: Methane (CH4), IIASA Interim Report IR-05-054. International Institute for Applied Systems Analysis, Laxenburg. https://previous.iiasa.ac.at/web/home/research/researchPrograms/air/IR54-GAINS-CH4.pdf
