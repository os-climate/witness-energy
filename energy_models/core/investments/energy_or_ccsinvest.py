'''
Copyright 2022 Airbus SAS
Modifications on 2023/09/07-2023/11/03 Copyright 2023 Capgemini

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

import pandas as pd

from climateeconomics.glossarycore import GlossaryCore


class EnergyOrCCSInvest():
    '''
        Model to split global investment into investment for Carbon Capture and Storage technologies and into investment for energy conversion 
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.invest_mix = None
        self.global_invest = None
        self.invest_ccs_percentage = None
        self.invest_ccs = None
        self.invest_energy_conversion = None

    def configure(self, input_dict):
        '''
        COnfigure global invest and invest_ccs percentage
        '''
        self.global_invest = input_dict[GlossaryCore.EnergyInvestmentsValue]
        self.invest_ccs_percentage = input_dict['ccs_percentage']

    def compute(self):
        '''
        Compute the investment in to CCS and into energy_conversion 
        '''
        ccs_invest = self.global_invest[GlossaryCore.EnergyInvestmentsValue].values * \
            self.invest_ccs_percentage['ccs_percentage'].values / 100.0

        energy_conversion_invest = self.global_invest[GlossaryCore.EnergyInvestmentsValue].values - ccs_invest
        self.invest_ccs = pd.DataFrame({GlossaryCore.Years: self.global_invest[GlossaryCore.Years].values,
                                        GlossaryCore.EnergyInvestmentsValue: ccs_invest})
        self.invest_energy_conversion = pd.DataFrame({GlossaryCore.Years: self.global_invest[GlossaryCore.Years].values,
                                                      GlossaryCore.EnergyInvestmentsValue: energy_conversion_invest})

    def get_ccs_investment(self, rescaling_factor):
        '''
        Rescale the investment with a given rescaling factor
        '''
        self.invest_ccs[GlossaryCore.EnergyInvestmentsValue] *= rescaling_factor
        return self.invest_ccs

    def get_energy_conversion_investment(self):
        '''
        Getter
        '''
        return self.invest_energy_conversion
