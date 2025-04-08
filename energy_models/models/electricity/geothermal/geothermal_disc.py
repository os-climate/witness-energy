'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/03-2024/06/24 Copyright 2023 Capgemini

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

from energy_models.core.techno_type.disciplines.electricity_techno_disc import (
    ElectricityTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.electricity.geothermal.geothermal import Geothermal


class GeothermalDiscipline(ElectricityTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    # ontology information
    _ontology_data = {
        'label': 'Geothermal Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-temperature-high fa-fw',
        'version': '',
    }
    techno_name = GlossaryEnergy.Geothermal
    # Tsiropoulos, I., Tarvydas, D. and Zucker, A., 2018.
    # Cost development of low carbon energy technologies-Scenario-based cost trajectories to 2050, 2017 Edition.
    # Publications Office of the European Union, Luxemburgo.


    techno_infos_dict_default = {'maturity': 0,
                                 'Opex_percentage': 0.045,
                                 # Fixed 4.0% and recurrent 0.5 %
                                 # Demystifying-the-Costs-of-Electricity-Generation-Technologies, average
                                 'WACC': 0.048,  # Weighted averaged cost of capital / ATB NREL 2020
                                 # Zucker, A., 2018. Cost development of low carbon energy technologies.
                                 # https://publications.jrc.ec.europa.eu/repository/bitstream/JRC109894/cost_development_of_low_carbon_energy_technologies_v2.2_final_online.pdf
                                 'learning_rate': 0.05,
                                 # Timilsina, G.R., 2020.
                                 # Demystifying the Costs of Electricity Generation Technologies.
                                 # https://openknowledge.worldbank.org/bitstream/handle/10986/34018/Demystifying-the-Costs-of-Electricity-Generation-Technologies.pdf?sequence=4
                                 'Capex_init': 4275,  # average
                                 'Capex_init_unit': '$/kW',
                                 'full_load_hours': 8760.0,  # Full year hours
                                 # Demystifying-the-Costs-of-Electricity-Generation-Technologies
                                 'capacity_factor': 0.85,
                                 'techno_evo_eff': 'no',
                                 'efficiency': 0.16,
                                 # https://www.sciencedirect.com/science/article/abs/pii/S0375650513001120
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 f"{GlossaryEnergy.CopperResource}_needs": 1100 /1e9, # No data found, therefore we make the assumption that it needs at least a generator which uses the same amount of copper as a gaz powered station. It needs 1100 kg / MW. Computing the need in Mt/MW
                                 # no data, assuming it needs at least enough copper for a generator (such as the gas_turbine)
                                 }

    techno_info_dict = techno_infos_dict_default
    # Initial production in TWh at year_start, 621 GW / GWEC
    # Annual-Wind-Report_2019_digital_final_2r
    initial_production = 92

    # Invest from IRENA
    # Renewable Power Generation Costs in 2020
    # https://www.irena.org/publications/2021/Jun/Renewable-Power-Costs-in-2020
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
                      }
    # -- add specific techno outputs to this
    DESC_IN.update(ElectricityTechnoDiscipline.DESC_IN)

    DESC_OUT = ElectricityTechnoDiscipline.DESC_OUT

    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = Geothermal(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    def get_charts_consumption_and_production(self):
        "Adds the chart specific for resources needed for construction"
        instanciated_chart = super().get_charts_consumption_and_production()
        techno_consumption = self.get_sosdisc_outputs(
            GlossaryEnergy.TechnoDetailedConsumptionValue)

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
