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

import scipy.interpolate as sc
import numpy as np
from os.path import dirname
from sos_trades_core.execution_engine.execution_engine import ExecutionEngine
from sos_trades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest


class DesignVariablesTestCase(AbstractJacobianUnittest):
    """
    Design variables test class
    """
    #AbstractJacobianUnittest.DUMP_JACOBIAN = True

    def analytic_grad_entry(self):
        return [
            self.test_01_design_var_discipline_analytic_grad,
        ]

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.year_start = 2020
        self.year_end = 2050
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.energy_list = ['hydrogen.gaseous_hydrogen', 'methane']
        self.methane_techno_list = [
            'FossilGas', 'Methanation', 'UpgradingBiogas']
        self.hydrogen_techno_list = ['SMR', 'Electrolysis', 'PlasmaCracking']

        self.hydrogen_prices = np.array([0.076815, 0.07549102, 0.07433427, 0.07330841, 0.07238752,
                                         0.07155253, 0.07050461, 0.06960523, 0.068821, 0.06812833,
                                         0.06750997, 0.066893, 0.06635812, 0.06589033, 0.06547834,
                                         0.06511344, 0.06478879, 0.06449895, 0.06423948, 0.06400678,
                                         0.06379784, 0.06361016, 0.06344163, 0.06329045, 0.06315508,
                                         0.0630342, 0.06292668, 0.06283151, 0.06274783, 0.06267487,
                                         0.06261198])
        self.methane_prices = np.array([0.19333753, 0.1874625, 0.18467199, 0.21320619, 0.2308158,
                                        0.24196874, 0.25146023, 0.25909781, 0.26565857, 0.27142873,
                                        0.27673861, 0.27989425, 0.28277203, 0.28558565, 0.28905927,
                                        0.29229019, 0.29530982, 0.29853801, 0.29984838, 0.30094081,
                                        0.30355508, 0.3071769, 0.31104297, 0.31440867, 0.31709487,
                                        0.32047716, 0.32392652, 0.32739837, 0.33021771, 0.33313758,
                                        0.3361545])
        self.hydrogen_mix = np.array([1.69407693e+01, 1.01853673e+01, 7.81577346e+00, -4.08137903e+01,
                                      -1.08122741e+02, -1.99341666e+02, -3.27599329e+02, -5.20639555e+02,
                                      -8.41004523e+02, -1.44860347e+03, -3.04720041e+03, -2.02675286e+04,
                                      6.23793605e+03, 2.94895543e+03, 2.07088479e+03, 1.66411974e+03,
                                      1.42963825e+03, 1.27719843e+03, 1.46213096e+03, 1.80862005e+03,
                                      1.82285580e+03, 1.83521296e+03, 2.02423489e+03, 2.20596930e+03,
                                      2.40044247e+03, 2.62260151e+03, 2.89037960e+03, 3.22949791e+03,
                                      3.67135444e+03,  4.13143818e+03, 4.57270843e+03])
        self.methane_mix = np.array([83.05923073, 89.8146327, 92.18422654, 140.81379029,
                                     208.12274052, 299.34166615, 427.59932861, 620.63955456,
                                     941.00452341, 1548.60347321, 3147.20040973, 20367.52864439,
                                     -6137.93605048, -2848.95543477, -1970.8847938, -1564.11974426,
                                     -1329.63824886, -1177.19843087, -1362.13096127, -1708.62005263,
                                     -1722.85579984, -1735.21295601, -1924.23488779, -2105.96930341,
                                     -2300.44247284, -2522.60150558, -2790.37959806, -3129.49790527,
                                     -3571.3544391, -4031.438176, -4472.70843])
        self.SMR_mix = np.array([1.28602088, 1.35074878, 1.4067371, 1.50825212, 1.67137695,
                                 1.79909285, 1.92694645, 2.08259147, 2.11450777, 2.06934613,
                                 2.35420123, 2.43776006, 2.41716843, 2.45052476, 2.38371769,
                                 2.30986649, 2.30016962, 2.32851773, 2.4606011, 2.44801854,
                                 2.30719665, 2.18046598, 2.14573585, 2.10955638, 2.07601016,
                                 2.04495191, 2.01625348, 1.98979781, 1.9654826, 1.94367325,
                                 1.92427264])
        self.Electrolysis_mix = np.array([1.28602088, 1.35074878, 1.4067371, 1.50825212, 1.67137695,
                                          1.79909285, 1.92694645, 2.08259147, 2.11450777, 2.06934613,
                                          2.35420123, 2.43776006, 2.41716843, 2.45052476, 2.38371769,
                                          2.30986649, 2.30016962, 2.32851773, 2.4606011, 2.44801854,
                                          2.30719665, 2.18046598, 2.14573585, 2.10955638, 2.07601016,
                                          2.04495191, 2.01625348, 1.98979781, 1.9654826, 1.94367325,
                                          1.92427264])
        self.PlasmaCracking_mix = np.array([97.42795825, 97.29850243, 97.18652581, 96.98349576, 96.65724611,
                                            96.4018143, 96.14610711, 95.83481705, 95.77098445, 95.86130774,
                                            95.29159753, 95.12447988, 95.16566313, 95.09895048, 95.23256462,
                                            95.38026701, 95.39966075, 95.34296454, 95.0787978, 95.10396291,
                                            95.3856067, 95.63906804, 95.7085283, 95.78088725, 95.84797967,
                                            95.91009617, 95.96749304, 96.02040438, 96.0690348, 96.1126535,
                                            96.15145473])
        self.FossilGas_mix = np.array([0.33] * 31)
        self.Methanation_mix = np.array([0.33] * 31)
        self.UpgradingBiogas_mix = np.array([0.33] * 31)
        co2_taxes_year = [self.year_start, self.year_end]
        co2_taxes = [20.0, 620.0]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')
        self.co2_taxes_array = func(self.years)

    def test_01_design_var_discipline_analytic_grad(self):

        self.name = 'Test'
        self.model_name = 'design_var'
        self.ee = ExecutionEngine(self.name)
        ns_dict = {'ns_public': self.name, 'ns_energy': f'{self.name}',
                   'ns_energy_study': f'{self.name}', 'ns_energy_mix': f'{self.name}'}
        self.ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.design_variables_translation.design_var_disc.Design_Var_Discipline'
        builder = self.ee.factory.get_builder_from_module(
            self.model_name, mod_path)

        self.ee.factory.set_builders_to_coupling_builder(builder)

        self.ee.configure()
        self.ee.display_treeview_nodes()

        inputs_dict = {f'{self.name}.energy_list': self.energy_list,
                       f'{self.name}.methane.technologies_list': self.methane_techno_list,
                       f'{self.name}.hydrogen.gaseous_hydrogen.technologies_list': self.hydrogen_techno_list,
                       f'{self.name}.hydrogen.gaseous_hydrogen.hydrogen_gaseous_hydrogen_array_mix': self.hydrogen_mix,
                       f'{self.name}.methane.methane_array_mix': self.methane_mix,
                       f'{self.name}.hydrogen.gaseous_hydrogen.SMR.hydrogen_gaseous_hydrogen_SMR_array_mix': self.SMR_mix,
                       f'{self.name}.hydrogen.gaseous_hydrogen.Electrolysis.hydrogen_gaseous_hydrogen_Electrolysis_array_mix': self.Electrolysis_mix,
                       f'{self.name}.hydrogen.gaseous_hydrogen.PlasmaCracking.hydrogen_gaseous_hydrogen_PlasmaCracking_array_mix': self.PlasmaCracking_mix,
                       f'{self.name}.methane.FossilGas.methane_FossilGas_array_mix': self.FossilGas_mix,
                       f'{self.name}.methane.Methanation.methane_Methanation_array_mix': self.Methanation_mix,
                       f'{self.name}.methane.UpgradingBiogas.methane_UpgradingBiogas_array_mix': self.UpgradingBiogas_mix,
                       f'{self.name}.CO2_taxes_array': self.co2_taxes_array
                       }

        self.ee.load_study_from_input_dict(inputs_dict)

        disc = self.ee.root_process.sos_disciplines[0]

        inputs_names = [
            f'{self.name}.{energy}.' + energy.replace('.', '_') + '_array_mix' for energy in self.energy_list]
        inputs_names.extend(
            [f'{self.name}.hydrogen.gaseous_hydrogen.{techno}.hydrogen_gaseous_hydrogen_{techno}_array_mix' for techno in self.hydrogen_techno_list])
        inputs_names.extend(
            [f'{self.name}.methane.{techno}.methane_{techno}_array_mix' for techno in self.methane_techno_list])

        self.check_jacobian(location=dirname(__file__), filename=f'jacobian_{self.model_name}.pkl',
                            discipline=disc, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
                            inputs=inputs_names,
                            outputs=[f'{self.name}.invest_energy_mix',
                                     f'{self.name}.methane.invest_techno_mix',
                                     f'{self.name}.hydrogen.gaseous_hydrogen.invest_techno_mix'])  # , parallel=True)


if '__main__' == __name__:
    cls = DesignVariablesTestCase()
    cls.test_01_design_var_discipline_analytic_grad()
