'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/19-2024/06/24 Copyright 2023 Capgemini

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
from energy_models.models.electricity.solar_pv.solar_pv import SolarPv


class SolarPvDiscipline(ElectricityTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    # ontology information
    _ontology_data = {
        'label': 'Solar Photovoltaic Energy Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-solar-panel fa-fw',
        'version': '',
    }
    techno_name = GlossaryEnergy.SolarPv

    # Source for Opex percentage, Capex init, capacity factor:
    # IEA 2022, World Energy Outlook 2019,
    # https://www.iea.org/reports/world-energy-outlook-2019, License: CC BY
    # 4.0.
    techno_infos_dict_default = {'maturity': 0,
                                 'product': GlossaryEnergy.electricity,
                                 'Opex_percentage': 0.021,  # Mean of IEA 2019, EOLES data and others
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 'fuel_demand': 0.0,
                                 'fuel_demand_unit': 'kWh/kWh',
                                 'elec_demand': 0.0,
                                 'elec_demand_unit': 'kWh/kWh',
                                 'heat_demand': 0.0,
                                 'heat_demand_unit': 'kWh/kgCO2',
                                 'WACC': 0.075,  # Weighted averaged cost of capital. Source IRENA
                                 'learning_rate': 0.18,  # IEA 2011
                                 'Capex_init': 1077,  # IEA 2019 Mean of regional value
                                 'Capex_init_unit': '$/kW',
                                 'efficiency': 1.0,  # No need of efficiency here
                                 'full_load_hours': 8760,  # 1577, #Source Audi ?
                                 'water_demand': 0.0,
                                 'water_demand_unit': '',
                                 # IEA Average annual capacity factors by
                                 # technology, 2018 10-21%, IRENA 2019: 18%
                                 'capacity_factor': 0.2,
                                 'density_per_ha': 315059,
                                 'density_per_ha_unit': 'kWh/ha',
                                 'transport_cost_unit': '$/kg',  # check if pertient
                                 'techno_evo_eff': 'no',
                                 GlossaryEnergy.EnergyEfficiency: 1.0,
                                 f"{GlossaryEnergy.CopperResource}_needs": 2822 / 1e9  # According to the IEA, Solar PV panels need 2822 kg of copper for each MW implemented. Computing the need in Mt/MW,
                                 # IEA Executive summary - Role of critical minerals in clean energy transitions 2022
                                 }

    techno_info_dict = techno_infos_dict_default
    initial_production = 700  # in TWh at year_start source IEA 2019
    # Invest before year start in $ source IEA 2019

    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
                      }
    # -- add specific techno outputs to this
    DESC_IN.update(ElectricityTechnoDiscipline.DESC_IN)

    DESC_OUT = ElectricityTechnoDiscipline.DESC_OUT

    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = SolarPv(self.techno_name)
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
