## Forests

Forests are divided in 2 type of forests.
Managed forests are forests intensively managed for production purposes, but can also be established for protection, conservation or socio-economic purposes. Managed forests are used to capture CO2. Wood biomass from those forests can be considered as carbon neutral (CO2 absorbed when the tree growths = CO2 emitted when it burns).

Unmanaged forests, on the contrary, cannot be considered as carbon neutral.

The area of forest under long-term management plans has increased significantly in the past 30 years to an estimated 2.05 billion hectares (Gha) in 2020, equivalent to 54 percent of the global forest area[^1].
Globally, about 1.15 Gha of forest is managed primarily for the production of wood and non-wood forest products[^1].
In addition, 749 million ha is designated for multiple use, which often includes production[^1].

![](forestry_carbon_cycle.jpg)

(image from Tackle Climate Change - Use Wood[^2])

## Forestry woodFuel

Globally, the area of forest used for production so designated is estimated at 1.15 Gha, which is equivalent to 31 percent of the forest area of reporting countries[^1].
![](forests_for_production.jpg)

A little part of this production is dedicated to the energy sector.

The forest products can be divided in two categories: woodfuel and residues.
![](We_use_the_entire_three.jpg)
(image from SCA[^3])

We can estimate that forests produce 10.08m3/ha of woodfuel and 20.12 m3/ha of residues per year in average[^4].
We also estimate that the part of woodfuel for energy is 3% and residues for energy is 30%.

Wood have an average density of 600 kg/m3.
Wood is chipped and dried (at ambiant air for a certain period of storage) leading in woodchips biomass of 15% of moisture.

The wood production computed corresponds on a mix of wood and residue available for energy. The wood production dedicated to industry has been removed.

## Model inputs and outputs

This model has specific inputs:

 - **CO2_from_production**: Represent the CO2 absorbed while the tree grows. It is determined to lead to zero emissions (CO2_absorbed - CO2 emit when used = 0),
 - **CO2_from_production_unit**: Unit of the CO2_from_production value. In kgCO2/kgBiomassDry by default,
 - **Capex_init**: CAPEX of managed forest exploitation. See details on costs,
 - **Opex_percentage**: OPEX of managed forest exploitation. See details on costs,
 - **lifetime**: lifetime of a forests, initilized to 150 years,
 - **percentage_for_production**: percentage of forests used for production, at 31% by default. It is used to compute land use,
 - **residue_density_percentage**: percentage of residue for one hectare of forest, at 2/3 by default,
 - **wood_density_percentage**: percentage of woodfuel for one hectare of forest, at 1/3 by default,
 - **density_per_ha**: density of wood product by hectare, at 30 m3/ha by default,
 - **density**: wood density, 600 kg/m3 by default,
 - **wood_percentage_for_energy**: wood percentage for energy
 - **residue_percentage_for_energy**: residue percentage for energy
 - **wood_residue_price_percent_dif**: ratio between the average price of residue price (34€) on average wood price (100€), 34% by default.

This model has in outputs:

 - **CO2 Emissions**: CO2 emissions from managedWood production for energy sector
 - **Required land surface**: Surface of managed forest
 - **Technology production**: wood production for energy sector
 - **Technology prices**: detailed of prices
 - **Detailed mix prices**: detailed average price of wood and residues

## Details

**production**

initial production: production of wood from managed forest in 2020.

initial_production=1.66 Gha of unmanaged forests * 31% of forest for production * density_per_ha * density * 3.36 kWh/kg calorific value

To compute the production for the energy sector, the production for industry is assumed to be constant so the production for industry is computed at year start and then removed from the total production each year.

$$Residue\_production\_for\_energy=residue\_density\_percentage*\\(total\_production - total\_production[0]*(1-residue\_percentage\_for\_energy))$$

$$Wood\_production\_for\_energy=wood\_density\_percentage*\\(total\_production - total\_production[0]*(1-wood\_percentage\_for\_energy))$$

Then :

$$total\_production\_for\_energy=Residue\_production\_for\_energy+Wood\_production\_for\_energy$$

**Land use**

The computed land-use amount of hectares is the global amount of managed forest with the following computation:

$$NumberOfHa=\frac{WoodProductionForEnergy+WoodProductionForNonEnergy}{forest\_percentage\_for\_production*density\_per\_ha*calorific\_value}$$

With: 
- WoodProductionForEnergy, the production of Managed wood and residue computed by this model
- WoodProductionForNonEnergy, the computed amount of Managed Wood used for production using the inputs data wood_percentage_for_non_energy and wood_percentage_for_non_energy.
- forest_percentage_for_production, the percentage of forest use for production (0.31 here)

**Costs**

For CAPEX computation:
 - Land purchase: 12000 $/ha

For OPEX computation:
  - cutting, chipping, off_road transportation : 8 $/Mwh[^5]
  
The computed price is the mixed price of wood and residue. Details in the composition of prices of wood and residue is shown in the graphics named "Detailed Price of Unmanaged wood technology over the years". Prices are computed with the input parameter wood_residue_price_percent_dif.

## Other Data

Information regarding the age distribution of planted forests comes from Our World In Data[^6]. An average lifetime of forest has been taken at 150 years (corresponding to the age of a tree).

[^1]: Food and Agriculture Organization of the United Nations, The state of the worl's forests, 2020, http://www.fao.org/3/ca8642en/CA8642EN.pdf
[^2]: Tackle Climate Change Use Wood, http://www.softwoodlumber.org/pdfs/Book_Tackle_Climate_Change_Use_Wood_eVersion.pdf
[^3]: SCA, We use the entire tree, https://www.sca.com/en/about-us/sustainability/sustainable-development/Efficient-use-of-resources/we-use-the-entire-tree/
[^4]: teagasc, Agriculture and food development authority, https://www.teagasc.ie/crops/forestry/advice/timber-harvesting/number-of-trees-removed-during-thinning/
[^5]: Eubia, Recovery of forests residues, https://www.eubia.org/cms/wiki-biomass/biomass-resources/challenges-related-to-biomass/recovery-of-forest-residues/
[^6]: OurworldInData, Primary vs. planted forest, https://ourworldindata.org/forest-area#primary-vs-planted-forest