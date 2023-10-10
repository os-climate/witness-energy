# Hydrogen liquefaction

Hydrogen liquefaction is the process of changing the state of hydrogen from gas to liquid (temperatures of around 20 K). 
This is performed through thermodynamics cycles. 
The data used here are taken from a model based on a four steps process:
- the hydrogen feed is first pressurized and pre-cooled,
- then it is cooled down with liquid nitrogen in a Claude cycle to be below the inversion point
- the stream of cooled gaseous hydrogen is further cooled down and finally partially liquefied using the Joule-Thompson effect
- re-expanded to low pressure
The part of the hydrogen stream that isn't liquified is sent back to the beginning of the cycle.

hydrogen liquefaction is a cooling process that requires the removal of heat to convert gaseous hydrogen into a cryogenic liquid. It does not produce heat as a primary output; instead, it consumes energy to achieve low temperatures.

![liquefaction cycle](./Liquefaction_cycle.PNG)
(Image Credit: [^3])

> The Joule-Thompson effect occurs when a real gas goes through a throttle and then into a space where it can expand again and if the enthalpy is conserved. If the gas is below the inversion point (around 80 K for hydrogen) it is cooled down and on the contrary, it is heated up if the gas is above the inversion point.

> Another condition for the hydrogen to be liquified is for it to be in an para-state (opposite to ortho-state): the nuclear spins of the H2 molecule are in opposite directions. In gaseous form, hydrogen is 75% ortho to 25% para, while in liquid form, it is >99% para. The conversion from ortho to para state is achieved naturally below the boiling point but happens slowly, hence a catalyst is usually added to the liquifier plant to accelerate the conversion.

The current liquifier plants have capacities ranging from 6000 to 70000. Trying to take into account the future innovations,
the model is based on a liquifier with a capacity of 200000 kg/day.

<ins>Economic and technical datas are taken from [^1] [^2] [^3].

<ins>For more technical details please read [^4] [^5]:</ins>

[^1]: [Cardella, U., Decker, L. and Klein, H., 2017, February. Economically viable large-scale hydrogen liquefaction. In IOP conference series: materials science and engineering (Vol. 171, No. 1, p. 012013). IOP Publishing.](https://iopscience.iop.org/article/10.1088/1757-899X/171/1/012013)

[^2]: [Integrated Design for Demonstration of Efficient Liquefaction of Hydrogen (IDEALHY) (2013)](https://www.idealhy.eu/uploads/documents/IDEALHY_D5-22_Schedule_demonstration_and_location_web.pdf)

[^3]: [Current Status of Hydrogen Liquefaction Costs, E Connelly and M Penev and A Elgowainy and C Hunter (2019)](https://www.hydrogen.energy.gov/pdfs/19001_hydrogen_liquefaction_costs.pdf)



[^4]: [Large-scale liquid hydrogen production methods and approaches: A review, M Asadnia and M Mehrpooya (2017)](https://www.researchgate.net/publication/321686488_Large-scale_liquid_hydrogen_production_methods_and_approaches_A_review)

[^5]: [Hydrogen liquefaction and liquid hydrogen storage, G Valenti (2016)](https://www.sciencedirect.com/science/article/pii/B978178242362100002X)