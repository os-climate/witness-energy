'''
Copyright 2022 Airbus SAS
Modifications on 2023/10/23-2023/11/16 Copyright 2023 Capgemini

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
import pandas as pd

from energy_models.core.stream_type.base_stream import BaseStream
from energy_models.glossaryenergy import GlossaryEnergy


class CarbonCapture(BaseStream):
    name = GlossaryEnergy.carbon_capture
    flue_gas_name = GlossaryEnergy.CO2FromFlueGas
    unit = 'Mt'
    default_techno_list = [f'{GlossaryEnergy.direct_air_capture}.{GlossaryEnergy.AmineScrubbing}', f'{GlossaryEnergy.direct_air_capture}.{GlossaryEnergy.CalciumPotassiumScrubbing}',
                           f'{GlossaryEnergy.direct_air_capture}.{GlossaryEnergy.DirectAirCaptureTechno}',
                           f'{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.CalciumLooping}', f'{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.ChilledAmmoniaProcess}',
                           f'{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.CO2Membranes}', f'{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.MonoEthanolAmine}',
                           f'{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.PiperazineProcess}', f'{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.PressureSwingAdsorption}',
                           f'{GlossaryEnergy.flue_gas_capture}.{GlossaryEnergy.FlueGasTechno}']
    # Data dict from CO2 dioxyde
    data_energy_dict = {'maturity': 5,
                        'density': 1.98,
                        'density_unit': 'kg/m^3',
                        'molar_mass': 44.01,
                        'molar_mass_unit': 'g/mol',
                        # Calorific values set to 1.0 for the calculation of transport cost (in $/kWh)
                        # Since it is not used as an energy source
                        'calorific_value': 1.0,
                        'calorific_value_unit': 'kWh/kg',
                        'high_calorific_value': 1.0,
                        'high_calorific_value_unit': 'kWh/kg'}

    def __init__(self, name):
        BaseStream.__init__(self, name)

        self.consumption_woratio = None
        self.carbon_captured_type_woratio = None
        self.flue_gas_percentage_woratio = None
        self.fg_ratio_woratio = None
        self.production = None
        self.consumption = None
        self.production_by_techno = None
        self.flue_gas_percentage = None
        self.carbon_captured_type = None
        self.flue_gas_production = None
        self.flue_gas_prod_ratio = None
        self.fg_ratio = None

    def configure_parameters_update(self, inputs_dict):
        self.subelements_list = inputs_dict[GlossaryEnergy.techno_list]
        BaseStream.configure_parameters_update(self, inputs_dict)
        self.flue_gas_production = inputs_dict['flue_gas_production'][self.flue_gas_name].values
        self.flue_gas_prod_ratio = inputs_dict['flue_gas_prod_ratio']

    def compute(self, inputs, exp_min=True):
        '''
        Specific compute to handle the number of values in the return out of compute_production
        '''

        _, self.consumption_woratio, _, self.carbon_captured_type_woratio, self.flue_gas_percentage_woratio, self.fg_ratio_woratio = self.compute_production(
            self.sub_production_dict, self.sub_consumption_woratio_dict)

        self.production, self.consumption, self.production_by_techno, self.carbon_captured_type, self.flue_gas_percentage, self.fg_ratio = self.compute_production(
            self.sub_production_dict, self.sub_consumption_dict)

        self.compute_price(exp_min=exp_min)

        self.aggregate_land_use_required()

        self.compute_energy_type_capital(inputs)

        return self.total_prices, self.production, self.consumption, self.consumption_woratio, self.mix_weights

    def compute_production(self, sub_production_dict, sub_consumption_dict):
        '''
        Specific compute energy production where we compute carbon captured from flue gas 
        '''

        # Initialize dataframe out
        base_df = pd.DataFrame({GlossaryEnergy.Years: self.years})
        production = base_df.copy(deep=True)
        consumption = base_df.copy(deep=True)
        production_by_techno = base_df.copy(deep=True)
        carbon_captured_type = pd.DataFrame({GlossaryEnergy.Years: self.years,
                                             'flue gas': 0.0,
                                             'DAC': 0.0,
                                             'flue_gas_limited': 0.0})
        flue_gas_percentage = None
        fg_ratio = None

        production[f'{self.name}'] = 0.
        for element in self.subelements_list:
            production_by_techno[f'{self.name} {element} ({self.unit})'] = sub_production_dict[
                element][f'{self.name} ({self.unit})'].values
            production[
                f'{self.name}'] += production_by_techno[f'{self.name} {element} ({self.unit})'].values

            if element.startswith('flue_gas_capture'):
                carbon_captured_type['flue gas'] += production_by_techno[
                    f'{self.name} {element} ({self.unit})'].values
            else:
                carbon_captured_type['DAC'] += production_by_techno[
                    f'{self.name} {element} ({self.unit})'].values

        diff_flue_gas = self.flue_gas_production - \
                        carbon_captured_type['flue gas'].values

        # Means that we capture more flue gas than available
        if min(diff_flue_gas.real) < 0:
            if carbon_captured_type['flue gas'].values.dtype != self.flue_gas_production.dtype:
                self.flue_gas_production = self.flue_gas_production.astype(
                    carbon_captured_type['flue gas'].values.dtype)
            fg_ratio = np.divide(
                self.flue_gas_production, carbon_captured_type['flue gas'].values,
                where=carbon_captured_type['flue gas'].values != 0.0, out=np.zeros_like(self.flue_gas_production))
            flue_gas_percentage = self.compute_flue_gas_with_exp_min(
                fg_ratio)
            carbon_captured_type['flue gas limited'] = carbon_captured_type['flue gas'] * \
                                                       flue_gas_percentage
            production[f'{self.name}'] = carbon_captured_type['flue gas limited'] + \
                                         carbon_captured_type['DAC']

        else:
            carbon_captured_type['flue gas limited'] = carbon_captured_type['flue gas']

        # Divide the prod or the cons  if element is carbon capture
        for element in self.subelements_list:
            if element.startswith('flue_gas_capture') and min(diff_flue_gas.real) < 0:
                factor = flue_gas_percentage
            else:
                factor = 1.0
            production_by_techno[f'{self.name} {element} ({self.unit})'] = sub_production_dict[
                                                                               element][
                                                                               f'{self.name} ({self.unit})'].values * factor
            production, consumption = self.compute_byproducts_consumption_and_production(
                element, sub_production_dict, sub_consumption_dict, production, consumption, factor=factor)
        return production, consumption, production_by_techno, carbon_captured_type, flue_gas_percentage, fg_ratio

    def compute_flue_gas_with_exp_min(self, fg_perc):

        f = 1.0 - fg_perc
        min_prod = 0.001
        f[f < np.log(1e-30) * min_prod] = np.log(1e-30) * min_prod

        f_limited = np.maximum(min_prod / 10.0 * (9.0 + np.exp(np.minimum(f, min_prod) / min_prod)
                                                  * np.exp(-1)), f)
        return 1.0 - f_limited

    def compute_dflue_gas_with_exp_min(self, fg_ratio):

        f = 1.0 - fg_ratio
        min_prod = 0.001
        dflue_gas = np.ones(len(fg_ratio))
        if f.min() < min_prod:
            f[f < np.log(1e-30) * min_prod] = np.log(1e-30) * min_prod
            dflue_gas[f < min_prod] = np.exp(
                f[f < min_prod] / min_prod) * np.exp(-1) / 10.0
        return dflue_gas

    def aggregate_land_use_required(self):
        '''
        Aggregate into an unique dataframe of information of sub technology about land use required
        '''

        for element in self.sub_land_use_required_dict.values():

            element_columns = list(element)
            element_columns.remove(GlossaryEnergy.Years)

            for column_df in element_columns:
                if column_df.startswith('flue_gas_capture') and self.flue_gas_percentage is not None:
                    self.land_use_required[column_df] = element[column_df] * \
                                                        self.flue_gas_percentage
                else:
                    self.land_use_required[column_df] = element[column_df]
