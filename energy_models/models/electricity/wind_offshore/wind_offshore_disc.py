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
from copy import deepcopy

from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import (
    InstanciatedSeries,
    TwoAxesInstanciatedChart,
)

from energy_models.core.techno_type.disciplines.electricity_techno_disc import (
    ElectricityTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.electricity.wind_offshore.wind_offshore import WindOffshore


class WindOffshoreDiscipline(ElectricityTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    # ontology information
    _ontology_data = {
        'label': 'Offshore Wind Energy Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-fan fa-fw',
        'version': '',
    }
    techno_name = GlossaryEnergy.WindOffshore

    techno_infos_dict_default = {'maturity': 0,
                                 'Opex_percentage': 0.022,  # ATB NREL 2020, average value
                                 'WACC': 0.052,  # Weighted averaged cost of capital / ATB NREL 2020
                                 'learning_rate': 0.07,  # Cost development of low carbon energy technologies
                                 'Capex_init': 4353,  # Irena Future of wind 2019
                                 'Capex_init_unit': '$/kW',
                                 'full_load_hours': 8760.0,  # Full year hours
                                 'capacity_factor': 0.43,  # Irena Future of wind 2019
                                 'capacity_factor_at_year_end': 0.54,  # Irena Future of wind 2019
                                 'techno_evo_eff': 'no',
                                 'efficiency': 1.0,
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 f"{GlossaryEnergy.CopperResource}_needs": 8000 / 1e9  # According to the IEA, WindOffshore panels needs 8000 kg of copper for each MW implemented. Computing the need in Mt/MW,
                                 # IEA Executive summary - Role of critical minerals in clean energy transitions 2022
                                 }

    techno_info_dict = techno_infos_dict_default
    # Initial production in TWh at year_start, 28.9 GW / GWEC
    # Annual-Wind-Report_2019_digital_final_2r
    # initial_production = 0.0289 * techno_infos_dict_default['full_load_hours'] * \
    #     techno_infos_dict_default['capacity_factor']
    initial_production = 89  # IEA in 2019
    # Invest in 2019 => 29.6 bn
    
    # Age distribution => GWEC Annual-Wind-Report_2019_digital_final_2r
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
                      }
    # -- add specific techno outputs to this
    DESC_IN.update(ElectricityTechnoDiscipline.DESC_IN)
    # Add specific transport cost for Offshore technology
    DESC_IN = deepcopy(DESC_IN)
    DESC_IN[GlossaryEnergy.TransportCostValue]['visibility'] = ElectricityTechnoDiscipline.LOCAL_VISIBILITY

    DESC_OUT = ElectricityTechnoDiscipline.DESC_OUT

    _maturity = 'Research'

    def init_execution(self):
        self.techno_model = WindOffshore(self.techno_name)

    def get_charts_consumption_and_production(self):
        "Adds the chart specific for resources needed for construction"
        instanciated_chart = super().get_charts_consumption_and_production()
        techno_consumption = self.get_sosdisc_outputs(GlossaryEnergy.TechnoConsumptionValue)

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
