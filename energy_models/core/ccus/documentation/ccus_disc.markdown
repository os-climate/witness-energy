# Carbon Capture and Storage model 

The Carbon Capture and Storage model in the energy mix model computes the carbon capture stored limited by the CO2 to capture.


Carbon emissions stored by carbon storage technologies are limited by the amount of CO2 captured. Gaseous CO2 storage and solid carbon storage are separated and they are both limited each by the amount of CO2 and solid carbon ready to store. 

![](carbon_stored.PNG)

The Solid carbon ready to store is for now the one created by plasma cracking technology. However the computation of gaseous CO2 ready to store is more complex. The CO2 captured to be stored is the difference between the gaseous CO2 capture provided by the energy mix and the needed one. The CO2 capture provided is the sum of the CO2 really captured by carbon capture technologies and the CO2 already captured by energy mic technologies (as Upgrading biogas technology).

![](Carbon_captured_to_be_stored.PNG)

If the CO2 captured to be stored is lower than zero that means that we need more carbon capture for technos than provided. A ratio of carbon captured available is then computed as : 

$$ratio_{cc\_available}  = min(1.0,\frac{cc_{provided}}{cc_{needed}})$$

This ratio is send to technology models that needs carbon capture and their production is consequently impacted : 

$$production  = production*ratio_{cc\_available}$$


