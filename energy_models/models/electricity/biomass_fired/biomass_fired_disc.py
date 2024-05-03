'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/18-2023/11/16 Copyright 2023 Capgemini

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
from energy_models.glossaryenergy import GlossaryEnergy

'''
mode: python; py-indent-offset: 4; tab-width: 8; coding: utf-8
'''
import pandas as pd
import numpy as np

from energy_models.core.techno_type.disciplines.electricity_techno_disc import ElectricityTechnoDiscipline
from energy_models.models.electricity.biomass_fired.biomass_fired import BiomassFired
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import TwoAxesInstanciatedChart, \
    InstanciatedSeries
from energy_models.core.stream_type.resources_models.resource_glossary import ResourceGlossary
from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry


class BiomassFiredDiscipline(ElectricityTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Biomass Fired Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-burn fa-fw',
        'version': '',
    }

    techno_name = GlossaryEnergy.BiomassFired
    lifetime = 25  # Value for CHP units
    construction_delay = 2  # years

    # Source for Initial prod in TWh (2019):
    # IEA 2022, Data Tables
    # https://www.iea.org/data-and-statistics/data-tables?country=WORLD&energy=Renewables%20%26%20waste&year=2019,
    # License: CC BY 4.0.
    # biomass is primary solid biofuels
    initial_production = 443.085

    # IEA 2022, Data Tables,
    # https://www.iea.org/data-and-statistics/data-tables?country=WORLD&energy=Renewables%20%26%20waste&year=2019
    # License: CC BY 4.0.
    # Electricity plants consumption: 3650996 TJ net -> 3650.996 / 3.6 TWh
    biomass_needs = (3650.996 / 3.6) / \
                    initial_production  # ratio without dimension

    # IRENA Power Generation Cost 2019 Report
    # https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2020/Jun/IRENA_Power_Generation_Costs_2019.pdf
    # pages 110 to 119

    # Whole Building Design Guide
    # https://www.wbdg.org/resources/biomass-electricity-generation

    techno_infos_dict_default = {'maturity': 5,
                                 # IRENA (mean of 2% - 6%)
                                 'Opex_percentage': 0.04,
                                 'WACC': 0.075,
                                 'learning_rate': 0,
                                 'lifetime': lifetime,
                                 # IRENA (value from Figure 7.1, page 111)
                                 'Capex_init': 3000,
                                 'Capex_init_unit': '$/kW',
                                 # IRENA (value from Figure 7.1, page 111)
                                 'capacity_factor': 0.80,
                                 'biomass_needs': biomass_needs,
                                 'efficiency': 1,
                                 'techno_evo_eff': 'no',  # yes or no
                                 GlossaryEnergy.ConstructionDelay: construction_delay,
                                 'full_load_hours': 8760,
                                 'copper_needs': 1100,
                                 # no data, assuming it needs at least enough copper for a generator (such as the gas_turbine)
                                 }

    # From IRENA Data
    # https://public.tableau.com/views/IRENARETimeSeries/Charts?:embed=y&:showVizHome=no&publish=yes&:toolbar=no
    # setup = region: all, techno: bioenergy, sub-techno: biomass, flow: installed_capacity
    # (15.414-9.598)/5 = 1.1632 MW per year increase
    invest_before_year_start = pd.DataFrame(
        {'past years': np.arange(-construction_delay, 0),
         GlossaryEnergy.InvestValue: [1.1632 * 3000 / 1000, 1.1632 * 3000 / 1000]})
    # In G$

    # From IRENA Data
    # https://public.tableau.com/views/IRENARETimeSeries/Charts?:embed=y&:showVizHome=no&publish=yes&:toolbar=no
    # setup = region: all, techno: bioenergy, sub-techno: biomass, flow: installed_capacity
    # (15.414-9.598)/5 = 1.1632 MW per year increase
    # 1.1632 / 15.414 ~= 7.5% added production each year (linear approximation)
    initial_age_distribution = pd.DataFrame({'age': np.arange(1, lifetime),
                                             'distrib': [100 - 12 * 7.5, 7.5, 7.5, 7.5, 7.5,
                                                         7.5, 7.5, 7.5, 7.5, 7.5,
                                                         7.5, 7.5, 7.5, 0.0, 0.0,
                                                         0.0, 0.0, 0.0, 0.0, 0.0,
                                                         0.0, 0.0, 0.0, 0.0]})

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float', 'unit': 'TWh', 'default': initial_production},
               'initial_age_distrib': {'type': 'dataframe', 'unit': '%', 'default': initial_age_distribution,
                                       'dataframe_descriptor': {'age': ('int', [0, 100], False),
                                                                'distrib': ('float', None, True)},
                                       'dataframe_edition_locked': False},
               GlossaryEnergy.InvestmentBeforeYearStartValue: {'type': 'dataframe', 'unit': 'G$',
                                                               'default': invest_before_year_start,
                                                               'dataframe_descriptor': {
                                                                   'past years': ('int', [-20, -1], False),
                                                                   GlossaryEnergy.InvestValue: ('float', None, True)},
                                                               'dataframe_edition_locked': False},
               }
    # -- add specific techno inputs to this
    DESC_IN.update(ElectricityTechnoDiscipline.DESC_IN)

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = BiomassFired(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    def get_charts_consumption_and_production(self):
        "Adds the chart specific for resources needed for construction"
        instanciated_chart = super().get_charts_consumption_and_production()
        techno_consumption = self.get_sosdisc_outputs(
            GlossaryEnergy.TechnoDetailedConsumptionValue)

        new_chart_copper = None
        for product in techno_consumption.columns:

            if product != GlossaryEnergy.Years and product.endswith(f'(Mt)'):
                if ResourceGlossary.CopperResource in product:
                    chart_name = f'Mass consumption of copper for the {self.techno_name} technology with input investments'
                    new_chart_copper = TwoAxesInstanciatedChart(
                        GlossaryEnergy.Years, 'Mass [t]', chart_name=chart_name, stacked_bar=True)

        for reactant in techno_consumption.columns:
            if ResourceGlossary.CopperResource in reactant:
                legend_title = f'{reactant} consumption'.replace(
                    ' (Mt)', "")
                mass = techno_consumption[reactant].values * 1000 * 1000  # convert Mt in t for more readable post-proc
                serie = InstanciatedSeries(
                    techno_consumption[GlossaryEnergy.Years].values.tolist(),
                    mass.tolist(), legend_title, 'bar')
                new_chart_copper.series.append(serie)
        instanciated_chart.append(new_chart_copper)

        return instanciated_chart

    def compute_sos_jacobian(self):
        ElectricityTechnoDiscipline.compute_sos_jacobian(self)

        # the generic gradient for production column is not working because of
        # abandoned mines not proportional to production

        scaling_factor_invest_level, scaling_factor_techno_production = self.get_sosdisc_inputs(
            ['scaling_factor_invest_level', 'scaling_factor_techno_production'])
        applied_ratio = self.get_sosdisc_outputs(
            'applied_ratio')['applied_ratio'].values

        dprod_name_dinvest = (
                                         self.dprod_dinvest.T * applied_ratio).T * scaling_factor_invest_level / scaling_factor_techno_production
        consumption_gradient = self.techno_consumption_derivative[
            f'{BiomassDry.name} ({self.techno_model.product_energy_unit})']
        # self.techno_consumption_derivative[f'{SolidFuel.name} ({self.product_energy_unit})']
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoProductionValue,
             f'{hightemperatureheat.name} ({self.techno_model.product_energy_unit})'),
            (GlossaryEnergy.InvestLevelValue, GlossaryEnergy.InvestValue),
            (consumption_gradient - dprod_name_dinvest))
