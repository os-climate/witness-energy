'''
Copyright 2022 Airbus SAS

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

class ScenarioModel:
    """
    Class for the data depending on scenario
    """

    def __init__(self, scenario_name, carbon_taxe, transport_price, transport_margin):
        self.scenario_name = scenario_name
        #-- Inputs attributes set from configure method
        self.year_start = 2020  # year start
        self.year_end = 2100  # year end
        self.co2_taxe_all = carbon_taxe  # data of all scenairos
        self.transport_price_all = transport_price  # data of all scenarios
        self.transport_margin_all = transport_margin

    def configure_co2_taxe(self):
        """
        get the carbon taxe of the considered scenario
        """
        return(self.co2_taxe_all[self.scenario_name])

    def configure_transport_price(self):
        """
        get the transport price of the considered scenario
        """
        return(self.transport_price_all[self.scenario_name])

    def configure_transport_margin(self):
        """
        get the transport price of the considered scenario
        """
        return(self.transport_margin_all[self.scenario_name])
