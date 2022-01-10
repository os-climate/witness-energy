# Documentation 

the energy mix discipline acts at the top of energies, the goal is to aggregate the information arriving from each energy, calculate the net production and the CO2 emissions, refer to the l0 test (l0_test_compute__energy_mix.py) for more details on the inputs and outputs of the discipline. The net productions can be negative, an alert is launched in the code to warn the user, 


## CO2 emissions model 

The CO2 emissions model in the energy mix model computed the total of carbon emissions f the entire energy mix. 

Four main sources are taken into account : 
- The CO2 in the flue gas expelled from plants (like coal generation plants)
- The CO2 emitted by the use of each net energy production (energy burned)
- The CO2 emitted by technos that cannot be stored, from machinery which uses fuels (tractors for biomass, coal extractors ...)
- The CO2 which is captured by technologies as Upgrading biogas for example
  
Other technologies acts in the favor of the removal of carbon emissions and CO2 fluxes are divided in three categories : 
- The CO2 fluxes stored by carbon storage technologies (i.e. injected in oceans)
- The CO2 removed by technologies (i.e. managed wood technology removes CO2 thanks to tree carbon cycle)
- The CO2 needed by the chemcial reaction of a technology (i.e. Fischer Tropsch plants may needs CO2 to enrich syngas in CO for Fischer Tropsch synthesis)
  
![](co2_emissions_model.PNG)

Carbon emissions stored by carbon storage technologies are limited by the amount of CO2 captured. Gaseous CO2 storage and solid carbon storage are separated and they are both limited each by the amount of CO2 and solid carbon ready to store. 

![](carbon_stored.PNG)

The Solid carbon ready to store is for now the one created by plasma cracking technology. However the computation of gaseous CO2 ready to store is more complex. The CO2 captured to be stored is the difference between the gaseous CO2 capture provided by the energy mix and the needed one. The CO2 capture provided is the sum of the CO2 really captured by carbon capture technologies and the CO2 already captured by energy mic technologies (as Upgrading biogas technology).

![](Carbon_captured_to_be_stored.PNG)

If the CO2 captured to be stored is lower than zero that means that we need more carbon capture for technos than provided. A ratio of carbon captured available is then computed as : 

$$ratio_{cc\_available}  = min(1.0,\frac{cc_{provided}}{cc_{needed}})$$

This ratio is send to technology models that needs carbon capture and their production is consequently impacted : 

$$production  = production*ratio_{cc\_available}$$

## Optimization objective and constraints 

The energy mix discipline is used to computer the objective and the constraints of the optimization. The objective is a weighted aggregation of both CO2 emissions and the energy produced. An inequality constraint is defined as the difference between net energy production and energy demand.


