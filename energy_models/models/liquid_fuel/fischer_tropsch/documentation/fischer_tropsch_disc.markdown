# Fischer Tropsch synthesis



## The Fischer Tropsch Reaction
The Fischer-Tropsch process is used to generate high carbon chain up to synthetic fuel and water wi th $n$ the carbon molecular number of the wanted synthetic fuel.

$$(2n + 1) H_2 + n CO --> C_nH_{2n+2} + nH_2O$$(2)

 These reactions occur in the presence of metal catalysts, typically at temperatures of 150–300 °C (302–572 °F) and pressures of one to several tens of atmospheres. The process was first developed by Franz Fischer and Hans Tropsch in 1925.[^1]

For industrial use, the Fischer Tropsch reaction does not guarantee a single fuel as output of the synthesis. The output stream is called syncrude and is a mixture of different synthetic fuel such as kerosene diesel or naphtas. 
For the purpose of the model, we suppose first that the Fischer Tropsch model products only kerosene and we take into account in its cost the hydrocraking process used to extract kerosene from the producted syncrude. 

## Usage for XtL industries

The fischer Tropsch synthesis is the main reaction to produce synthesis fuel from power or any sources of energy. The process of producing synfuels through indirect conversion is often referred to as CtL (Coal-to-Liquids Coal Gasification for syngas production) GtL (Gas-to-Liquids, SMR for syngas production) or PBtL (Power-Biomass-to-Liquids, Biomass gasification for syngas production) depending on the initial feedstock. 

The most known synthesis fuel production is the Power-to_Liquids conversion where syngas is produced through renewable electricity via Electrolysis or Co-electrolysis technologies.

### Difference of fuel synthesis pathways depending on the syngas supply [^2]  
![](Xtl.PNG)
(Image Credit: [^2])


On the Figure above, all concepts are influencing the process of syngas upgrading because of the composition of the syngas after production. More technical details are explained in the section Modifying the syngas ratio for the synthesis below.

### Existing and projected Fischer-Tropsch production

The commercialisation of X-to-liquids processes emerges in some countries. The world's largest scale implementation of Fischer–Tropsch technology is a series of plants operated by Sasol in South Africa with a production of 201000 BPD (Barrel Per Day) based on Coal Gasification [^6] (CtL). China and its large coal production uses also coal gasification for its FT industries and produces around 112000 BPD [^7].  Qatar, is the second largest FT plant in the world based on SMR (Steam Methane Reforming) with a production of 174000 BPD (GtL). Malaysia has also a Fischer Tropsch Plant based on GtL with 12000 BPD of synthetic fuel. In the United States, India, Finland or Russia some states have invested in Fischer–Tropsch plants but not at commercial scale for now. 

The first PtL (Power to Liquid with Electrolysis) demo plant at industrial scale is in construction in Norway [^3], capable of producing 10 million litres of fuel a year before scaling up the facility to commercially produce 100 million litres by 2026. The consortium has four main partners: German PtL technology provider Sunfire, Swiss-based CO2 air capture technology specialist Climeworks, Luxembourg-headquartered international engineering company Paul Worth SMS Group and Valinor, a Norwegian family-owned green investment company.

### Sunfire PtL demonstration plant in Dresden, Germany [^4]

![](Sunfire_PtL_Dresden.jpg) 
(Image Credit: Sunfire, taken from [^4])

## Modifying the syngas ratio for the synthesis
The ratio $\frac{CO}{H_2}$ of the needed syngas (gas composed of carbon monoxyde $CO$ and hydrogen $H_2$) must be equal to : 

$$r_{syngas} = \frac{n}{2n+1}$$

Depending on the syngas production technology, the syngas ratio of $CO$ over $H_2$ can be different. If the ratio of input syngas is lower than $\frac{n}{2n+1}$ we need to enrich the syngas with carbon monoxyde.
If the syngas ratio is higher, some CO in the syngas must be removed.

### The Reverse Water Gas Shift reaction 

The Reverse Water Gas Shift reaction is able to enrich a syngas mixture using carbon dioxyde ($CO_2$) :

$$dCO_2 + e(H_2 +r_1CO)  --> (H_2 +r_2 CO) + cH_20$$

