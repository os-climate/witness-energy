'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2024/06/24 Copyright 2023 Capgemini

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

from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.techno_type.disciplines.electricity_techno_disc import (
    ElectricityTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.electricity.renewable_electricity_simple_techno.renewable_simple_techno import (
    RenewableElectricitySimpleTechno,
)


class RenewableElectricitySimpleTechnoDiscipline(ElectricityTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    # ontology information
    _ontology_data = {
        'label': 'energy_models.models.electricity.renewable_electricity_simple_techno.renewable_electricity_simple_techno_disc',
        'type': 'Test',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': '',
        'version': '',
    }
    data_fuel_dict_default = Electricity.data_energy_dict
    techno_name = GlossaryEnergy.RenewableElectricitySimpleTechno
    # Cole, W.J., Gates, N., Mai, T.T., Greer, D. and Das, P., 2020.
    # 2019 standard scenarios report: a US electric sector outlook (No. NREL/PR-6A20-75798).
    # National Renewable Energy Lab.(NREL), Golden, CO (United States).

    techno_infos_dict_default = {'maturity': 0,
                                 'Opex_percentage': 0.12,
                                 # Fixed 1.9 and recurrent 0.5 %
                                 # Demystifying-the-Costs-of-Electricity-Generation-Technologies, average
                                 'WACC': 0.058,  # Weighted averaged cost of capital / ATB NREL 2020
                                 'learning_rate': 0.00,  # Cost development of low carbon energy technologies
                                 # Demystifying-the-Costs-of-Electricity-Generation-Technologies, average
                                 'Capex_init': 6000,
                                 'Capex_init_unit': '$/kW',
                                 'full_load_hours': 8760.0,  # Full year hours
                                 # Demystifying-the-Costs-of-Electricity-Generation-Technologies, average
                                 'capacity_factor': 0.90,
                                 'techno_evo_eff': 'no',
                                 'efficiency': 1.0,
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 # f"{GlossaryEnergy.CopperResource}_needs": 1100 /1e9, # No data found, therefore we make the assumption that it needs at least a generator which uses the same amount of copper as a gaz powered station. It needs 1100 kg / MW. Computing the need in Mt/MW #no data, assuming it needs at least enough copper for a generator (such as the gas_turbine)
                                 }

    techno_info_dict = techno_infos_dict_default
    # Initial production in TWh at year_start IAEA - IAEA_Energy Electricity
    # and Nuclear Power Estimates up to 2050
    initial_production = 6590.0
    # Invest in 2019 => 29.6 bn

    # Age distribution => IAEA OPEX Nuclear 2020 - Number of Reactors by Age
    # (as of 1 January 2020)
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               'data_fuel_dict': {'type': 'dict', 'default': data_fuel_dict_default},
                      }
    # -- add specific techno outputs to this
    DESC_IN.update(ElectricityTechnoDiscipline.DESC_IN)

    DESC_OUT = ElectricityTechnoDiscipline.DESC_OUT

    _maturity = 'Research'

    def init_execution(self):
        self.model = RenewableElectricitySimpleTechno(self.techno_name)

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
