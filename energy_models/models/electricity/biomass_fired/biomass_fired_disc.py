'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/18-2024/06/24 Copyright 2023 Capgemini

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
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import (
    InstanciatedSeries,
    TwoAxesInstanciatedChart,
)

from energy_models.core.techno_type.disciplines.electricity_techno_disc import (
    ElectricityTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.electricity.biomass_fired.biomass_fired import BiomassFired


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

    FLUE_GAS_RATIO = np.array([0.13])

    techno_infos_dict_default = {'maturity': 5,
                                 # IRENA (mean of 2% - 6%)
                                 'Opex_percentage': 0.04,
                                 'WACC': 0.075,
                                 'learning_rate': 0,
                                 # IRENA (value from Figure 7.1, page 111)
                                 'Capex_init': 3000,
                                 'Capex_init_unit': '$/kW',
                                 # IRENA (value from Figure 7.1, page 111)
                                 'capacity_factor': 0.80,
                                 'biomass_needs': biomass_needs,
                                 'efficiency': 1,
                                 'techno_evo_eff': 'no',  # yes or no
                                 'full_load_hours': 8760,
                                 f"{GlossaryEnergy.CopperResource}_needs": 1100 / 1e9 #No data found, therefore we make the assumption that it needs at least a generator which uses the same amount of copper as a gaz powered station. It needs 1100 kg / MW. Computing the need in Mt/MW,
                                 # no data, assuming it needs at least enough copper for a generator (such as the gas_turbine)
                                 }

    # From IRENA Data
    # https://public.tableau.com/views/IRENARETimeSeries/Charts?:embed=y&:showVizHome=no&publish=yes&:toolbar=no
    # setup = region: all, techno: bioenergy, sub-techno: biomass, flow: installed_capacity
    # (15.414-9.598)/5 = 1.1632 MW per year increase

    # From IRENA Data
    # https://public.tableau.com/views/IRENARETimeSeries/Charts?:embed=y&:showVizHome=no&publish=yes&:toolbar=no
    # setup = region: all, techno: bioenergy, sub-techno: biomass, flow: installed_capacity
    # (15.414-9.598)/5 = 1.1632 MW per year increase
    # 1.1632 / 15.414 ~= 7.5% added production each year (linear approximation)
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
                      }
    # -- add specific techno inputs to this
    DESC_IN.update(ElectricityTechnoDiscipline.DESC_IN)

    def init_execution(self):
        self.model = BiomassFired(self.techno_name)

    def get_charts_consumption_and_production(self):
        "Adds the chart specific for resources needed for construction"
        instanciated_chart = []
        techno_consumption = self.get_sosdisc_outputs(GlossaryEnergy.TechnoEnergyConsumptionValue)

        new_chart_copper = None
        for product in techno_consumption.columns:

            if product != GlossaryEnergy.Years and product.endswith('(Mt)'):
                if GlossaryEnergy.CopperResource in product:
                    chart_name = f'Mass consumption of copper for the {self.techno_name} technology with input investments'
                    new_chart_copper = TwoAxesInstanciatedChart(
                        GlossaryEnergy.Years, 'Mass [t]', chart_name=chart_name, stacked_bar=True)

        for reactant in techno_consumption.columns:
            if GlossaryEnergy.CopperResource in reactant:
                legend_title = f'{reactant} consumption'.replace(
                    ' (Mt)', "")
                mass = techno_consumption[reactant].values * 1000 * 1000  # convert Mt in t for more readable post-proc
                serie = InstanciatedSeries(
                    techno_consumption[GlossaryEnergy.Years].values.tolist(),
                    mass.tolist(), legend_title, 'bar')
                new_chart_copper.series.append(serie)
        instanciated_chart.append(new_chart_copper)

        return instanciated_chart
