# Documentation 

The energy demand model gathers demand models for energies and computes a constraint for the optimization process. The constraint is simply to check that the energy production is higher than its demand. 


## Electricity demand model 

The electricity demand model computes the demand in electricity varying in time with the population number and an electrical machine efficiency

$$electricity\_demand  = init\_elec\_demand*\frac{population}{population[2020]}*\frac{EM\_efficiency[2020]}{EM\_efficiency}$$

with the init_elec_demand = 22847.66 TWh by default. 

The EM_efficiency is computed with a sigmoid function calibrated to be equals to 0.95 in 2020, 0.98 in 2025 and 0.985 in the distant future (see post-processing).

The electricity demand_constraint is finally computed :

$$electricity\_demand\_constraint  = -\frac{electricity\_prod - electricity\_demand}{ref \Delta t}$$

with a reference defined in input parameters. 