with $r_1<r_2$ the $CO$ over $H_2$ ratio of the input and output syngases respectively : 

$$r_i = \frac{mol CO}{mol H_2}$$

and with $c$,$d$ and $e$ coefficients of the reaction that can be computed with $r_1$ and $r_2$ to satisfy chemical equilibrium : 

$$c = \frac{r2-r1}{1+r1}$$

$$d = r2 - \frac{r1(1+r2)}{1+r1}$$

$$e = \frac{1+r2}{1+r1}$$



### The Water Gas Shift reaction 

The Water Gas Shift reaction is able to remove CO from a syngas mixture using water ($H_2O$) :

$$(H_2 +r_1 CO) + cH_20 --> dCO_2 + e(H_2 +r_2CO)$$

with $r_1>r_2$ syngas ratios before and after the reaction :


and with $c$, $d$ and $e$ coefficients of the reaction that can be computed with $r_1$ and $r_2$ to satisfy chemical equilibrium : 

$$c = \frac{r1-r2}{1+r2}$$

$$d = r1 - \frac{r2(1+r1)}{1+r2}$$

$$e = \frac{1+r1}{1+r2}$$


In our context, we know the value of $r_2= \frac{n}{2n+1}$ with $n=12$ which is a valid assumption for kerosene jet fuel (between 10 and 16 carbon atoms by moles).
Then, we are able to determine first which technology do we need to obtain the correct syngas (WGS or RWGS) and secondly, the amount of $CO_2$ (amount of $H_2O$), the production of $H_2O$ (production of $CO_2$) and the total cost of the WGS conversion reaction (RWGS reaction respectively) which will be added to the cost of the Fischer Tropsch synthesis. Note that due to evolving investments, the syngas ratio in input of the model may be different over the years and the choice of the syngas ratio conversion could change between WGS and RWGS. 


## Data 

All technical and economical datas are extracted from [^5]. The paper details the techno-Economic assessment of a PtL factory using a hybrid PV-Wind power plant to provide electricity and combined to an electrolyser to produce $H_2$ and a CO2 capture plant. The $CO_2-H_2$ stream is injected into a Reverse Water Gas Shift reactor to enrich the syngas in $CO$ (considering the pure $H_2$ stream as a syngas with a zero $CO$ over $H_2$ ratio.). The economic model includes the FT and Hydrocracker part of the Figure below. 

### Ptl flow diagram of Fasihi & al  [^5]

![](fasihi2016.PNG)
(Image Credit: [^5])

## Heat
The Fischer-Tropsch reaction is carried out over supported cobalt-based catalysts at 20–30 bar and at temperatures below 240 °C. The FTS is a highly exothermic reaction due to a standard reaction enthalpy of −165kJ/molCO.[^8]

[^1]: [De Klerk , A. (2013) FischerTropsch Process. Kirk Othmer Encyclopedia of Chemical Technology. Weinheim: Wiley-VCH](https://onlinelibrary.wiley.com/doi/abs/10.1002/0471238961.fiscdekl.a01) 

[^2]: [Albrecht, F. (2017) A standardized methodology for the techno-economic evaluation of alternative fuels A case study, Fuel, vol 194, p511-526](https://www.sciencedirect.com/science/article/pii/S0016236116312248)

[^3]: [Schmidt, P. (2016) Power-to-Liquids Potentials and Perspectives for the Future Supply of Renewable Aviation Fuel, Umweltbundesamt article](https://www.umweltbundesamt.de/en/publikationen/power-to-liquids-potentials-perspectives-for-the)

[^4]: [Neste acquires stake in PtX developer Sunfire, online article](https://www.greenaironline.com/news.php?viewStory=2711)

[^5]: [Fasihi, M., Bogdanov, D. and Breyer, C., 2016. Techno-economic assessment of power-to-liquids (PtL) fuels production and global trading based on hybrid PV-wind power plants. Energy Procedia, 99, pp.243-268.](https://www.sciencedirect.com/science/article/pii/S1876610216310761)

[^6]: https://en.wikipedia.org/wiki/Fischer%E2%80%93Tropsch_process#Commercialization
[^7]: http://www.synfuelschina.com.cn/en/about/
[^8]: https://www.sciencedirect.com/science/article/pii/S1385894718309215
