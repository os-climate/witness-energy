# Solar Thermal

**Definition:[^1]**

Solar thermal electric plants generate electricity by converting concentrated solar energy to heat, which is in turn converted to electricity in a thermal power block. Combined with a thermal energy storage system it provides dispatchable renewable electricity.


The two major designs used today are parabolic trough power plants and central receiver or power tower systems. Both can include a heat storage system, which allows electricity generation in the evening and night. Systems with linear Fresnel receivers (essentially a variation on the power trough concept, but using flat mirror elements to concentrate the light) are also in commercial operation. The parabolic dish with a Stirling engine receiver is researched as well, but there are no plants in commercial operation.
STE systems comprise the following main elements:
- solar field
- receiver and heat transfer system
- thermal storage system
- power conversion unit (heat to electricity) and balance of plant.


 ![](solar_thermal_type.png)
 (Image Credit: IEA [^1b])

## Data     
Most of the data used for this model is extracted from Greenpeace International, SolarPACES and ESTELA report[^2], National Renewable Energy Laboratory (NREL) [^3], Joint Research Center [^1] and International Renewable Energy Agency (IRENA)[^4].

## Some insight on SolarThermal evolution
IEA solar thermal power generation in the Sustainable Development Scenario, 2000-2030
![](concentrating-solar-power-generation-in-the-sustainable-development-scenario-2000-2030.png)  

 Global weighted average total installed costs, capacity factors and LCOE for CSP, 2010-2019
 ![](irena_csp.png)
 
## Land use
Solar thermal are disposed in lands and most of it on crops category of lands.[^5] 
Because in developed countries, where solar thermal are the most deployed, barren lands and desert are scarce (around 10% of the global barren lands surface), it will not be considered in this model.
Moreover, only 3% of the urban surface can be used for solar thermal, very few rooftops are eligible to solar panels. So for this first version of land use model it will not be considered either. 

The power by hectare value has been computed on the base of 357 MWh/acre[^6] for photovoltaic panels, and solar thermal uses 10% less space than Solar photovoltaic, giving 346564,9 kWh/ha.


[^2]: Greenpeace International, SolarPACES and ESTELA (European Solar Thermal Electricity Association) (2016), Solar Thermal Electricity Global Outlook 2016 – Full Report, http://www.solarpaces.org/new-web-nasertic/images/pdfs/GP-ESTELA-SolarPACES_Solar-Thermal-Electricity-Global-Outlook-2016_Executive-Summary.pdf
[^3]: NREL (National Renewable Energy Laboratory), Concentrating Solar Power Projects, https://solarpaces.nrel.gov/
[^1]: JRC (Joint Research Center) (2019), Solar Thermal Electricity: Technology development report https://publications.jrc.ec.europa.eu/repository/bitstream/JRC118040/jrc118040_1.pdf
[^1b]: [IEA (2014), Technology Roadmap - Solar Thermal Electricity 2014, IEA, Paris](https://www.iea.org/reports/technology-roadmap-solar-thermal-electricity-2014)
[^4]: IRENA (2020), Renewable Power Generation Costs in 2019,
International Renewable Energy Agency, Abu Dhabi. https://www.irena.org/publications/2020/Jun/Renewable-Power-Costs-in-2019
[^5]: Scientific report (2021), https://www.nature.com/articles/s41598-021-82042-5
[^6]: greenCoast, 2019, Solar Farm Land Requirements: How Much Land Do You Need?, https://greencoast.org/solar-farm-land-requirements/