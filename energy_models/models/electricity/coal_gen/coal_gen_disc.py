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

from energy_models.core.stream_type.energy_models.heat import hightemperatureheat
from energy_models.core.stream_type.energy_models.solid_fuel import SolidFuel
from energy_models.core.techno_type.disciplines.electricity_techno_disc import (
    ElectricityTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.electricity.coal_gen.coal_gen import CoalGen


class CoalGenDiscipline(ElectricityTechnoDiscipline):
    """**EnergyModelsDiscipline** is the :class:`~gems.core.discipline.MDODiscipline`
    implementing the computation of Energy Models outputs."""

    # ontology information
    _ontology_data = {
        'label': 'Coal Generation Model',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-industry fa-fw',
        'version': '',
    }
    techno_name = GlossaryEnergy.CoalGen

    # Source: Cui, R.Y., Hultman, N., Edwards, M.R., He, L., Sen, A., Surana, K., McJeon, H., Iyer, G., Patel, P., Yu, S. and Nace, T., 2019.
    # Quantifying operational lifetimes for coal power plants under the Paris
    # goals. Nature communications, 10(1), pp.1-9.
    techno_infos_dict_default = {'maturity': 0,
                                 'product': GlossaryEnergy.electricity,
                                 # Lorenczik, S., Kim, S., Wanner, B., Bermudez Menendez, J.M., Remme, U., Hasegawa,
                                 # T., Keppler, J.H., Mir, L., Sousa, G., Berthelemy, M. and Vaya Soler, A., 2020.
                                 # Projected Costs of Generating Electricity-2020 Edition (No. NEA--7531).
                                 # Organisation for Economic Co-Operation and Development.
                                 # U.S. Energy Information Association
                                 # Levelized Costs of New Generation Resources in the Annual Energy Outlook 2021
                                 # IEA 2022, World Energy Outlook 2014,
                                 # https://www.iea.org/reports/world-energy-outlook-2014
                                 # License: CC BY 4.0.
                                 'Opex_percentage': 0.0339,  # Mean of IEA World Energy Outlook 2014
                                 # Bruckner, T., Bashmakov, I.A., Mulugetta, Y., Chum, H., De la Vega Navarro, A., Edmonds,
                                 # J., Faaij, A., Fungtammasan, B., Garg, A., Hertwich, E. and Honnery, D., 2014.
                                 # Energy systems. IPCC
                                 # https://www.ipcc.ch/site/assets/uploads/2018/02/ipcc_wg3_ar5_chapter7.pdf
                                 # Or for a simplified chart:
                                 # https://www.world-nuclear.org/information-library/energy-and-the-environment/carbon-dioxide-emissions-from-electricity.aspx
                                 'CO2_from_production': 0.82,
                                 'CO2_from_production_unit': 'kg/kWh',
                                 # https://previous.iiasa.ac.at/web/home/research/researchPrograms/air/IR55-GAINS-N2O.pdf
                                 # 0.0014 kt/PJ
                                 'N2O_emission_factor': 0.0014e-3 / 0.277,
                                 'N2O_emission_factor_unit': 'Mt/TWh',
                                 # IEA 2022, Levelised Cost of Electricity Calculator,
                                 # https://www.iea.org/articles/levelised-cost-of-electricity-calculator
                                 # License: CC BY 4.0.
                                 'elec_demand': 0.16,
                                 'elec_demand_unit': 'kWh/kWh',
                                 # IEA 2022, Projected Costs of Generating Electricity 2015,
                                 # https://www.iea.org/reports/projected-costs-of-generating-electricity-2015
                                 # License: CC BY 4.0.
                                 'fuel_demand': 0.836,  # at 100% efficiency
                                 'fuel_demand_unit': 'kWh/kWh',
                                 # Renewable Power Generation Costs in 2020
                                 # IRENA, 2020
                                 # https://www.irena.org/publications/2021/Jun/Renewable-Power-Costs-in-2020
                                 'WACC': 0.075,
                                 # Rubin, E.S., Azevedo, I.M., Jaramillo, P. and Yeh, S., 2015.
                                 # A review of learning rates for electricity supply technologies.
                                 # Energy Policy, 86, pp.198-218.
                                 # https://www.cmu.edu/epp/iecm/rubin/PDF%20files/2015/A%20review%20of%20learning%20rates%20for%20electricity%20supply%20technologies.pdf
                                 'learning_rate': 0.083,
                                 # IEA 2022, World Energy Outlook 2014,
                                 # https://www.iea.org/reports/world-energy-outlook-2014
                                 # License: CC BY 4.0.
                                 'Capex_init': 1900,
                                 'Capex_init_unit': '$/kW',
                                 'full_load_hours': 8760,
                                 'water_demand': 2.22,
                                 'water_demand_unit': 'kg/kWh',
                                 # EIA, U., 2021. Electric Power Monthly,
                                 # Table 6.07.A. Capacity Factors for Utility Scale Generators Primarily Using Fossil Fuels
                                 # https://www.eia.gov/electricity/monthly/epm_table_grapher.php?t=epmt_6_07_a
                                 'capacity_factor': 0.405,  # Average value in the US in 2020
                                 'transport_cost_unit': '$/kg',  # check if pertinent
                                 'techno_evo_eff': 'yes',
                                 'techno_evo_time': 10,
                                 # efficiency computed to match IEA datas
                                 'efficiency': 0.41,
                                 'efficiency_max': 0.48,
                                 'efficiency evolution slope': 0.5,
                                 f"{GlossaryEnergy.CopperResource}_needs": 1150 /1e9 #According to the IEA, Coal powered stations need 1150 kg of copper for each MW implemented. Computing the need in Mt/MW.,
                                 # IEA Executive summary - Role of critical minerals in clean energy transitions 2022
                                 }

    techno_info_dict = techno_infos_dict_default
    # Source for initial production and initial invest:
    # IEA 2022, Coal 2019, https://www.iea.org/reports/coal-2019,
    # License: CC BY 4.0.
    initial_production = 9914.45  # in TWh at year_start
    # Invest before year start in $
    
    FLUE_GAS_RATIO = np.array([0.13])
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
                      }
    # -- add specific techno outputs to this
    DESC_IN.update(ElectricityTechnoDiscipline.DESC_IN)

    _maturity = 'Research'

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = CoalGen(self.techno_name)
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
            f'{SolidFuel.name} ({self.techno_model.product_unit})']
        # self.techno_consumption_derivative[f'{SolidFuel.name} ({self.product_unit})']
        self.set_partial_derivative_for_other_types(
            (GlossaryEnergy.TechnoProductionValue,
             f'{hightemperatureheat.name} ({self.techno_model.product_unit})'),
            (GlossaryEnergy.InvestLevelValue, GlossaryEnergy.InvestValue),
            (consumption_gradient - dprod_name_dinvest))
