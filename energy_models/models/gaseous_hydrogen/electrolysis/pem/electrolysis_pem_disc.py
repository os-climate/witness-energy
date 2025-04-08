'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2024/06/24 Copyright 2023 Capgemini

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

from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import (
    InstanciatedSeries,
    TwoAxesInstanciatedChart,
)

from energy_models.core.techno_type.disciplines.gaseous_hydrogen_techno_disc import (
    GaseousHydrogenTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.gaseous_hydrogen.electrolysis.pem.electrolysis_pem import (
    ElectrolysisPEM,
)


class ElectrolysisPEMDiscipline(GaseousHydrogenTechnoDiscipline):
    """
    Electrolysis PEM Discipline
    """

    # ontology information
    _ontology_data = {
        'label': 'Hydrogen Electrolysis PEM Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-hospital-symbol fa-fw',
        'version': '',
    }
    techno_name = GlossaryEnergy.ElectrolysisPEM
    # Fuel Cells and Hydrogen 2 Joint Undertaking 2018
    # LAUNCH OF REFHYNE, WORLD'S LARGEST ELECTROLYSIS PLANT IN RHINELAND REFINERY
    # https://www.fch.europa.eu/news/launch-refhyne-worlds-largest-electrolysis-plant-rhineland-refinery

    techno_infos_dict_default = {'maturity': 5,
                                 'Opex_percentage': 0.025,
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'WACC': 0.05,
                                 'learning_rate': 0.15,
                                 'maximum_learning_capex_ratio': 500.0 / 1012.5,  # 500 euro/kw minimum capex
                                 'stack_lifetime': 100000,
                                 'stack_lifetime_unit': 'hours',
                                 'Capex_init': 1012.5,  # for a power input of 2MW, decreases for 10 MW
                                 'Capex_init_unit': 'euro/kW',
                                 'euro_dollar': 1.114,
                                 'full_load_hours': 8000,
                                 'techno_evo_eff': 'yes',
                                 'techno_evo_time': 10,
                                 'efficiency evolution slope': 0.5,
                                 # electric efficiency that we will use to
                                 # compute elec needs
                                 'efficiency': 0.65,
                                 'efficiency_max': 0.75,
                                 'platinum_needs': 1.0 / 8.0,  # Fuel Cell technologies Office 2017
                                 'platinum_needs_units': 'g/KW', }

    # Around 50MW of nominal power *8000 hours per year
    initial_production = 0.4
    # Industrial plants started to emerge around 2015
    # Public investment in Europe through FCH JU : 156 MEuro or 190M$
    # We assume half is for PEM .
    # Worldwide the investment of europe for PEM is 36%   190/2*100/36 = 263.9 M$
    # https://www.euractiv.com/section/energy/news/europe-china-battle-for-global-supremacy-on-electrolyser-manufacturing/
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'initial_production': {'type': 'float',
                                      'unit': 'TWh', 'default': initial_production},
               }
    DESC_IN.update(GaseousHydrogenTechnoDiscipline.DESC_IN)

    # -- add specific techno outputs to this
    DESC_OUT = GaseousHydrogenTechnoDiscipline.DESC_OUT

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = ElectrolysisPEM(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    def get_charts_consumption_and_production(self):
        "Adds the chart specific for resources needed for construction"
        instanciated_chart = super().get_charts_consumption_and_production()
        techno_consumption = self.get_sosdisc_outputs(
            GlossaryEnergy.TechnoDetailedConsumptionValue)

        new_chart_platinum = None
        for product in techno_consumption.columns:

            if product != GlossaryEnergy.Years and product.endswith('(Mt)'):
                if GlossaryEnergy.PlatinumResource in product:
                    chart_name = f'Mass consumption of platinum for the {self.techno_name} technology with input investments'
                    new_chart_platinum = TwoAxesInstanciatedChart(
                        GlossaryEnergy.Years, 'Mass [kg]', chart_name=chart_name, stacked_bar=True)

        for reactant in techno_consumption.columns:
            if GlossaryEnergy.PlatinumResource in reactant:
                legend_title = f'{reactant} consumption'.replace(
                    ' (Mt)', "")
                mass = techno_consumption[
                           reactant].values * 1000 * 1000 * 1000  # convert Mt in kg for more readable post-proc
                serie = InstanciatedSeries(
                    techno_consumption[GlossaryEnergy.Years].values.tolist(),
                    mass.tolist(), legend_title, 'bar')
                new_chart_platinum.series.append(serie)
        instanciated_chart.append(new_chart_platinum)

        return instanciated_chart
