'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/10-2024/06/24 Copyright 2023 Capgemini

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
from energy_models.models.electricity.solar_thermal.solar_thermal import SolarThermal


class SolarThermalDiscipline(ElectricityTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    # mean values for plant with 8 hours storage

    # ontology information
    _ontology_data = {
        'label': 'Solar Thermal Energy Model',
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
    techno_name = GlossaryEnergy.SolarThermal

    techno_infos_dict_default = {'maturity': 0,
                                 'product': GlossaryEnergy.electricity,
                                 # OPEX : lmean of lazard / JRC / ATB NREL
                                 'Opex_percentage': 0.015,
                                 # WACC : mean of Frauhofer / IRENA / ATB NREL
                                 'WACC': 0.062,
                                 'learning_rate': 0.07,  # JRC
                                 # Capex : mean of JRC / IRENA /ATB NREL / ...
                                 'Capex_init': 5000,
                                 'Capex_init_unit': '$/kW',
                                 'techno_evo_eff': 'no',
                                 'efficiency': 0.25,
                                 # considered average   # https://www.volker-quaschning.de/articles/fundamentals2/index.php#:~:text=The%20efficiency%20of%20a%20solar,losses%20are%20usually%20below%2010%25.
                                 'full_load_hours': 8760,  # max value
                                 # capacity factor actual mean JRC / ATC NREL
                                 # and reverse calculation from IRENA values
                                 # (6.3 GW and 15.6 TWh)
                                 'capacity_factor': 0.4,
                                 'capacity_factor_at_year_end': 0.50,  # value IRENA / ATB NREL
                                 'density_per_ha': 346564.9,  # 10% less space than solar pv
                                 'density_per_ha_unit': 'kWh/ha',
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 f"{GlossaryEnergy.CopperResource}_needs": 1100 / 1e9,  # No data found, therefore we make the assumption that it needs at least a generator which uses the same amount of copper as a gaz powered station. It needs 1100 kg / MW. Computing the need in Mt/MW
                                 # no data, assuming it needs at least enough copper for a generator (such as the gas_turbine)
                                 }

    techno_info_dict = techno_infos_dict_default
    initial_production = 15.6  # in TWh at year_start (IEA)
    # Invest before year start
    # from
    # https://www.irena.org/Statistics/View-Data-by-Topic/Finance-and-Investment/Investment-Trends

    # from database https://solarpaces.nrel.gov/
    # Nb plants 'Operational' and not pilot/demo/proto
    # only commercial or production
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
                      }
    # -- add specific techno outputs to this
    DESC_IN.update(ElectricityTechnoDiscipline.DESC_IN)

    DESC_OUT = ElectricityTechnoDiscipline.DESC_OUT

    _maturity = 'Research'

    def init_execution(self):
        self.model = SolarThermal(self.techno_name)

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
