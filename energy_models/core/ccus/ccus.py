'''
Copyright 2022 Airbus SAS
Modifications on 2023/11/07-2023/11/09 Copyright 2023 Capgemini

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

import autograd.numpy as np
import pandas as pd
from autograd import jacobian

from energy_models.core.stream_type.carbon_models.carbon import Carbon
from energy_models.core.stream_type.carbon_models.carbon_capture import CarbonCapture
from energy_models.glossaryenergy import GlossaryEnergy


class CCUS:
    """
    Class CCUS
    """
    name = GlossaryEnergy.ccus_type
    PRODUCTION = 'production'
    DELTA_ENERGY_PRICES = 'delta_energy_prices'
    DELTA_CO2_EMISSIONS = 'delta_co2_emissions'
    TOTAL_PRODUCTION = 'Total production'
    RESOURCE_LIST = ['natural_gas_resource',
                     'uranium_resource', 'coal_resource', 'oil_resource']

    resource_list = RESOURCE_LIST
    CO2_list = [f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit})',
                f'{CarbonCapture.flue_gas_name} ({GlossaryEnergy.mass_unit})',
                f'{GlossaryEnergy.carbon_storage} ({GlossaryEnergy.mass_unit})',
                f'{Carbon.name} ({GlossaryEnergy.mass_unit})']
    ccs_list = [GlossaryEnergy.carbon_capture, GlossaryEnergy.carbon_storage]

    def __init__(self, name):
        '''
        Constructor 
        '''
        self.year_start = None
        self.year_end = None
        self.years = None
        self.co2_for_food = None
        self.scaling_factor_energy_production = None
        self.scaling_factor_energy_consumption = None

        self.inputs_dict = {}
        self.outputs_dict = {}

    def configure_parameters(self, inputs_dict):
        '''
        COnfigure parameters (variables that does not change during the run
        '''
        self.inputs_dict = inputs_dict
        self.year_start = inputs_dict[GlossaryEnergy.YearStart]
        self.year_end = inputs_dict[GlossaryEnergy.YearEnd]
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.scaling_factor_energy_production = inputs_dict['scaling_factor_energy_production']
        self.scaling_factor_energy_consumption = inputs_dict['scaling_factor_energy_consumption']
        self.co2_for_food = pd.DataFrame({GlossaryEnergy.Years: self.years, f'{GlossaryEnergy.carbon_capture} for food (Mt)': 0.0})
        self.ccs_list = [GlossaryEnergy.carbon_capture, GlossaryEnergy.carbon_storage]

    def compute_carbon_storage_capacity(self):
        total_carbon_storage_by_invest = self.inputs_dict[f"{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.EnergyProductionValue}"][ GlossaryEnergy.carbon_storage].values * self.scaling_factor_energy_production

        self.outputs_dict['carbon_storage_capacity'] = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            'carbon_storage_capacity': total_carbon_storage_by_invest
        })

    def compute_co2_emissions(self):
        self.compute_carbon_storage_capacity()

        carbon_capture_from_energy_mix = self.inputs_dict['carbon_capture_from_energy_mix'][f'{GlossaryEnergy.carbon_capture} from energy mix (Gt)'].values
        co2_emissions_needed_by_energy_mix = self.inputs_dict['co2_emissions_needed_by_energy_mix'][f'{GlossaryEnergy.carbon_capture} needed by energy mix (Gt)'].values
        co2_for_food = self.co2_for_food[f'{GlossaryEnergy.carbon_capture} for food (Mt)'].values

        carbon_capture_prod = self.inputs_dict[f"{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.EnergyProductionValue}"][GlossaryEnergy.carbon_capture].values
        carbon_storage_prod = self.inputs_dict[f"{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.EnergyProductionValue}"][GlossaryEnergy.carbon_storage].values

        carbon_capture_to_be_stored, carbon_storage_limited_by_capture_gt, carbon_storage, carbon_capture_from_cc_technos = compute_carbon_storage_limited_by_capture_gt(
            carbon_capture_prod=carbon_capture_prod,
            carbon_storage_prod=carbon_storage_prod,
            carbon_capture_from_energy_mix=carbon_capture_from_energy_mix,
            co2_emissions_needed_by_energy_mix=co2_emissions_needed_by_energy_mix,
            co2_for_food=co2_for_food,
            scaling_factor_energy_production=self.scaling_factor_energy_production
        )

        self.outputs_dict['co2_emissions_ccus'] = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            f'{GlossaryEnergy.carbon_storage} ({GlossaryEnergy.mass_unit})': carbon_storage,
            f'{GlossaryEnergy.carbon_capture} to be stored (Mt)': carbon_capture_to_be_stored,
            f'{GlossaryEnergy.carbon_capture} ({GlossaryEnergy.mass_unit}) from CC technos': carbon_capture_from_cc_technos,
            f'{GlossaryEnergy.carbon_storage} Limited by capture (Mt)': carbon_storage_limited_by_capture_gt / 1e3,
        })

        self.outputs_dict['co2_emissions_ccus_Gt'] = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            f'{GlossaryEnergy.carbon_storage} Limited by capture (Gt)': carbon_storage_limited_by_capture_gt
        })

    def compute(self):
        self.compute_co2_emissions()
        self.compute_CCS_price()

    def compute_CCS_price(self):
        '''
        Compute CCS_price 
        '''
        ccs_price = self.inputs_dict[f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.StreamPricesValue}'][GlossaryEnergy.carbon_capture].values +\
                                               self.inputs_dict[f'{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.StreamPricesValue}'][GlossaryEnergy.carbon_storage].values
        self.outputs_dict['CCS_price'] = pd.DataFrame({
            GlossaryEnergy.Years: self.years,
            'ccs_price_per_tCO2': ccs_price
        })

    def grad_co2_emissions_ccus_Gt(self):
        carbon_capture_from_energy_mix = self.inputs_dict['carbon_capture_from_energy_mix'][f'{GlossaryEnergy.carbon_capture} from energy mix (Gt)'].values
        co2_emissions_needed_by_energy_mix = self.inputs_dict['co2_emissions_needed_by_energy_mix'][f'{GlossaryEnergy.carbon_capture} needed by energy mix (Gt)'].values
        co2_for_food = self.co2_for_food[f'{GlossaryEnergy.carbon_capture} for food (Mt)'].values

        carbon_capture_prod = self.inputs_dict[f"{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.EnergyProductionValue}"][GlossaryEnergy.carbon_capture].values
        carbon_storage_prod = self.inputs_dict[f"{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.EnergyProductionValue}"][GlossaryEnergy.carbon_storage].values

        jac_carbon_capture_from_cc_prod, jac_carbon_capture_from_cs_prod, jac_carbon_capture_from_energy_mix, jac_co2_emissions_needed_by_energy_mix =\
            compute_carbon_storage_limited_by_capture_gt_der(
            carbon_capture_prod=carbon_capture_prod,
            carbon_storage_prod=carbon_storage_prod,
            carbon_capture_from_energy_mix=carbon_capture_from_energy_mix,
            co2_emissions_needed_by_energy_mix=co2_emissions_needed_by_energy_mix,
            co2_for_food=co2_for_food,
            scaling_factor_energy_production=self.scaling_factor_energy_production
        )
        # input_name : (column_name, grad value)
        out = {
            'carbon_capture_from_energy_mix': [(f'{GlossaryEnergy.carbon_capture} from energy mix (Gt)', jac_carbon_capture_from_energy_mix)],
            'co2_emissions_needed_by_energy_mix': [(f'{GlossaryEnergy.carbon_capture} needed by energy mix (Gt)', jac_co2_emissions_needed_by_energy_mix)],
            f'{GlossaryEnergy.carbon_storage}.{GlossaryEnergy.EnergyProductionValue}': [(GlossaryEnergy.carbon_storage, jac_carbon_capture_from_cs_prod)],
            f'{GlossaryEnergy.carbon_capture}.{GlossaryEnergy.EnergyProductionValue}': [(GlossaryEnergy.carbon_capture, jac_carbon_capture_from_cc_prod)]
        }

        return out


def compute_carbon_storage_limited_by_capture_gt(
        carbon_capture_prod: np.ndarray,
        carbon_storage_prod: np.ndarray,
        carbon_capture_from_energy_mix: np.ndarray,
        co2_emissions_needed_by_energy_mix: np.ndarray,
        co2_for_food: np.ndarray,
        scaling_factor_energy_production: float
        ):
    '''The carbon stored by invest is limited by the carbon to stored'''

    carbon_storage = carbon_storage_prod * scaling_factor_energy_production
    carbon_capture_from_cc_technos = carbon_capture_prod * scaling_factor_energy_production

    carbon_capture_to_be_stored = (
            carbon_capture_from_cc_technos +
            carbon_capture_from_energy_mix * 1e3 -
            co2_emissions_needed_by_energy_mix * 1e3 -
            co2_for_food
    )

    carbon_storage_limited_by_capture_mt = np.minimum(carbon_capture_to_be_stored, carbon_storage)
    return carbon_capture_to_be_stored, carbon_storage_limited_by_capture_mt / 1e3, carbon_storage, carbon_capture_from_cc_technos


def compute_carbon_storage_limited_by_capture_gt_der(
        carbon_capture_prod: np.ndarray,
        carbon_storage_prod: np.ndarray,
        carbon_capture_from_energy_mix: np.ndarray,
        co2_emissions_needed_by_energy_mix: np.ndarray,
        co2_for_food: np.ndarray,
        scaling_factor_energy_production: float
        ):
    args = (carbon_capture_prod,
            carbon_storage_prod,
            carbon_capture_from_energy_mix,
            co2_emissions_needed_by_energy_mix,
            co2_for_food,
            scaling_factor_energy_production,)

    jac_carbon_capture_from_cc_prod = jacobian(lambda *args: compute_carbon_storage_limited_by_capture_gt(*args)[1], 0)
    jac_carbon_capture_from_cs_prod = jacobian(lambda *args: compute_carbon_storage_limited_by_capture_gt(*args)[1], 1)
    jac_carbon_capture_from_energy_mix = jacobian(lambda *args: compute_carbon_storage_limited_by_capture_gt(*args)[1], 2)
    jac_co2_emissions_needed_by_energy_mix = jacobian(lambda *args: compute_carbon_storage_limited_by_capture_gt(*args)[1], 3)

    return jac_carbon_capture_from_cc_prod(*args), jac_carbon_capture_from_cs_prod(*args), jac_carbon_capture_from_energy_mix(*args), jac_co2_emissions_needed_by_energy_mix(*args)