'''
Copyright 2023 Capgemini

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
from math import isclose

import pandas as pd

from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.glossaryenergy import GlossaryEnergy


class InvestmentsRedistribution():
    '''
        Model to distribute investments based on percentage of GDP to technologies
    '''

    def __init__(self):
        '''
        Constructor
        '''
        # initialize variables
        self.years = None
        self.energy_investment_wo_tax = None
        self.percentage_gdp_energy_invest = None
        self.techno_invest_percentage_df = None
        self.economics_df = None
        self.investment_per_technology_dict = None
        self.energy_list = None
        self.ccs_list = None
        self.techno_list_dict = None
        self.total_investments_in_energy = None
        self.total_investments_in_energy_w_biomass_dry = None
        self.forest_investment_df = None
        self.inputs_dict = None

    def configure_parameters(self, inputs_dict: dict):
        """
        Configure parameters that will be used in the model
        """
        # get all necessary data from inputs_dict
        self.inputs_dict = inputs_dict
        self.percentage_gdp_energy_invest = self.inputs_dict[GlossaryEnergy.EnergyInvestPercentageGDPName]
        self.techno_invest_percentage_df = self.inputs_dict[GlossaryEnergy.TechnoInvestPercentageName]
        self.economics_df = self.inputs_dict[GlossaryEnergy.EconomicsDfValue]
        self.energy_list = self.inputs_dict[GlossaryEnergy.EnergyListName]
        self.ccs_list = self.inputs_dict[GlossaryEnergy.CCSListName]
        self.techno_list_dict = {energy: self.inputs_dict[f'{energy}.{GlossaryEnergy.TechnoListName}'] for energy in
                                 self.energy_list + self.ccs_list if energy != BiomassDry.name}
        self.forest_investment_df = self.inputs_dict[GlossaryEnergy.ForestInvestmentValue]

    def compute(self):
        """compute investment per technology and total energy investments"""
        self.compute_investment_per_technology()
        self.compute_total_energy_investment_wo_tax()

    def compute_total_energy_investment_wo_tax(self):
        """computes investments in the energy sector (without tax)"""

        # compute sum of all investments (energy investments + forest investments + biomass_dry investments
        # if used in model )
        self.total_investments_in_energy_w_biomass_dry = (self.total_investments_in_energy +
                                                          self.forest_investment_df[
                                                              GlossaryEnergy.ForestInvestmentValue].values)

        if BiomassDry.name in self.energy_list:
            for techno in ['managed_wood_investment', 'deforestation_investment', 'crop_investment']:
                self.total_investments_in_energy_w_biomass_dry += self.inputs_dict[techno][
                    GlossaryEnergy.InvestmentsValue].values
        self.energy_investment_wo_tax = pd.DataFrame(
            {GlossaryEnergy.Years: self.years.reset_index(drop=True),
             GlossaryEnergy.EnergyInvestmentsWoTaxValue: self.total_investments_in_energy_w_biomass_dry / 1e3})  # G$ to T$

    def compute_investment_per_technology(self):
        """
        Compute investment per energy technology based on percentage of GDP and input percentages
        """
        # compute part of gdp that is used for investment in energy
        self.total_investments_in_energy = (
                    self.economics_df[GlossaryEnergy.OutputNetOfDamage].values * 1e3 *  # T$ to G$
                    self.percentage_gdp_energy_invest[
                        GlossaryEnergy.EnergyInvestPercentageGDPName] / 100.)
        self.years = self.economics_df[GlossaryEnergy.Years]
        investments_dict = {}
        for energy, techno_list in self.techno_list_dict.items():
            # biomassdry technologies does not come in percentages
            if energy != BiomassDry.name:
                for techno in techno_list:
                    # investment in technology is total invest in energy * techno percentage
                    investments_dict[f'{energy}.{techno}'] = (self.total_investments_in_energy *
                                                              self.techno_invest_percentage_df[techno].values) / 100.

        # create dictionnary with all dataframes of investments prepared
        # in case of witness studies, self.years has index=years whereas invests have index starting at 0
        # => Reset self.years index so that they are consistent with invests indices and fill out properly the df
        self.investment_per_technology_dict = {
            full_techno_name: pd.DataFrame(
                {GlossaryEnergy.Years: self.years.reset_index(drop=True), GlossaryEnergy.InvestValue: invests
                 }) for full_techno_name, invests in investments_dict.items()}

    def check_data_integrity(self, inputs_dict):
        '''
        Check the data integrity of the model
        Returns a dict with problematic variable name as keys and integrity msg to send to the GUI as values
        '''
        # Check that all input values are filled (No None in values) If none it is checked by the genric data integrity function
        integrity_msg_dict = {}

        self.configure_parameters(inputs_dict)

        integrity_msg_dict.update(self.check_integrity_techno_percentages())

        return integrity_msg_dict

    def check_integrity_techno_percentages(self):
        """
        Check sum of technos percentages is 100%
        """
        integrity_msg_dict = {}

        techno_percentages_col = self.techno_invest_percentage_df.columns[
            self.techno_invest_percentage_df.columns != 'years']

        # check if sum is 100% or not with accuracy of 0.001
        all_years_equal_100 = all(
            isclose(self.techno_invest_percentage_df[self.techno_invest_percentage_df['years'] == year][
                        techno_percentages_col].sum(axis=1).values[0], 100., rel_tol=1e-5)
            for year in self.techno_invest_percentage_df['years']
        )
        if not all_years_equal_100:
            integrity_msg_dict[GlossaryEnergy.TechnoInvestPercentageName] = ('Sum of percentages is not equal to 100%, '
                                                                             'please verify your input dataframe')
        return integrity_msg_dict
