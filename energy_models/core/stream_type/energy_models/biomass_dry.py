'''
Copyright 2022 Airbus SAS
Modifications on 2024/02/01 Copyright 2024 Capgemini
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

'''
from energy_models.core.stream_type.energy_type import EnergyType
from energy_models.glossaryenergy import GlossaryEnergy


class BiomassDry(EnergyType):
    name = GlossaryEnergy.biomass_dry
    default_techno_list = ['ManagedWood', 'UnmanagedWood', 'CropEnergy']
    data_energy_dict = {'maturity': 5,
                        'WACC': 0.1,
                        # Raffa, D.W., Bogdanski, A. and Tittonell, P., 2015.
                        # How does crop residue removal affect soil organic carbon and yield?
                        # A hierarchical analysis of management and environmental factors.
                        # Biomass and Bioenergy, 81, pp.345-355.
                        # http://repo-desa.inta.gob.ar/xmlui/bitstream/handle/20.500.12123/1303/INTA_CRPatagoniaNorte-EEABariloche_WarrenRaffa_D_How_does_crop_residue_removal_affect_soil.pdf?sequence=3
                        # The paper says 42.5% of carbon in biomass meaning
                        # 0.425g of C in 1 kg of biomass meaning in term of CO2
                        GlossaryEnergy.CO2PerUse: 0.425 * 44.01 / 12.0,
                        'CO2_per_use_unit': 'kg/kg',
                        # Bray & al : Global emissions of NH3, NOx, and N2O from biomass burning and the impact of climate change
                        # https://www.tandfonline.com/doi/epub/10.1080/10962247.2020.1842822?needAccess=true
                        # 0.3 g/kg
                        GlossaryEnergy.N2OPerUse: 0.3e-3,
                        'N2O_per_use_unit': 'kg/kg',
                        # Whittaker, C., Macalpine, W., Yates, N.E. et al.
                        # Dry Matter Losses and Methane Emissions During Wood
                        # Chip Storage: the Impact on Full Life Cycle
                        # Greenhouse Gas Savings of Short Rotation Coppice
                        # Willow for Heat. Bioenerg. Res. 9, 820-835 (2016).
                        # https://doi.org/10.1007/s12155-016-9728-0
                        # Bond, T. C., et al 2013.
                        # Bounding the role of black carbon in the climate system: A scientific assessment.
                        # Journal of geophysical research: Atmospheres,
                        # 118(11), pp.5380-5552.
                        'CH4_per_energy': 0.01,
                        'CH4_per_energy_unit': 'kg/kg',
                        'density': 380,  # for woodchip
                        'density_unit': 'kg/m^3',
                        # Calorific value of the fully dried biomass (forest residue) from:
                        # H2tools, Pacific Northwest National Laboratory
                        # https://h2tools.org/hyarc/calculator-tools/lower-and-higher-heating-values-fuels
                        # Given H(w) the calorific value of the moisturized wood
                        # H(wf) the calorific value of the fully dried wood and w the moisture percentage
                        # The formula is H(w)= [H(wf)(100-w)-2.44w]/100 and comes from:
                        # Food and Agriculture Organization of the United-Nations (FAO):
                        # https://www.fao.org/3/j4504e/j4504e08.htm
                        # H(w)= [15.40MJ.kg-1*0.27778kWh.MJ-1 *
                        # (100-15)-2.44*15]/100 for wood moisturize
                        'calorific_value': 3.6,  # mean calorific value residue / wood,
                        # lower value for electricity use
                        'calorific_value_unit': 'kWh/kg',
                        'high_calorific_value': 5.61,
                        'high_calorific_value_unit': 'kWh/kg',
                        # percentage content of water
                        'moisture': 0.15}
