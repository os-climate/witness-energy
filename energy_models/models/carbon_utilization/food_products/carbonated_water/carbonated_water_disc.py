'''
Copyright 2023 Capgemini

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

import numpy as np
import pandas as pd

from energy_models.core.techno_type.disciplines.carbon_utilization_techno_disc import CUTechnoDiscipline
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.carbon_utilization.food_products.carbonated_water.carbonated_water import CarbonatedWater


class CarbonatedWaterDiscipline(CUTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    # ontology information
    _ontology_data = {
        'label': 'Carbonated Water Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-globe-europe fa-fw',
        'version': '',
    }
    techno_name = 'food_products.CarbonatedWater'
    # https://patents.google.com/patent/US6060103A/en
    # https://drinkheartwater.com/blog/does-bottled-water-go-bad
    # https://en.wikipedia.org/wiki/Carbonated_water
    lifetime = 35        #2
    construction_delay = 3
    techno_infos_dict_default = {'maturity': 0,
                                 'reaction': 'CO2 + H2O <--> H2CO3',
                                 # Husebye, J., Brunsvold, A.L., Roussanaly, S. and Zhang, X., 2012.
                                 # Techno economic evaluation of amine based CO2 capture: impact of CO2 concentration and steam supply.
                                 # Energy Procedia, 23, pp.381-390.
                                 # Opex % : fig 5 - 6 :
                                 'Opex_percentage': 0.35,  #https://www.atlantis-press.com/article/125971500.pdf
                                 'elec_demand': 3.19,      # https://www.google.com/search?q=carbonated+water+process+how+much+electricity+used+in+kwh+&sca_esv=b9eca7660d2a1203&rlz=1C1UEAD_enIN1000IN1000&sxsrf=ACQVn0_mLwbL4I9MG04Nw-xDXYROrfmkdg%3A1707333796755&ei=pNjDZafhLdKeseMP8OGy6Ao&ved=0ahUKEwinw9-D-pmEAxVST2wGHfCwDK0Q4dUDCBA&uact=5&oq=carbonated+water+process+how+much+electricity+used+in+kwh+&gs_lp=Egxnd3Mtd2l6LXNlcnAiOmNhcmJvbmF0ZWQgd2F0ZXIgcHJvY2VzcyBob3cgbXVjaCBlbGVjdHJpY2l0eSB1c2VkIGluIGt3aCBIAFAAWABwAHgBkAEAmAEAoAEAqgEAuAEDyAEA-AEB4gMEGAAgQQ&sclient=gws-wiz-serp#ip=1
                                 'elec_demand_unit': 'kWh/kg',
                                 # Fasihi, M., Efimova, O. and Breyer, C., 2019.
                                 # Techno-economic assessment of CO2 direct air capture plants.
                                 # Journal of cleaner production, 224, pp.957-980.
                                 # for now constant in time but should increase
                                 # with time 10%/10year according to Fasihi2019
                                 'heat_demand': 0.00026,     # https://pubs.acs.org/doi/10.1021/acssuschemeng.0c08561
                                 'heat_demand_unit': 'kWh/kg',
                                 'WACC': 0.1,  # Weighted averaged cost of capital for the carbon capture plant
                                 'learning_rate': 0.1,
                                 'maximum_learning_capex_ratio': 0.33,
                                 'lifetime': lifetime,  # should be modified
                                 'lifetime_unit': GlossaryEnergy.Years,
                                 # 0.6577,  # 730 euro/tCO2 in Fashi2019 Capex
                                 # initial at year 2020 1.11 euro/$
                                 'Capex_init': 0.12,                         # https://www.sciencedirect.com/topics/engineering/mineral-carbonation
                                 'Capex_init_unit': '$/kgCO2',
                                 'efficiency': 0.9,                          # https://www.scripps.org/news_items/5224-are-carbonated-beverages-harming-your-health
                                                                             # https://www.total-water.com/blog/improving-efficiency-purified-water-treatment-system/
                                 'CO2_capacity_peryear': 230E+9,             # https://www.iea.org/reports/putting-co2-to-use
                                 'CO2_capacity_peryear_unit': 'kg CO2/year', # https://www.google.com/search?q=230+million+tonnes+to+kg&sca_esv=eff03c613f9494ac&rlz=1C1UEAD_enIN1000IN1000&sxsrf=ACQVn08lfyUxK-_CvU8T6kZoS_FZ_BFOXg%3A1707412271742&ei=LwvFZef9LM2cseMPifO12AY&oq=230+million+to+to+kg&gs_lp=Egxnd3Mtd2l6LXNlcnAiFDIzMCBtaWxsaW9uIHRvIHRvIGtnKgIIATIKECEYChigARjDBDIKECEYChigARjDBEisZ1DBBlj5UXABeAGQAQCYAe8BoAHYDqoBBjAuMTMuMbgBAcgBAPgBAcICChAAGEcY1gQYsAPCAg0QABiABBiKBRhDGLADwgIGEAAYBxgewgIKEAAYgAQYigUYQ8ICCBAAGAcYHhgPwgIKEAAYCBgHGB4YD8ICCxAAGIAEGIoFGIYDwgIGEAAYHhgPwgIIEAAYHhgNGA_CAgoQABgIGB4YDxgKwgIHEAAYgAQYDcICDBAhGAoYoAEYwwQYCsICBhAhGAoYCsICCBAhGKABGMME4gMEGAAgQYgGAZAGCg&sclient=gws-wiz-serp
                                 'real_factor_CO2': 1.0,
                                 GlossaryEnergy.TransportCostValue: 0.0,
                                 'transport_cost_unit': '$/kgCO2',
                                 # Keith, D.W., Holmes, G., Angelo, D.S. and Heidel, K., 2018.
                                 # A process for capturing CO2 from the atmosphere.
                                 # Joule, 2(8), pp.1573-1594.
                                 # Vo, T.T., Wall, D.M., Ring, D., Rajendran, K. and Murphy, J.D., 2018.
                                 # Techno-economic analysis of biogas upgrading via amine scrubber, carbon capture and ex-situ methanation.
                                 # Applied energy, 212, pp.1191-1202.
                                 # from Keith2018 3.18 GJ/tCaO in theory 5.25
                                 # GJ/tCO2 in practice (Climeworks)
                                 # according to Vo2018 4GJ/tCO2 or Fasihi2016:
                                 # 1.51 in practice
                                 'enthalpy': 3.19,
                                 'enthalpy_unit': 'kWh/kgC02',
                                 GlossaryEnergy.EnergyEfficiency: 0.78,
                                 GlossaryEnergy.ConstructionDelay: construction_delay,
                                 'techno_evo_eff': 'no',
                                 'water_demand': 1.32,  # https://en.wikipedia.org/wiki/Bottled_water
                                 'water_demand_unit': 'l/l',
                                 'co2_needs': 1,      # https://www.sciencedirect.com/topics/agricultural-and-biological-sciences/carbonation
                                 'co2_needs_unit': 'l/l',
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 }

    # source :
    # Husebye, J., Brunsvold, A.L., Roussanaly, S. and Zhang, X., 2012.
    # Techno economic evaluation of amine based CO2 capture: impact of CO2 concentration and steam supply.
    # Energy Procedia, 23, pp.381-390.
    # Buijs, W. and De Flart, S., 2017.
    # Direct air capture of CO2 with an amine resin: A molecular modeling study of the CO2 capturing process.
    # Industrial & engineering chemistry research, 56(43), pp.12297-12304.

    techno_info_dict = techno_infos_dict_default

    initial_utilize = 10  # in Mt at year_start # https://www.iea.org/reports/putting-co2-to-use
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), GlossaryEnergy.InvestValue: np.array([0.05093, 0.05093, 15.0930]) * 0.8 / 3000})

    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime - 1),
                                             'distrib': [10.0, 10.0, 10.0, 10.0, 10.0,
                                                         10.0, 10.0, 10.0,
                                                         10.0, 10.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0, 0.0, 0.0,
                                                         0.0]
                                             })
    # use the same flue gas ratio as gas turbine one
    FOOD_PRODUCTS_RATIO = np.array([0.0350])

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float', 'unit': 'MtCO2', 'default': initial_utilize},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int',  [0, 100], False),
                                                                'distrib': ('float',  None, True)},
                                       'dataframe_edition_locked': False},
               GlossaryEnergy.InvestmentBeforeYearStartValue: {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 GlossaryEnergy.InvestValue: ('float',  None, True)},
                                        'dataframe_edition_locked': False}}
    # -- add specific techno outputs to this
    DESC_IN.update(CUTechnoDiscipline.DESC_IN)

    DESC_OUT = CUTechnoDiscipline.DESC_OUT

    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = CarbonatedWater(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    # def compute_sos_jacobian(self):
    #     # Grad of price vs energyprice
    #
    #     CUTechnoDiscipline.compute_sos_jacobian(self)
    #
    #     grad_dict = self.techno_model.grad_price_vs_energy_price()
    #     grad_dict_resources = self.techno_model.grad_price_vs_resources_price()
    #     carbon_emissions = self.get_sosdisc_outputs(GlossaryEnergy.CO2EmissionsValue)
    #     self.set_partial_derivatives_techno(
    #         grad_dict, carbon_emissions, grad_dict_resources)
