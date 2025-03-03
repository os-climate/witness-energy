
## Agricultural lands

Agricultural lands are divided in 2 type of fields that are mixed in this model.
Crops for cereal, vegetables or other production, and grazing lands for switchgrass or other products.

The area available for crops is 1.1Gha and for grazing lands 3.8 Gha for a total around 4.9Gha[^1].

![](total_crop_lands.png)
(source: ourworldindata[^1])

## Agricultural products

**crop residues**

In a field, 50% of the harvest is left, this is what is called crop residues. The field residues are left on the field (to minimize the erosion of soil by wind and water), and the process residues are from the processing of the crops in usable resources (for esample  husks, seeds, bagasse, molasses and roots). 25% of residues can be used as biomass for energy[^2].
The biomass potential from crops residues for energy is high but not yet fully exploited. The residue potential is between 4900Twh (17.8EJ) to 22000Twh(82.3EJ)[^3], but in reality, biomass from agriculture is around 1555Twh(5.6EJ)[^4].

The removed residues from the field must be compensated with fertilizers.

**crops**

As most of the crops are for the food industry (human or animal), some of it is used for the energy sector, it is called energy crop. Only 0.1% of the total biomass production are from energy crops[^5].

The crop production is computed from an average crop yield at 2903kg/ha with 4070kg/ha for 1.1Gha of crop fields[^6] and an average crop yield of 2565.68kg/ha for 3.8Gha of grazing lands.
The total yield (crop + 25% residue) is:
$$Y = 2903kg/ha * 1.25 = 3628.75kg/ha$$

The crop energy production computed corresponds in a mix of crops and residue available for energy. The crop production dedicated to industry (food or other) has been removed.

## Model inputs and outputs

This model has specific inputs:

 - **CO2_from_production**: Represent the CO2 emitted while the biomass dry production. CO2 is absorbed by the plants in order to be zero emissions in the end. Emissions from tractors are taken into account in the raw to net energy factor,
 - **CO2_from_production_unit**: Unit of the CO2_from_production value. In kgCO2/kgBiomassDry by default,
 - **Capex_init**: CAPEX of crop exploitation. See details on costs,
 - **Opex_percentage**: OPEX of crop exploitation. See details on costs,
 - **lifetime**: lifetime of an agriculture activities, initilized to 50 years,
 - **residue_density_percentage**: percentage of residue, at 0.25 by default,
 - **density_per_ha**: density of crop product by hectare, at 3628.75 kg/ha by default,
 - **density_per_ha_unit**:unit of the density of crop, at kg/ha by default,
 - **crop_percentage_for_energy**: crop percentage for energy, at 0.001 by default
 - **residue_percentage_for_energy**: residue percentage for energy, at 0.1 by default
 - **crop_residue_price_percent_dif**: ratio between the average price of residue price (23$/t) on average crop price (60$/t), 38% by default.
 - **Land_surface_from_food_df**: surface of agricultural activities needed to feed the population.

This model has in outputs:

 - **CO2 Emissions**: CO2 emissions from crop production and residues for energy sector
 - **Required land surface**: Surface of crop energy
 - **Technology production**: crop production for energy sector with residues for energy sector
 - **Technology prices**: detailed of prices
 - **Detailed mix prices**: detailed average price of crop and residues

## Details

**production**

initial production: production of energy crop in 2020.

initial_production=4.9 Gha of agricultural lands * density_per_ha * 3.36 kWh/kg calorific value * crop_percentage_for_energy

The model computes the crop energy production and then add the residue production part for energy from the surface for food.

$$Residue\_production\_for\_energy=total\_production * residue\_density\_percentage +  \\ residue\_energy\_production\_from\_food$$

$$Crop\_production\_for\_energy=crop\_density\_percentage*total\_production$$

Then :

$$total\_production\_for\_energy=Residue\_production\_for\_energy+Crop\_production\_for\_energy$$

**Land use**

The computed land-use amount of hectares is the agricultural area for energy crops (only the crop part) with the following computation:

$$NumberOfHa=\frac{CropProductionForEnergy}{density\_per\_ha*calorific\_value}$$

With:
- CropProductionForEnergy, the production of crop and residue for energy sector computed by this model

**Costs**

For CAPEX computation:
 - crop production: 237.95 €/ha (717$/acre)[^7]

For OPEX computation:
  - crop harvest and processing: 87.74 €/ha (264.4$/acre)[^7]
  - residue harvest (22$/t) + fertilizing (23$/t): 37.54 €/ha[^8]

The computed price is the mixed price of crop and residue. Details in the composition of prices of crop and residue is shown in the graphics named "Detailed Price of energy crop technology over the years". Prices are computed with the input parameter crop_residue_price_percent_dif.

## Other Data

Information regarding the age distribution of agricultural lands comes from Our World In Data[^1]. An average lifetime of forest has been taken at 50 years (corresponding to the average lifetime of an agricultural activity).

[^1]: OurWorldInData, land use over the long term, https://ourworldindata.org/land-use#agricultural-land-use-over-the-long-run
[^2]: MDPI, Crop Residue Removal: Assessment of Future Bioenergy Generation Potential and Agro-Environmental Limitations Based on a Case Study of Ukraine, https://www.mdpi.com/1996-1073/13/20/5343/pdf
[^3]: World Bioenergy Association, Global Energy Statistics 2019, http://www.worldbioenergy.org/uploads/191129%20WBA%20GBS%202019_HQ.pdf
[^4]:  World Bioenergy Association, Global biomass potential towards 2035, http://www.worldbioenergy.org/uploads/Factsheet_Biomass%20potential.pdf
[^5]: Bioenergy Europe, Biomass for energy: agricultural residues and energy crops, https://bioenergyeurope.org/component/attachments/attachments.html?id=561&task=download
[^6]: The world bank, Cereal yield kg per hectare, https://data.worldbank.org/indicator/AG.YLD.CREL.KG
[^7]: Manitoba, Crops production costs - 2021, gov.mb.ca/agriculture/farm-management/production-economics/pubs/cop-crop-production.pdf
[^8]: United States Department of Agriculture, 2016, Harvesting Crop Residue: What’s it worth?, https://www.nrcs.usda.gov/Internet/FSE_DOCUMENTS/nrcseprd1298023.pdf
