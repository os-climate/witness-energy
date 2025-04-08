'''
Copyright 2022 Airbus SAS
Modifications on 2023/06/14-2024/03/27 Copyright 2023 Capgemini

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


from energy_models.core.stream_type.energy_models.wet_biomass import WetBiomass
from energy_models.core.techno_type.disciplines.biogas_techno_disc import (
    BiogasTechnoDiscipline,
)
from energy_models.glossaryenergy import GlossaryEnergy
from energy_models.models.biogas.anaerobic_digestion.anaerobic_digestion import (
    AnaerobicDigestion,
)


class AnaerobicDigestionDiscipline(BiogasTechnoDiscipline):
    # ontology information
    _ontology_data = {
        'label': 'Energy Biogas Anaerobic Digestion Model',
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
    # -- add specific techno inputs to this
    techno_name = GlossaryEnergy.AnaerobicDigestion

    techno_infos_dict_default = {'maturity': 3,
                                 'Opex_percentage': 0.85,
                                 'CO2_from_production': 0.0,
                                 'CO2_from_production_unit': 'kg/kg',
                                 # Rajendran, K., Gallachóir, B.ó. and Murphy, J.D., 2019.
                                 # The Role of Incentivising Biomethane in
                                 # Ireland Using Anaerobic Digestion.
                                 'elec_demand': 0.25,  # Mean of technos
                                 'elec_demand_unit': 'kWh/m^3',
                                 f"{WetBiomass.name}_needs": 2.0,  # Rakendran2019 in table 3
                                 'wet_biomass_needs_unit': 'kg/m^3',
                                 # McKendry P (2019)
                                 # Overview of Anaerobic Digestion and Power and Gas to Grid Plant CAPEX and OPEX Costs.
                                 # Int J Bioprocess Biotech 02: 109.
                                 # DOI:10.20911/IJBBT-109.100009
                                 # Source for CAPEX init: IEA 2022, Outlook for biogas and biomethane: Prospects for organic growth,
                                 # https://www.iea.org/reports/outlook-for-biogas-and-biomethane-prospects-for-organic-growth,
                                 # License: CC BY 4.0.
                                 # Capex 6.9 $/Mbtu from IEA medium digester
                                 # (Mbtu/kWh = 1/293)
                                 'Capex_init': 6.9 / 293.,
                                 'Capex_init_unit': '$/kWh',
                                 'learning_rate': 0.2,  # not found
                                 # move from medium to large digester to
                                 # decrease capex
                                 'maximum_learning_capex_ratio': 5.2 / 6.9,
                                 # Carlini, M., Mosconi, E.M., Castellucci, S., Villarini, M. and Colantoni, A., 2017.
                                 # An economical evaluation of anaerobic digestion plants fed with organic agro-industrial waste.
                                 # Energies, 10(8), p.1165.
                                 'efficiency': 0.4,
                                 'WACC': 0.06,
                                 'techno_evo_eff': 'no',
                                 }

    # Source for initial production: IEA 2022, Outlook for biogas and biomethane: Prospects for organic growth,
    # https://www.iea.org/reports/outlook-for-biogas-and-biomethane-prospects-for-organic-growth
    # License: CC BY 4.0.
    # in 17.7 GW with 8760 hours in a year  at year_start
    # 35 Mtoe in 2020 by IEA  Mtoe to TWh:
    initial_production = 35.0 * 11.63

    # Age distribution can be computed with
    # http://task37.ieabioenergy.com/plant-list.html
    # Source for initial production: IEA 2022, Outlook for biogas and biomethane: Prospects for organic growth,
    # https://www.iea.org/reports/outlook-for-biogas-and-biomethane-prospects-for-organic-growth
    # License: CC BY 4.0.
    DESC_IN = {'techno_infos_dict': {'type': 'dict',
                                     'default': techno_infos_dict_default, 'unit': 'defined in dict'},
               }
    DESC_IN.update(BiogasTechnoDiscipline.DESC_IN)

    # -- add specific techno outputs to this
    DESC_OUT = BiogasTechnoDiscipline.DESC_OUT

    def init_execution(self):
        inputs_dict = self.get_sosdisc_inputs()
        self.techno_model = AnaerobicDigestion(self.techno_name)
        self.techno_model.configure_parameters(inputs_dict)

    def compute_sos_jacobian(self):
        # Grad of price vs energyprice

        super().compute_sos_jacobian()

        grad_dict = self.techno_model.grad_price_vs_stream_price()
        carbon_emissions = self.get_sosdisc_outputs(GlossaryEnergy.CO2EmissionsValue)
        grad_dict_resources = self.techno_model.grad_price_vs_resources_price()

        self.set_partial_derivatives_techno(
            grad_dict, carbon_emissions, grad_dict_resources)
