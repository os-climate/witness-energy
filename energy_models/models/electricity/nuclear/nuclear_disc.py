'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/06-2023/11/16 Copyright 2023 Capgemini

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

from climateeconomics.glossarycore import GlossaryCore
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.techno_type.disciplines.electricity_techno_disc import ElectricityTechnoDiscipline
from energy_models.models.electricity.nuclear.nuclear import Nuclear
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import TwoAxesInstanciatedChart, \
    InstanciatedSeries


class NuclearDiscipline(ElectricityTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    # ontology information
    _ontology_data = {
        'label': 'Nuclear Energy Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-atom fa-fw',
        'version': '',
    }
    techno_name = 'Nuclear'
    # Cole, W.J., Gates, N., Mai, T.T., Greer, D. and Das, P., 2020.
    # 2019 standard scenarios report: a US electric sector outlook (No. NREL/PR-6A20-75798).
    # National Renewable Energy Lab.(NREL), Golden, CO (United States).
    lifetime = 60
    # Timilsina, G.R., 2020. Demystifying the Costs of Electricity Generation
    # Technologies., average
    construction_delay = 6

    techno_infos_dict_default = {'maturity': 0,
                                 'Opex_percentage': 0.024,
                                 # Fixed 1.9 and recurrent 0.5 %
                                 # Demystifying-the-Costs-of-Electricity-Generation-Technologies, average
                                 'WACC': 0.058,  # Weighted averaged cost of capital / ATB NREL 2020
                                 'learning_rate': 0.00,  # Cost development of low carbon energy technologies
                                 'lifetime': lifetime,
                                 'lifetime_unit': GlossaryCore.Years,
                                 # Demystifying-the-Costs-of-Electricity-Generation-Technologies, average
                                 'Capex_init': 6765,
                                 'Capex_init_unit': '$/kW',
                                 'full_load_hours': 8760.0,  # Full year hours
                                 # Demystifying-the-Costs-of-Electricity-Generation-Technologies, average
                                 'capacity_factor': 0.90,
                                 'techno_evo_eff': 'no',
                                 'efficiency': 0.35,
                                 'useful_heat_recovery_factor': 0.6,
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 GlossaryCore.ConstructionDelay: construction_delay,
                                 'waste_disposal_levy': 0.1 * 1e-2 * 1e3,   # conversion from c/kWh to $/MWh
                                 'waste_disposal_levy_unit': '$/MWh',
                                 'decommissioning_cost': 1000,
                                 'decommissioning_cost_unit': '$/kW',
                                 # World Nuclear Waste Report 2019, Chapter 6 (https://worldnuclearwastereport.org)
                                 # average of 1000 $/kW
                                 'copper_needs': 1473, #IEA Executive summary - Role of critical minerals in clean energy transitions 2022
                                 }

    techno_info_dict = techno_infos_dict_default
    # Initial production in TWh at year_start IAEA - IAEA_Energy Electricity
    # and Nuclear Power Estimates up to 2050
    initial_production = 2657.0
    # Invest in 2019 => 29.6 bn
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0), GlossaryCore.InvestValue: [30.0, 29.0, 33.0,
                                                                     34.0, 33.0, 39.0]})

    # Age distribution => IAEA OPEX Nuclear 2020 - Number of Reactors by Age
    # (as of 1 January 2020)
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [
                                                 1.36, 2.04, 0.91, 2.27, 2.27, 1.13, 0.91, 0.68, 1.59, 1.13, 0.45, 0.68,
                                                 0.45, 0.91, 1.13, 0.45, 1.36, 0.68, 1.36, 0.91, 0.91, 0.68, 1.36, 0.91,
                                                 1.13, 2.04, 1.36, 0.91, 2.27, 2.49, 3.17, 4.76, 5.22, 7.26, 6.80, 3.85,
                                                 3.40, 4.31, 4.08, 1.13, 2.04, 1.59, 3.17, 2.27, 3.40, 2.04, 1.59, 1.36,
                                                 0.68, 1.15, 0, 0, 0, 0, 0, 0, 0, 0, 0
    ]
    })

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int',  [0, 100], False),
                                                                'distrib': ('float',  None, True)},
                                       'dataframe_edition_locked': False},
               GlossaryCore.InvestmentBeforeYearStartValue: {'type': 'dataframe', 'unit': 'G$', 'default': invest_before_year_start,
                                        'dataframe_descriptor': {'past years': ('int',  [-20, -1], False),
                                                                 GlossaryCore.InvestValue: ('float',  None, True)},
                                        'dataframe_edition_locked': False}}
    # -- add specific techno outputs to this
    DESC_IN.update(ElectricityTechnoDiscipline.DESC_IN)

    DESC_OUT = ElectricityTechnoDiscipline.DESC_OUT

    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = Nuclear(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    
    def get_charts_consumption_and_production(self):
        "Adds the chart specific for resources needed for construction"
        instanciated_chart = super().get_charts_consumption_and_production()
        techno_consumption = self.get_sosdisc_outputs(
            GlossaryCore.TechnoDetailedConsumptionValue)

        new_chart_copper = None
        for product in techno_consumption.columns:

            if product != GlossaryCore.Years and product.endswith(f'(Mt)'):
                if ResourceGlossary.Copper['name'] in product :
                    chart_name = f'Mass consumption of copper for the {self.techno_name} technology with input investments'
                    new_chart_copper = TwoAxesInstanciatedChart(
                        GlossaryCore.Years, 'Mass [t]', chart_name=chart_name, stacked_bar=True)

        for reactant in techno_consumption.columns:
            if ResourceGlossary.Copper['name'] in reactant:
                legend_title = f'{reactant} consumption'.replace(
                    ' (Mt)', "")
                mass = techno_consumption[reactant].values * 1000 * 1000 #convert Mt in t for more readable post-proc
                serie = InstanciatedSeries(
                    techno_consumption[GlossaryCore.Years].values.tolist(),
                    mass.tolist(), legend_title, 'bar')
                new_chart_copper.series.append(serie)
        instanciated_chart.append(new_chart_copper)
        
        return instanciated_chart
    

    def get_chart_detailed_price_in_dollar_kwh(self):
        """
        overloads the price chart from techno_disc to display decommissioning costs
        """

        new_chart = ElectricityTechnoDiscipline.get_chart_detailed_price_in_dollar_kwh(
            self)

        # decommissioning price part
        techno_infos_dict = self.get_sosdisc_inputs('techno_infos_dict')
        techno_detailed_prices = self.get_sosdisc_outputs(
            GlossaryCore.TechnoDetailedPricesValue)
        ratio = techno_infos_dict['decommissioning_cost'] / \
            techno_infos_dict['Capex_init']
        decommissioning_price = ratio * \
            techno_detailed_prices[f'{self.techno_name}_factory'].values

        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryCore.Years].values.tolist(),
            decommissioning_price.tolist(), 'Decommissioning (part of Factory)', 'lines')

        new_chart.series.append(serie)

        waste_disposal_levy_mwh = techno_detailed_prices['waste_disposal']
        serie = InstanciatedSeries(
            techno_detailed_prices[GlossaryCore.Years].values.tolist(),
            waste_disposal_levy_mwh.tolist(), 'Waste Disposal (part of Energy)', 'lines')

        new_chart.series.append(serie)

        return new_chart

    # def compute_sos_jacobian(self):
    #     ElectricityTechnoDiscipline.compute_sos_jacobian(self)
    #
    #     # the generic gradient for production column is not working because of
    #     # abandoned mines not proportional to production
    #
    #     scaling_factor_invest_level, scaling_factor_techno_production = self.get_sosdisc_inputs(
    #         ['scaling_factor_invest_level', 'scaling_factor_techno_production'])
    #     applied_ratio = self.get_sosdisc_outputs(
    #         'applied_ratio')['applied_ratio'].values
    #
    #     dprod_name_dinvest = (self.dprod_dinvest.T * applied_ratio).T * scaling_factor_invest_level / scaling_factor_techno_production
    #     consumption_gradient = self.techno_consumption_derivative[f'{BiomassDry.name} ({self.techno_model.product_energy_unit})']
    #     #self.techno_consumption_derivative[f'{SolidFuel.name} ({self.product_energy_unit})']
    #     self.set_partial_derivative_for_other_types(
    #         (GlossaryCore.TechnoProductionValue,
    #          f'{hightemperatureheat.name} ({self.techno_model.product_energy_unit})'), (GlossaryCore.InvestLevelValue, GlossaryCore.InvestValue),
    #         (consumption_gradient- dprod_name_dinvest))