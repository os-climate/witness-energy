import numpy as np

from energy_models.core.stream_type.energy_models.electricity import Electricity
from energy_models.core.techno_type.base_techno_models.carbon_capture_techno import CCTechno
from energy_models.glossaryenergy import GlossaryEnergy


class GenericFlueGasTechnoModel(CCTechno):
    def __init__(self, name):
        super().__init__(name)
        self.flue_gas_ratio = None
        self.fg_ratio_effect = None

    def configure_parameters_update(self, inputs_dict):

        CCTechno.configure_parameters_update(self, inputs_dict)
        self.flue_gas_ratio = inputs_dict[GlossaryEnergy.FlueGasMean].loc[
            inputs_dict[GlossaryEnergy.FlueGasMean][GlossaryEnergy.Years]
            <= self.year_end]
        # To deal quickly with l0 test
        if 'fg_ratio_effect' in inputs_dict:
            self.fg_ratio_effect = inputs_dict['fg_ratio_effect']
        else:
            self.fg_ratio_effect = True

    def compute_other_energies_needs(self):
        self.cost_details[f'{GlossaryEnergy.electricity}_needs'] = self.get_electricity_needs() / self.cost_details['efficiency']

    def grad_price_vs_energy_price(self):
        '''
        Compute the gradient of global price vs energy prices
        Work also for total CO2_emissions vs energy CO2 emissions
        '''
        elec_needs = self.get_electricity_needs()

        return {Electricity.name: np.identity(len(self.years)) * elec_needs / self.techno_infos_dict[
            'efficiency'] * self.compute_electricity_variation_from_fg_ratio(
            self.flue_gas_ratio[GlossaryEnergy.FlueGasMean].values, self.fg_ratio_effect)
                }

    def compute_capex(self, invest_list, data_config):
        capex_calc_list = super().compute_capex(invest_list, data_config)
        capex_calc_list *= self.compute_capex_variation_from_fg_ratio(
            self.flue_gas_ratio[GlossaryEnergy.FlueGasMean].values, self.fg_ratio_effect)

        return capex_calc_list

    def compute_cost_of_other_energies_usage(self):
        self.cost_details[Electricity.name] = list(self.energy_prices[Electricity.name] * self.cost_details[f'{GlossaryEnergy.electricity}_needs'])

        self.cost_details[Electricity.name] *= self.compute_electricity_variation_from_fg_ratio(
            self.flue_gas_ratio[GlossaryEnergy.FlueGasMean].values, self.fg_ratio_effect)

    def compute_consumption_and_production(self):
        """
        Compute the consumption and the production of the technology for a given investment
        """

        # Consumption
        self.consumption_detailed[f'{Electricity.name} ({self.energy_unit})'] = self.cost_details[f'{GlossaryEnergy.electricity}_needs'] * \
                                                                                self.production_detailed[
                                                                                    f'{CCTechno.energy_name} ({self.product_energy_unit})']

