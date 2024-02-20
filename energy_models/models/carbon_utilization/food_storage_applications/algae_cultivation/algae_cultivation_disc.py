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
from energy_models.models.carbon_utilization.food_storage_applications.algae_cultivation.algae_cultivation import AlgaeCultivation


class AlgaeCultivationDiscipline(CUTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    # ontology information
    _ontology_data = {
        'label': 'Algae Cultivation Model',
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
    techno_name = 'food_storage_applications.AlgaeCultivation'
    lifetime = 35  # 15  # https://www.sciencedirect.com/science/article/abs/pii/S2211926418300808
    construction_delay = 3
    techno_infos_dict_default = {'maturity': 0,
                                 # Husebye, J., Brunsvold, A.L., Roussanaly, S. and Zhang, X., 2012.
                                 # Techno economic evaluation of amine based CO2 capture: impact of CO2 concentration and steam supply.
                                 # Energy Procedia, 23, pp.381-390.
                                 'Opex_percentage': 0.34,   #https://www.sciencedirect.com/science/article/pii/S004896972202839X
                                 'elec_demand': 0.7,    # https://www.sciencedirect.com/science/article/pii/S2211926417306677#:~:text=For%20closed%20cultivation%20systems%20the,kWh%C2%B7kg%E2%88%92%201%20algae.
                                'elec_demand_unit': 'kWh/kg',
                                 # Fasihi, M., Efimova, O. and Breyer, C., 2019.
                                 # Techno-economic assessment of CO2 direct air capture plants.
                                 # Journal of cleaner production, 224, pp.957-980.
                                 # for now constant in time but should increase
                                 # with time 10%/10year according to Fasihi2019
                                 'heat_demand': 0.036,    # https://downloads.hindawi.com/journals/ijce/2010/102179.pdf # page no.6
                                 'heat_demand_unit': 'kWh/kgCO2',
                                 'WACC': 0.1,  # Weighted averaged cost of capital for the carbon capture plant
                                 'learning_rate': 0.1,
                                 'maximum_learning_capex_ratio': 0.33,
                                 'lifetime': lifetime,  # should be modified
                                 'lifetime_unit': GlossaryEnergy.Years,
                                 # 0.6577,  # 730 euro/tCO2 in Fashi2019 Capex
                                 # initial at year 2020 1.11 euro/$
                                 'Capex_init': 1.47,  # https://www.osti.gov/servlets/purl/1845001 # page no. 17
                                 'Capex_init_unit': '$/kgCO2',
                                 'efficiency': 0.98,    # https://energsustainsoc.biomedcentral.com/articles/10.1186/s13705-020-00262-5
                                 'CO2_capacity_peryear': 2.425,  # https://mdpi-res.com/d_attachment/sustainability/sustainability-13-13061/article_deploy/sustainability-13-13061-v2.pdf?version=1637918442
                                 'CO2_capacity_peryear_unit': 'kg CO2/year',
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
                                 'enthalpy': 0.416667,
                                 'enthalpy_unit': 'kWh/kgC02',
                                 GlossaryEnergy.EnergyEfficiency: 0.78,
                                 GlossaryEnergy.ConstructionDelay: construction_delay,
                                 'nitrogen_needs': 0.36,     # https://www.osti.gov/servlets/purl/1785547#:~:text=Approximately%200.36%20kg%20of%20nitrogen,%25%20lipid%20content%20(6).
                                 'nitrogen_needs_unit': 'kg/kg',
                                 'phosphorus_needs': 0.023,   # https://www.researchgate.net/figure/Summary-of-LCA-Nutrient-Input-Data-for-Production-of-1-kg-Dry-Algal-Biomass-the-Types_tbl2_305791188#:~:text=%5B257%5D%20investigated%20the%20nutrient%20requirements,...
                                 'phosphorus_needs_unit': 'kg/kg',
                                 'techno_evo_eff': 'no',
                                 'water_demand': 3726,      # https://www.sciencedirect.com/science/article/abs/pii/S0960852414015727
                                 'water_demand_unit': 'kg/kg',
                                 'co2_needs': 1.8,           # https://www.sciencedirect.com/science/article/pii/S2772427122000948
                                 'co2_needs_unit': 'kg/kg',
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

    initial_utilization = 13.986   # in Mt at year_start # https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6999637/
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
    FOOD_STORAGE_RATIO = np.array([0.0350])

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float', 'unit': 'MtCO2', 'default': initial_utilization},
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
        self.techno_model = AlgaeCultivation(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)
        # co2 = self.get_sosdisc_outputs(GlossaryEnergy.TechnoDetailedProductionValue)

        # print(co2.to_string())



    def compute_sos_jacobian(self):
        # Grad of price vs energyprice

        CUTechnoDiscipline.compute_sos_jacobian(self)

        grad_dict = self.techno_model.grad_price_vs_energy_price()
        grad_dict_resources = self.techno_model.grad_price_vs_resources_price()
        carbon_emissions = self.get_sosdisc_outputs(GlossaryEnergy.CO2EmissionsValue)
        self.set_partial_derivatives_techno(
            grad_dict, carbon_emissions, grad_dict_resources)

