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
#
# import numpy as np
# import pandas as pd
# from os.path import dirname
# from sostrades_core.execution_engine.execution_engine import ExecutionEngine
#
# # from energy_models.sos_processes.energy.MDO_subprocesses.energy_optim_sub_process.usecase import Study
# from energy_models.sos_processes.energy.MDA.energy_process_v0.usecase import Study as Study_open
# from sostrades_core.tests.core.abstract_jacobian_unit_test import AbstractJacobianUnittest
# from sostrades_core.tools.post_processing.post_processing_factory import PostProcessingFactory
# from energy_models.core.energy_mix.energy_mix import EnergyMix
#
# import scipy.interpolate as sc
#
#
# class EnergyMixJacobianTestCase(AbstractJacobianUnittest):
#     """
#     Energy mix jacobian test class
#     """
#     # AbstractJacobianUnittest.DUMP_JACOBIAN = False
#     parallel = True
#
#     def analytic_grad_entry(self):
#         return [
#
#             self._test_01_energy_mix_discipline_jacobian_obj_constraints_wrt_state_variables,
#             self.test_02_energy_mix_discipline_residual_vars_wrt_state_variables,
#             self.test_03_gradient_energy_mix_with_open_loop,
#             self.test_04_energy_mix_discipline_co2_emissions_gt,
#             self.test_05_energy_mix_test_mean_price_grad,
#             self.test_06_energy_mix_all_outputs,
#             self.test_07_energy_mix_co2_tax,
#             self.test_08_energy_mix_gradients_exponential_limit,
#             self.test_10_energy_mix_demand_dataframe,
#             self.test_11_energy_mix_detailed_co2_emissions,
#             self.test_13_energy_mix_co2_per_use_gradients,
#             self.test_14_energy_mix_with_losses,
#             self.test_15_energy_mix_with_agriculture_mix]
#
#     def setUp(self):
#         '''
#         Initialize third data needed for testing
#         '''
#         self.disc_name = 'energy_mix'
#         self.year_start = 2020
#         self.year_end = 2050
#         self.years = np.arange(self.year_start, self.year_end + 1)
#         self.year_range = self.year_end - self.year_start + 1
#         self.energy_list = ['hydrogen.gaseous_hydrogen', 'methane']
#         self.consumption_hydro = pd.DataFrame(
#             {'electricity (TWh)': np.array([5.79262302e+09, 5.96550630e+09, 6.13351314e+09, 6.29771389e+09,
#                                             6.45887954e+09, 6.61758183e+09, 6.81571547e+09, 7.00833095e+09,
#                                             7.19662898e+09, 7.38146567e+09, 7.56347051e+09, 7.58525158e+09,
#                                             7.60184181e+09, 7.61413788e+09, 7.62282699e+09, 7.62844682e+09,
#                                             7.63143167e+09, 7.63212186e+09, 7.63080121e+09, 7.62770511e+09,
#                                             7.62303081e+09, 7.61658967e+09, 7.60887892e+09, 7.60002116e+09,
#                                             7.59012249e+09, 7.57927528e+09, 7.56756653e+09, 7.55506132e+09,
#                                             7.54182260e+09, 7.52790631e+09, 7.51336234e+09]) / 1.0e9,
#              'methane (TWh)': np.array([1.30334018e+10, 1.34223892e+10, 1.38004046e+10, 1.41698563e+10,
#                                         1.45324790e+10, 1.48895591e+10, 1.53353598e+10, 1.57687446e+10,
#                                         1.61924152e+10, 1.66082977e+10, 1.70178086e+10, 1.70668161e+10,
#                                         1.71041441e+10, 1.71318102e+10, 1.71513607e+10, 1.71640053e+10,
#                                         1.71707213e+10, 1.71722742e+10, 1.71693027e+10, 1.71623365e+10,
#                                         1.71518193e+10, 1.71373267e+10, 1.71199776e+10, 1.71000476e+10,
#                                         1.70777756e+10, 1.70533694e+10, 1.70270247e+10, 1.69988880e+10,
#                                         1.69691008e+10, 1.69377892e+10, 1.69050653e+10]) / 1.0e9,
#              'water (Mt)': np.array([8.23100419e+09, 8.47666200e+09, 8.71539063e+09, 8.94871102e+09,
#                                      9.17771870e+09, 9.40322607e+09, 9.68476326e+09, 9.95845946e+09,
#                                      1.02260208e+10, 1.04886637e+10, 1.07472828e+10, 1.07782325e+10,
#                                      1.08018063e+10, 1.08192784e+10, 1.08316251e+10, 1.08396106e+10,
#                                      1.08438519e+10, 1.08448326e+10, 1.08429560e+10, 1.08385567e+10,
#                                      1.08319147e+10, 1.08227622e+10, 1.08118056e+10, 1.07992193e+10,
#                                      1.07851538e+10, 1.07697405e+10, 1.07531030e+10, 1.07353338e+10,
#                                      1.07165222e+10, 1.06967480e+10, 1.06760818e+10]) / 1.0e9})
#
#         self.production_hydro = pd.DataFrame(
#             {'hydrogen.gaseous_hydrogen': np.array([2.89631151e+10, 2.98275315e+10, 3.06675657e+10, 3.14885694e+10,
#                                                     3.22943977e+10, 3.30879091e+10, 3.40785773e+10, 3.50416548e+10,
#                                                     3.59831449e+10, 3.69073283e+10, 3.78173526e+10, 3.79262579e+10,
#                                                     3.80092091e+10, 3.80706894e+10, 3.81141349e+10, 3.81422341e+10,
#                                                     3.81571584e+10, 3.81606093e+10, 3.81540060e+10, 3.81385255e+10,
#                                                     3.81151541e+10, 3.80829483e+10, 3.80443946e+10, 3.80001058e+10,
#                                                     3.79506125e+10, 3.78963764e+10, 3.78378327e+10, 3.77753066e+10,
#                                                     3.77091130e+10, 3.76395315e+10, 3.75668117e+10]) / 1.0e9,
#              'hydrogen.gaseous_hydrogen SMR (TWh)': np.array(
#                  [1.44815575e+10, 1.49137658e+10, 1.53337829e+10, 1.57442847e+10,
#                   1.61471989e+10, 1.65439546e+10, 1.70392887e+10, 1.75208274e+10,
#                   1.79915724e+10, 1.84536642e+10, 1.89086763e+10, 1.89631289e+10,
#                   1.90046045e+10, 1.90353447e+10, 1.90570675e+10, 1.90711170e+10,
#                   1.90785792e+10, 1.90803046e+10, 1.90770030e+10, 1.90692628e+10,
#                   1.90575770e+10, 1.90414742e+10, 1.90221973e+10, 1.90000529e+10,
#                   1.89753062e+10, 1.89481882e+10, 1.89189163e+10, 1.88876533e+10,
#                   1.88545565e+10, 1.88197658e+10, 1.87834058e+10]) / 1.0e9,
#              'CO2 (Mt)': np.array([1.45250457e+09, 1.49585518e+09, 1.53798303e+09, 1.57915649e+09,
#                                    1.61956889e+09, 1.65936361e+09, 1.70904577e+09, 1.75734425e+09,
#                                    1.80456012e+09, 1.85090806e+09, 1.89654591e+09, 1.90200753e+09,
#                                    1.90616754e+09, 1.90925079e+09, 1.91142959e+09, 1.91283877e+09,
#                                    1.91358722e+09, 1.91376029e+09, 1.91342913e+09, 1.91265278e+09,
#                                    1.91148070e+09, 1.90986558e+09, 1.90793210e+09, 1.90571101e+09,
#                                    1.90322891e+09, 1.90050897e+09, 1.89757299e+09, 1.89443730e+09,
#                                    1.89111768e+09, 1.88762816e+09, 1.88398125e+09]) / 1.0e9,
#              'hydrogen.gaseous_hydrogen Electrolysis (TWh)': np.array(
#                  [1.44815575e+10, 1.49137658e+10, 1.53337829e+10, 1.57442847e+10,
#                   1.61471989e+10, 1.65439546e+10, 1.70392887e+10, 1.75208274e+10,
#                   1.79915724e+10, 1.84536642e+10, 1.89086763e+10, 1.89631289e+10,
#                   1.90046045e+10, 1.90353447e+10, 1.90570675e+10, 1.90711170e+10,
#                   1.90785792e+10, 1.90803046e+10, 1.90770030e+10, 1.90692628e+10,
#                   1.90575770e+10, 1.90414742e+10, 1.90221973e+10, 1.90000529e+10,
#                   1.89753062e+10, 1.89481882e+10, 1.89189163e+10, 1.88876533e+10,
#                   1.88545565e+10, 1.88197658e+10, 1.87834058e+10]) / 1.0e9,
#              'O2 (Mt)': np.array([1.45250457e+09, 1.49585518e+09, 1.53798303e+09, 1.57915649e+09,
#                                   1.61956889e+09, 1.65936361e+09, 1.70904577e+09, 1.75734425e+09,
#                                   1.80456012e+09, 1.85090806e+09, 1.89654591e+09, 1.90200753e+09,
#                                   1.90616754e+09, 1.90925079e+09, 1.91142959e+09, 1.91283877e+09,
#                                   1.91358722e+09, 1.91376029e+09, 1.91342913e+09, 1.91265278e+09,
#                                   1.91148070e+09, 1.90986558e+09, 1.90793210e+09, 1.90571101e+09,
#                                   1.90322891e+09, 1.90050897e+09, 1.89757299e+09, 1.89443730e+09,
#                                   1.89111768e+09, 1.88762816e+09, 1.88398125e+09]) / 1.0e9})
#
#         self.prices_hydro = pd.DataFrame(
#             {'hydrogen.gaseous_hydrogen': np.array([0.076815, 0.07549102, 0.07433427, 0.07330841, 0.07238752,
#                                                     0.07155253, 0.07050461, 0.06960523, 0.068821, 0.06812833,
#                                                     0.06750997, 0.066893, 0.06635812, 0.06589033, 0.06547834,
#                                                     0.06511344, 0.06478879, 0.06449895, 0.06423948, 0.06400678,
#                                                     0.06379784, 0.06361016, 0.06344163, 0.06329045, 0.06315508,
#                                                     0.0630342, 0.06292668, 0.06283151, 0.06274783, 0.06267487,
#                                                     0.06261198]) * 1000.0})
#
#         self.consumption = pd.DataFrame(
#             {'CO2 (Mt)': np.array([1.28473431e+09, 1.24026410e+09, 1.20920553e+09, 2.49446882e+10,
#                                    5.50034920e+10, 8.99877703e+10, 1.29098065e+11, 1.71931680e+11,
#                                    2.18234033e+11, 2.68123194e+11, 3.21458915e+11, 3.78134326e+11,
#                                    4.38214336e+11, 5.01623337e+11, 5.66820327e+11, 6.33674016e+11,
#                                    7.02070511e+11, 7.71909835e+11, 8.19285617e+11, 8.61586757e+11,
#                                    9.00230650e+11, 9.35836743e+11, 9.68739031e+11, 9.99135391e+11,
#                                    1.02697781e+12, 1.05232158e+12, 1.07519492e+12, 1.09560777e+12,
#                                    1.11355731e+12, 1.13049193e+12, 1.14650986e+12]) / 1.0e9,
#              'hydrogen.gaseous_hydrogen (TWh)': np.array(
#                  [7.83846196e+09, 7.56713887e+09, 7.37764337e+09, 1.52193327e+11,
#                   3.35589060e+11, 5.49036255e+11, 7.87657231e+11, 1.04899505e+12,
#                   1.33149645e+12, 1.63588179e+12, 1.96129539e+12, 2.30708521e+12,
#                   2.67364729e+12, 3.06052031e+12, 3.45830226e+12, 3.86619212e+12,
#                   4.28349500e+12, 4.70960091e+12, 4.99865154e+12, 5.25674061e+12,
#                   5.49251596e+12, 5.70975699e+12, 5.91050148e+12, 6.09595672e+12,
#                   6.26582979e+12, 6.42045801e+12, 6.56001356e+12, 6.68455710e+12,
#                   6.79407140e+12, 6.89739345e+12, 6.99512256e+12]) / 1.0e9,
#              'electricity (TWh)': np.array([1.24834354e+10, 2.26888500e+10, 3.13224798e+10, 4.16183686e+10,
#                                             5.33137316e+10, 6.65015094e+10, 8.07396503e+10, 9.59308386e+10,
#                                             1.12076605e+11, 1.29500242e+11, 1.48068984e+11, 1.67664859e+11,
#                                             1.88614872e+11, 2.10307763e+11, 2.32534190e+11, 2.55258218e+11,
#                                             2.78448193e+11, 3.02075958e+11, 3.26116264e+11, 3.50546301e+11,
#                                             3.66620834e+11, 3.81434383e+11, 3.98191584e+11, 4.13453346e+11,
#                                             4.27540649e+11, 4.40613006e+11, 4.52762555e+11, 4.64046630e+11,
#                                             4.74445226e+11, 4.83975687e+11, 4.92647562e+11]) / 1.0e9,
#              'biogas (TWh)': np.array([1.49773000e+11, 2.72214901e+11, 3.75798938e+11, 4.99326325e+11,
#                                        6.39644238e+11, 7.97867754e+11, 9.68693252e+11, 1.15095316e+12,
#                                        1.34466585e+12, 1.55371011e+12, 1.77649302e+12, 2.01159922e+12,
#                                        2.26295200e+12, 2.52321765e+12, 2.78988452e+12, 3.06252149e+12,
#                                        3.34074875e+12, 3.62422851e+12, 3.91265782e+12, 4.20576304e+12,
#                                        4.39862108e+12, 4.57635017e+12, 4.77739870e+12, 4.96050534e+12,
#                                        5.12952113e+12, 5.28635985e+12, 5.43212697e+12, 5.56751036e+12,
#                                        5.69227000e+12, 5.80661398e+12, 5.91065688e+12]) / 1.0e9,
#              'MEA (Mt)': np.array([7.43925657e+08, 1.35209717e+09, 1.86660126e+09, 2.48016441e+09,
#                                    3.17712645e+09, 3.96302600e+09, 4.81151986e+09, 5.71680869e+09,
#                                    6.67898370e+09, 7.71731095e+09, 8.82387839e+09, 9.99165585e+09,
#                                    1.12401304e+10, 1.25328754e+10, 1.38574154e+10, 1.52116089e+10,
#                                    1.65935696e+10, 1.80016196e+10, 1.94342541e+10, 2.08901139e+10,
#                                    2.18480439e+10, 2.27308280e+10, 2.37294403e+10, 2.46389349e+10,
#                                    2.54784398e+10, 2.62574611e+10, 2.69814895e+10, 2.76539416e+10,
#                                    2.82736254e+10, 2.88415743e+10, 2.93583576e+10]) / 1.0e9})
#
#         self.production = pd.DataFrame(
#             {'methane': np.array([1.16605879e+11, 2.09714671e+11, 2.88496631e+11, 4.30619647e+11,
#                                   5.98336737e+11, 7.89664048e+11, 9.98944599e+11, 1.22447365e+12,
#                                   1.46574928e+12, 1.72596317e+12, 2.00361864e+12, 2.29742180e+12,
#                                   2.61049046e+12, 2.93708922e+12, 3.27218360e+12, 3.61517937e+12,
#                                   3.96555667e+12, 4.32285576e+12, 4.63840191e+12, 4.94722388e+12,
#                                   5.17232979e+12, 5.37976418e+12, 5.59946957e+12, 5.80044012e+12,
#                                   5.98550982e+12, 6.15624743e+12, 6.31355157e+12, 6.45796597e+12,
#                                   6.58930224e+12, 6.71065379e+12, 6.82230688e+12]) / 1.0e9,
#              'methane Emethane (TWh)': np.array([2.60340125e+09, 2.51328627e+09, 2.45034882e+09, 5.05482199e+10,
#                                                  1.11459746e+11, 1.82352314e+11, 2.61605891e+11, 3.48404451e+11,
#                                                  4.42232103e+11, 5.43328106e+11, 6.51408261e+11, 7.66256003e+11,
#                                                  8.88002867e+11, 1.01649564e+12, 1.14861161e+12, 1.28408474e+12,
#                                                  1.42268423e+12, 1.56420749e+12, 1.66021035e+12, 1.74592990e+12,
#                                                  1.82423835e+12, 1.89639097e+12, 1.96306457e+12, 2.02466013e+12,
#                                                  2.08108035e+12, 2.13243727e+12, 2.17878808e+12, 2.22015293e+12,
#                                                  2.25652610e+12, 2.29084262e+12, 2.32330155e+12]) / 1.0e9,
#              GlossaryCore.InvestValue: np.array([8.87150e+09, 9.04400e+09, 9.21650e+09, 9.38900e+09, 9.56150e+09,
#                                  9.73400e+09, 9.93880e+09, 1.01436e+10, 1.03484e+10, 1.05532e+10,
#                                  1.07580e+10, 1.07294e+10, 1.07008e+10, 1.06722e+10, 1.06436e+10,
#                                  1.06150e+10, 1.05864e+10, 1.05578e+10, 1.05292e+10, 1.05006e+10,
#                                  1.04720e+10, 1.04434e+10, 1.04148e+10, 1.03862e+10, 1.03576e+10,
#                                  1.03290e+10, 1.03004e+10, 1.02718e+10, 1.02432e+10, 1.02146e+10,
#                                  1.01860e+10]) / 1.0e9,
#              'water (Mt)': np.array([4.20719806e+08, 4.06156873e+08, 3.95985935e+08, 8.16878967e+09,
#                                      1.80123301e+10, 2.94688458e+10, 4.22765332e+10, 5.63035194e+10,
#                                      7.14664343e+10, 8.78039430e+10, 1.05270118e+11, 1.23829961e+11,
#                                      1.43504730e+11, 1.64269664e+11, 1.85620121e+11, 2.07513107e+11,
#                                      2.29911326e+11, 2.52782037e+11, 2.68296474e+11, 2.82149087e+11,
#                                      2.94804040e+11, 3.06464185e+11, 3.17238898e+11, 3.27192980e+11,
#                                      3.36310708e+11, 3.44610188e+11, 3.52100660e+11, 3.58785381e+11,
#                                      3.64663427e+11, 3.70209111e+11, 3.75454601e+11]) / 1.0e9,
#              'methane UpgradingBiogas (TWh)': np.array([1.14002477e+11, 2.07201385e+11, 2.86046282e+11, 3.80071427e+11,
#                                                         4.86876991e+11, 6.07311734e+11, 7.37338708e+11, 8.76069197e+11,
#                                                         1.02351718e+12, 1.18263506e+12, 1.35221038e+12, 1.53116579e+12,
#                                                         1.72248759e+12, 1.92059358e+12, 2.12357198e+12, 2.33109463e+12,
#                                                         2.54287243e+12, 2.75864827e+12, 2.97819156e+12, 3.20129399e+12,
#                                                         3.34809144e+12, 3.48337321e+12, 3.63640500e+12, 3.77577999e+12,
#                                                         3.90442947e+12, 4.02381016e+12, 4.13476348e+12, 4.23781304e+12,
#                                                         4.33277614e+12, 4.41981116e+12, 4.49900533e+12]) / 1.0e9,
#              'CO2 (Mt)': np.array([5.62582867e+09, 1.02250365e+10, 1.41158983e+10, 1.87558795e+10,
#                                    2.40265528e+10, 2.99698028e+10, 3.63864132e+10, 4.32325272e+10,
#                                    5.05088346e+10, 5.83610321e+10, 6.67292861e+10, 7.55604318e+10,
#                                    8.50018377e+10, 9.47780320e+10, 1.04794671e+11, 1.15035562e+11,
#                                    1.25486437e+11, 1.36134608e+11, 1.46968696e+11, 1.57978422e+11,
#                                    1.65222627e+11, 1.71898553e+11, 1.79450412e+11, 1.86328331e+11,
#                                    1.92676964e+11, 1.98568198e+11, 2.04043557e+11, 2.09128877e+11,
#                                    2.13815145e+11, 2.18110176e+11, 2.22018273e+11]) / 1.0e9})
#
#         self.cost_details = pd.DataFrame({'methane': np.array([0.19333753, 0.1874625, 0.18467199, 0.21320619, 0.2308158,
#                                                                0.24196874, 0.25146023, 0.25909781, 0.26565857,
#                                                                0.27142873,
#                                                                0.27673861, 0.27989425, 0.28277203, 0.28558565,
#                                                                0.28905927,
#                                                                0.29229019, 0.29530982, 0.29853801, 0.29984838,
#                                                                0.30094081,
#                                                                0.30355508, 0.3071769, 0.31104297, 0.31440867,
#                                                                0.31709487,
#                                                                0.32047716, 0.32392652, 0.32739837, 0.33021771,
#                                                                0.33313758,
#                                                                0.3361545]) * 1000.0})
#
#         self.land_use_required_mock = pd.DataFrame(
#             {GlossaryCore.Years: self.years, 'random techno (Gha)': 0.0})
#
#         self.land_use_required_biomass = pd.DataFrame(
#             {GlossaryCore.Years: self.years, 'biomass_dry (Gha)': 0.0})
#         self.land_use_required_methane = pd.DataFrame(
#             {GlossaryCore.Years: self.years, 'mathane (Gha)': 0.0})
#         years = np.arange(2020, 2051)
#         co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
#         co2_taxes = [14.86, 17.22, 20.27,
#                      29.01, 34.05, 39.08, 44.69, 50.29]
#         func = sc.interp1d(co2_taxes_year, co2_taxes,
#                            kind='linear', fill_value='extrapolate')
#
#         self.co2_taxes = pd.DataFrame(
#             {GlossaryCore.Years: years, GlossaryCore.CO2Tax: func(years)})
#         # Biomass dry inputs coming from agriculture mix disc
#         #
#         energy_consumption_biomass = np.linspace(0, 4, self.year_range)
#         self.energy_consumption_biomass = pd.DataFrame(
#             {GlossaryCore.Years: self.years, 'CO2_resource (Mt)': energy_consumption_biomass})
#
#         energy_consumption_woratio_biomass = np.linspace(0, 4, self.year_range)
#         self.energy_consumption_woratio_biomass = pd.DataFrame(
#             {GlossaryCore.Years: self.years, 'CO2_resource (Mt)': energy_consumption_woratio_biomass})
#
#         energy_production_biomass = np.linspace(15, 16, self.year_range)
#         self.energy_production_biomass = pd.DataFrame(
#             {GlossaryCore.Years: self.years, 'biomass_dry': energy_production_biomass})
#
#         energy_prices_biomass = np.linspace(9, 9, self.year_range)
#         energy_prices_wotaxes_biomass = np.linspace(9, 9, self.year_range)
#         self.energy_prices_biomass = pd.DataFrame(
#             {GlossaryCore.Years: self.years, 'biomass_dry': energy_prices_biomass,
#              'biomass_dry_wotaxes': energy_prices_wotaxes_biomass})
#
#         CO2_per_use_biomass = np.linspace(0, 1, self.year_range)
#         self.CO2_per_use_biomass = pd.DataFrame(
#             {GlossaryCore.Years: self.years, 'CO2_per_use': CO2_per_use_biomass})
#
#         CO2_emissions_biomass = np.linspace(0, -1, self.year_range)
#         self.CO2_emissions_biomass = pd.DataFrame(
#             {GlossaryCore.Years: self.years, 'biomass_dry': CO2_emissions_biomass})
#
#         # ---Ratios---
#         demand_ratio_dict = dict(
#             zip(EnergyMix.energy_list, np.linspace(0.2, 0.8, len(self.years))))
#         demand_ratio_dict[GlossaryCore.Years] = self.years
#         self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)
#
#         resource_ratio_dict = dict(
#             zip(EnergyMix.RESOURCE_LIST, np.linspace(0.9, 0.3, len(self.years))))
#         resource_ratio_dict[GlossaryCore.Years] = self.years
#         self.all_resource_ratio_usable_demand = pd.DataFrame(
#             resource_ratio_dict)
#
#     def _test_01_energy_mix_discipline_jacobian_obj_constraints_wrt_state_variables(self):
#
#         self.name = 'Test'
#         self.ee = ExecutionEngine(self.name)
#         name = 'Test'
#         model_name = 'EnergyMix'
#         func_manager_name = 'FunctionManagerDisc'
#
#         repo = 'energy_models.sos_processes.energy.MDA'
#         builder = self.ee.factory.get_builder_from_process(
#             repo, 'energy_process_v0')
#
#         self.ee.factory.set_builders_to_coupling_builder(builder)
#         self.ee.configure()
#         usecase = Study_open(execution_engine=self.ee)
#         usecase.study_name = self.name
#         values_dict = usecase.setup_usecase()
#
#         self.ee.display_treeview_nodes()
#         full_values_dict = {}
#         for dict_v in values_dict:
#             full_values_dict.update(dict_v)
#
#         full_values_dict[f'{name}.epsilon0'] = 1.0
#         full_values_dict[f'{name}.tolerance'] = 1.0e-8
#         full_values_dict[f'{name}.max_mda_iter'] = 50
#         self.ee.load_study_from_input_dict(full_values_dict)
#
#         self.ee.execute()
#
#         disc = self.ee.dm.get_disciplines_with_name(
#             f'{self.name}.EnergyMix')[0]
#         energy_list = full_values_dict['Test.energy_list']
#
#         inputs_names = [
#             f'{name}.{model_name}.{energy}.{GlossaryCore.EnergyPricesValue}' for energy in energy_list if
#             energy not in ['carbon_capture', 'carbon_storage']]
#         inputs_names.extend([
#             f'{name}.{model_name}.{energy}.{GlossaryCore.EnergyProductionValue}' for energy in energy_list if
#             energy not in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.{model_name}.{energy}.{GlossaryCore.EnergyConsumptionValue}' for energy in energy_list if
#              energy not in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.CCUS.{energy}.{GlossaryCore.EnergyConsumptionValue}' for energy in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.CCUS.{energy}.{GlossaryCore.EnergyProductionValue}' for energy in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend([
#             f'{name}.CCUS.{energy}.{GlossaryCore.EnergyPricesValue}' for energy in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.{model_name}.{energy}.{GlossaryCore.CO2EmissionsValue}' for energy in energy_list if
#              energy not in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.{model_name}.syngas.syngas_ratio'])
#         inputs_names.extend(
#             [f'{name}.{GlossaryCore.CO2TaxesValue}'])
#
#         outputs_names = [f'{name}.{func_manager_name}.energy_production_objective',
#                          f'{name}.{func_manager_name}.primary_energies_production',
#                          f'{name}.{func_manager_name}.total_prod_solid_fuel_elec',
#                          f'{name}.{func_manager_name}.total_prod_h2_liquid',
#                          f'{name}.{func_manager_name}.syngas_prod_objective',
#                          ]
#         # AbstractJacobianUnittest.DUMP_JACOBIAN = True
#         self.check_jacobian(location=dirname(__file__), filename=f'jacobian_obj_constraints_wrt_state_variables.pkl',
#                             discipline=disc, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
#                             local_data=disc.local_data,
#                             inputs=inputs_names, outputs=outputs_names, parallel=self.parallel)
#
#     def test_02_energy_mix_discipline_coupling_variables(self):
#
#         self.name = 'Test'
#         self.ee = ExecutionEngine(self.name)
#         name = 'Test'
#         model_name = 'EnergyMix'
#
#         repo = 'energy_models.sos_processes.energy.MDA'
#         builder = self.ee.factory.get_builder_from_process(
#             repo, 'energy_process_v0')
#
#         self.ee.factory.set_builders_to_coupling_builder(builder)
#         self.ee.configure()
#         usecase = Study_open(execution_engine=self.ee)
#         usecase.study_name = self.name
#         values_dict = usecase.setup_usecase()
#
#         self.ee.display_treeview_nodes()
#         full_values_dict = {}
#         for dict_v in values_dict:
#             full_values_dict.update(dict_v)
#         full_values_dict[f'{name}.epsilon0'] = 1.0
#         full_values_dict[f'{name}.tolerance'] = 1.0e-8
#         full_values_dict[f'{name}.max_mda_iter'] = 50
#         self.ee.load_study_from_input_dict(full_values_dict)
#
#         self.ee.execute()
#
#         disc = self.ee.dm.get_disciplines_with_name(
#             f'{self.name}.EnergyMix')[0]
#         energy_list = full_values_dict['Test.energy_list']
#
#         inputs_names = [
#             f'{name}.{model_name}.{energy}.{GlossaryCore.EnergyPricesValue}' for energy in energy_list if
#             energy not in ['carbon_capture', 'carbon_storage']]
#         inputs_names.extend([
#             f'{name}.{model_name}.{energy}.{GlossaryCore.EnergyProductionValue}' for energy in energy_list if
#             energy not in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.{model_name}.{energy}.{GlossaryCore.EnergyConsumptionValue}' for energy in energy_list if
#              energy not in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.CCUS.{energy}.{GlossaryCore.EnergyConsumptionValue}' for energy in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.CCUS.{energy}.{GlossaryCore.EnergyProductionValue}' for energy in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend([
#             f'{name}.CCUS.{energy}.{GlossaryCore.EnergyPricesValue}' for energy in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.{model_name}.{energy}.{GlossaryCore.CO2EmissionsValue}' for energy in energy_list if
#              energy not in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.{model_name}.syngas.syngas_ratio'])
#         inputs_names.extend(
#             [f'{name}.{GlossaryCore.CO2TaxesValue}'])
#
#         outputs_names = [f'{name}.{model_name}.{GlossaryCore.EnergyPricesValue}',
#                          f'{name}.{model_name}.{GlossaryCore.EnergyCO2EmissionsValue}']
#         # AbstractJacobianUnittest.DUMP_JACOBIAN = True
#         self.check_jacobian(location=dirname(__file__), filename=f'jacobian_energymix_output_vs_design_vars.pkl',
#                             discipline=disc, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
#                             local_data=disc.local_data,
#                             inputs=inputs_names, outputs=outputs_names, parallel=self.parallel)
#
#     def test_04_energy_mix_discipline_co2_emissions_gt(self):
#
#         self.name = 'Test'
#         self.ee = ExecutionEngine(self.name)
#         name = 'Test'
#         model_name = 'EnergyMix'
#
#         repo = 'energy_models.sos_processes.energy.MDA'
#         builder = self.ee.factory.get_builder_from_process(
#             repo, 'energy_process_v0')
#
#         self.ee.factory.set_builders_to_coupling_builder(builder)
#         self.ee.configure()
#         usecase = Study_open(execution_engine=self.ee)
#         usecase.study_name = self.name
#         values_dict = usecase.setup_usecase()
#
#         self.ee.display_treeview_nodes()
#         full_values_dict = {}
#         for dict_v in values_dict:
#             full_values_dict.update(dict_v)
#
#         full_values_dict[f'{name}.epsilon0'] = 1.0
#         full_values_dict[f'{name}.tolerance'] = 1.0e-8
#         full_values_dict[f'{name}.max_mda_iter'] = 50
#         self.ee.load_study_from_input_dict(full_values_dict)
#
#         self.ee.execute()
#
#         disc = self.ee.dm.get_disciplines_with_name(
#             f'{name}.{model_name}')[0]
#         energy_list = full_values_dict['Test.energy_list']
#
#         inputs_names = [
#             f'{name}.{model_name}.{energy}.{GlossaryCore.EnergyPricesValue}' for energy in energy_list if
#             energy not in ['carbon_capture', 'carbon_storage']]
#         inputs_names.extend([
#             f'{name}.{model_name}.{energy}.{GlossaryCore.EnergyProductionValue}' for energy in energy_list if
#             energy not in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.{model_name}.{energy}.{GlossaryCore.EnergyConsumptionValue}' for energy in energy_list if
#              energy not in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.CCUS.{energy}.{GlossaryCore.EnergyConsumptionValue}' for energy in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.CCUS.{energy}.{GlossaryCore.EnergyProductionValue}' for energy in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend([
#             f'{name}.CCUS.{energy}.{GlossaryCore.EnergyPricesValue}' for energy in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.{model_name}.{energy}.{GlossaryCore.CO2EmissionsValue}' for energy in energy_list if
#              energy not in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.{model_name}.syngas.syngas_ratio'])
#         # AbstractJacobianUnittest.DUMP_JACOBIAN = True
#         self.check_jacobian(location=dirname(__file__), filename=f'jacobian_energymix_co2_emissions.pkl',
#                             discipline=disc, step=1.0e-16, derr_approx='complex_step', threshold=1e-5,
#                             local_data=disc.local_data,
#                             inputs=inputs_names, outputs=[f'{name}.{model_name}.co2_emissions_needed_by_energy_mix',
#                                                           f'{name}.{model_name}.carbon_capture_from_energy_mix'])
#
#     def test_05_energy_mix_test_mean_price_grad(self):
#
#         self.name = 'Test'
#         self.ee = ExecutionEngine(self.name)
#         name = 'Test'
#         model_name = 'EnergyMix'
#
#         repo = 'energy_models.sos_processes.energy.MDA'
#         builder = self.ee.factory.get_builder_from_process(
#             repo, 'energy_process_v0')
#
#         self.ee.factory.set_builders_to_coupling_builder(builder)
#         self.ee.configure()
#         usecase = Study_open(execution_engine=self.ee)
#         usecase.study_name = self.name
#         values_dict = usecase.setup_usecase()
#
#         self.ee.display_treeview_nodes()
#         full_values_dict = {}
#         for dict_v in values_dict:
#             full_values_dict.update(dict_v)
#         full_values_dict[f'{name}.epsilon0'] = 1.0
#         full_values_dict[f'{name}.tolerance'] = 1.0e-8
#         full_values_dict[f'{name}.max_mda_iter'] = 50
#         self.ee.load_study_from_input_dict(full_values_dict)
#
#         self.ee.execute()
#
#         disc = self.ee.dm.get_disciplines_with_name(
#             f'{self.name}.EnergyMix')[0].mdo_discipline_wrapp.mdo_discipline
#         energy_list = full_values_dict['Test.energy_list']
#
#         inputs_names = [
#             f'{name}.{model_name}.{energy}.{GlossaryCore.EnergyPricesValue}' for energy in energy_list if
#             energy not in ['carbon_capture', 'carbon_storage']]
#         inputs_names.extend([
#             f'{name}.{model_name}.{energy}.{GlossaryCore.EnergyProductionValue}' for energy in energy_list if
#             energy not in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.{model_name}.{energy}.{GlossaryCore.EnergyConsumptionValue}' for energy in energy_list if
#              energy not in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.CCUS.{energy}.{GlossaryCore.EnergyConsumptionValue}' for energy in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.CCUS.{energy}.{GlossaryCore.EnergyProductionValue}' for energy in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend([
#             f'{name}.CCUS.{energy}.{GlossaryCore.EnergyPricesValue}' for energy in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.{model_name}.syngas.syngas_ratio'])
#         outputs_names = [f'{name}.{model_name}.energy_mean_price']
#         # AbstractJacobianUnittest.DUMP_JACOBIAN = True
#         self.check_jacobian(location=dirname(__file__),
#                             filename=f'jacobian_energy_mean_price_energy_prices_production.pkl',
#                             discipline=disc, step=1.0e-14, derr_approx='complex_step', threshold=1e-5,
#                             local_data=disc.local_data,
#                             inputs=inputs_names, outputs=outputs_names, parallel=self.parallel)
#
#     def test_06_energy_mix_all_outputs(self):
#
#         self.name = 'Test'
#         self.ee = ExecutionEngine(self.name)
#         name = 'Test'
#         model_name = 'EnergyMix'
#         func_manager_name = 'FunctionManagerDisc'
#         repo = 'energy_models.sos_processes.energy.MDA'
#         builder = self.ee.factory.get_builder_from_process(
#             repo, 'energy_process_v0')
#
#         self.ee.factory.set_builders_to_coupling_builder(builder)
#         self.ee.configure()
#         usecase = Study_open(execution_engine=self.ee)
#         usecase.study_name = self.name
#         values_dict = usecase.setup_usecase()
#
#         self.ee.display_treeview_nodes()
#         full_values_dict = {}
#         for dict_v in values_dict:
#             full_values_dict.update(dict_v)
#         full_values_dict[f'{name}.epsilon0'] = 1.0
#         full_values_dict[f'{name}.tolerance'] = 1.0e-8
#         full_values_dict[f'{name}.max_mda_iter'] = 50
#         self.ee.load_study_from_input_dict(full_values_dict)
#
#         self.ee.execute()
#
#         disc = self.ee.dm.get_disciplines_with_name(
#             f'{self.name}.EnergyMix')[0].mdo_discipline_wrapp.mdo_discipline
#         energy_list = full_values_dict['Test.energy_list']
#
#         inputs_names = [
#             f'{name}.{model_name}.{energy}.{GlossaryCore.EnergyPricesValue}' for energy in energy_list if
#             energy not in ['carbon_capture', 'carbon_storage']]
#         inputs_names.extend([
#             f'{name}.{model_name}.{energy}.{GlossaryCore.EnergyProductionValue}' for energy in energy_list if
#             energy not in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.{model_name}.{energy}.{GlossaryCore.EnergyConsumptionValue}' for energy in energy_list if
#              energy not in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.CCUS.{energy}.{GlossaryCore.EnergyConsumptionValue}' for energy in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.CCUS.{energy}.{GlossaryCore.EnergyProductionValue}' for energy in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend([
#             f'{name}.CCUS.{energy}.{GlossaryCore.EnergyPricesValue}' for energy in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.{model_name}.syngas.syngas_ratio'])
#
#         energy_mix_output = [f'{name}.{model_name}.{GlossaryCore.EnergyProductionValue}',
#                              f'{name}.{func_manager_name}.energy_production_objective',
#                              f'{name}.{model_name}.energy_mean_price',
#                              f'{name}.{model_name}.land_demand_df',
#                              f'{name}.{func_manager_name}.primary_energies_production',
#                              f'{name}.{func_manager_name}.total_prod_minus_min_prod_constraint_df',
#                              f'{name}.{model_name}.energy_prices_after_tax']
#         # AbstractJacobianUnittest.DUMP_JACOBIAN = True
#         self.check_jacobian(location=dirname(__file__), filename=f'jacobian_energy_mix_outputs.pkl',
#                             discipline=disc, step=1.0e-12, derr_approx='complex_step', threshold=1e-5,
#                             local_data=disc.local_data,
#                             inputs=inputs_names, outputs=energy_mix_output, parallel=self.parallel)
#
#     def test_07_energy_mix_co2_tax(self):
#
#         self.name = 'Test'
#         self.ee = ExecutionEngine(self.name)
#         name = 'Test'
#         model_name = 'EnergyMix'
#         func_manager_name = 'FunctionManagerDisc'
#         repo = 'energy_models.sos_processes.energy.MDA'
#         builder = self.ee.factory.get_builder_from_process(
#             repo, 'energy_process_v0')
#
#         self.ee.factory.set_builders_to_coupling_builder(builder)
#         self.ee.configure()
#         usecase = Study_open(execution_engine=self.ee)
#         usecase.study_name = self.name
#         values_dict = usecase.setup_usecase()
#
#         self.ee.display_treeview_nodes()
#         full_values_dict = {}
#         for dict_v in values_dict:
#             full_values_dict.update(dict_v)
#         full_values_dict[f'{name}.epsilon0'] = 1.0
#         full_values_dict[f'{name}.tolerance'] = 1.0e-8
#         full_values_dict[f'{name}.max_mda_iter'] = 50
#         self.ee.load_study_from_input_dict(full_values_dict)
#
#         self.ee.execute()
#
#         disc = self.ee.dm.get_disciplines_with_name(
#             f'{self.name}.EnergyMix')[0]
#         energy_list = full_values_dict['Test.energy_list']
#
#         inputs_names = [
#             f'{name}.{GlossaryCore.CO2TaxesValue}']
#
#         energy_mix_output = [f'{name}.{model_name}.energy_mean_price',
#                              f'{name}.{model_name}.energy_prices_after_tax']
#         # AbstractJacobianUnittest.DUMP_JACOBIAN = True
#         self.check_jacobian(location=dirname(__file__), filename=f'jacobian_energy_mix_co2_tax.pkl',
#                             discipline=disc, step=1.0e-12, derr_approx='complex_step', threshold=1e-5,
#                             local_data=disc.local_data,
#                             inputs=inputs_names, outputs=energy_mix_output, parallel=self.parallel)
#
#     def test_08_energy_mix_gradients_exponential_limit(self):
#         '''
#             Test on energy_mix gradients if the limit on minimum energy production is reached
#             One should check on the post-proc that the total production is saturated by the limit for
#             part of the time-range
#             This tests is performed with the exp_min options on the mixes at energy and techno level
#         '''
#         self.name = 'Test'
#         self.ee = ExecutionEngine(self.name)
#         name = 'Test'
#         model_name = 'EnergyMix'
#         func_manager_name = 'FunctionManagerDisc'
#         repo = 'energy_models.sos_processes.energy.MDA'
#         builder = self.ee.factory.get_builder_from_process(
#             repo, 'energy_process_v0')
#
#         self.ee.factory.set_builders_to_coupling_builder(builder)
#         self.ee.configure()
#         usecase = Study_open(execution_engine=self.ee)
#         usecase.study_name = self.name
#         values_dict = usecase.setup_usecase()
#
#         low_production_dict = {'Test.EnergyMix.energy_investment':
#             pd.DataFrame(
#                 {GlossaryCore.Years: [2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030,
#                            2031, 2032, 2033, 2034, 2035, 2036, 2037, 2038, 2039, 2040, 2041,
#                            2042, 2043, 2044, 2045, 2046, 2047, 2048, 2049, 2050],
#                  GlossaryCore.EnergyInvestmentsValue: 0.0})}
#         energy_list = values_dict[-1]['Test.energy_list']
#         for energy in energy_list:
#             for technology in usecase.techno_dict[energy]['value']:
#                 low_production_dict[f'Test.EnergyMix.{energy}.{technology}.{GlossaryCore.InvestLevelValue}'] = 10
#                 low_production_dict[f'Test.EnergyMix.{energy}.{technology}.initial_production'] = 0.0001
#                 low_production_dict[f'Test.EnergyMix.{energy}.{technology}.initial_age_distribution'] = pd.DataFrame({
#                     'age': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22],
#                     'distrib': 0.001})
#                 invest_before_ystart = self.ee.dm.get_value(
#                     f'Test.EnergyMix.{energy}.{technology}.{GlossaryCore.InvestmentBeforeYearStartValue}')
#                 invest_before_ystart[GlossaryCore.InvestValue] = 10
#                 low_production_dict[f'Test.EnergyMix.{energy}.{technology}.{GlossaryCore.InvestmentBeforeYearStartValue}'] = invest_before_ystart
#
#         ccs_list = values_dict[-1]['Test.ccs_list']
#         del energy
#         for energy in ccs_list:
#
#             for technology in usecase.techno_dict[energy]['value']:
#                 low_production_dict[f'Test.CCUS.{energy}.{technology}.{GlossaryCore.InvestLevelValue}'] = 10
#                 low_production_dict[f'Test.CCUS.{energy}.{technology}.initial_production'] = 0.0001
#                 low_production_dict[f'Test.CCUS.{energy}.{technology}.initial_age_distribution'] = pd.DataFrame({
#                     'age': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22],
#                     'distrib': 0.001})
#                 invest_before_ystart = self.ee.dm.get_value(
#                     f'Test.CCUS.{energy}.{technology}.{GlossaryCore.InvestmentBeforeYearStartValue}')
#                 invest_before_ystart[GlossaryCore.InvestValue] = 10
#                 low_production_dict[f'Test.CCUS.{energy}.{technology}.{GlossaryCore.InvestmentBeforeYearStartValue}'] = invest_before_ystart
#
#         low_production_dict['Test.minimum_energy_production'] = 5e3
#
#         values_dict.append(low_production_dict)
#
#         self.ee.display_treeview_nodes()
#         full_values_dict = {}
#         for dict_v in values_dict:
#             full_values_dict.update(dict_v)
#
#         full_values_dict[f'{name}.epsilon0'] = 1.0
#         full_values_dict[f'{name}.tolerance'] = 1.0e-12
#         full_values_dict[f'{name}.sub_mda_class'] = 'GSorNewtonMDA'
#         full_values_dict[f'{name}.max_mda_iter'] = 50
#
#         self.ee.load_study_from_input_dict(full_values_dict)
#
#         self.ee.execute()
#
#         ppf = PostProcessingFactory()
#
#         disc = self.ee.dm.get_disciplines_with_name(
#             f'{self.name}.EnergyMix')[0]
#         filters = ppf.get_post_processing_filters_by_discipline(disc)
#         graph_list = ppf.get_post_processing_by_discipline(
#             disc, filters, as_json=False)
#
#         disc = self.ee.dm.get_disciplines_with_name(
#             f'{self.name}.EnergyMix')[0]
#         energy_list = full_values_dict['Test.energy_list']
#
#         inputs_names = [
#             f'{name}.{GlossaryCore.CO2TaxesValue}']
#         inputs_names.extend([
#             f'{name}.{model_name}.{energy}.{GlossaryCore.EnergyPricesValue}' for energy in energy_list])
#         inputs_names = [
#             f'{name}.{model_name}.{energy}.{GlossaryCore.EnergyProductionValue}' for energy in energy_list if
#             energy not in ['carbon_capture', 'carbon_storage']]
#         inputs_names.extend(
#             [f'{name}.{model_name}.{energy}.{GlossaryCore.EnergyConsumptionValue}' for energy in energy_list if
#              energy not in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.CCUS.{energy}.{GlossaryCore.EnergyConsumptionValue}' for energy in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.CCUS.{energy}.{GlossaryCore.EnergyProductionValue}' for energy in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.{model_name}.syngas.syngas_ratio'])
#         energy_mix_output = [f'{name}.{model_name}.{GlossaryCore.EnergyProductionValue}',
#                              f'{name}.{model_name}.co2_emissions_Gt',
#                              f'{name}.{func_manager_name}.energy_production_objective',
#                              f'{name}.{func_manager_name}.co2_emissions_objective',
#                              f'{name}.{model_name}.energy_mean_price',
#                              f'{name}.{model_name}.land_demand_df',
#                              f'{name}.{func_manager_name}.primary_energies_production',
#                              f'{name}.{func_manager_name}.total_prod_minus_min_prod_constraint_df',
#                              f'{name}.{model_name}.energy_prices_after_tax',
#                              f'{name}.{func_manager_name}.co2_emissions_objective',
#                              f'{name}.{func_manager_name}.energy_production_objective',
#                              f'{name}.{func_manager_name}.primary_energies_production',
#                              f'{name}.{func_manager_name}.carbon_storage_constraint']
#
#         self.check_jacobian(location=dirname(__file__), filename=f'jacobian_energy_mix_outputs_limit.pkl',
#                             discipline=disc, step=1.0e-16, derr_approx='complex_step', threshold=1e-3,
#                             local_data=disc.local_data,
#                             inputs=inputs_names, outputs=energy_mix_output)
#
#     def _test_09_energy_mix_gradients_cutoff(self):
#         '''
#             Same test as test 08 except:
#             this test is performed with the cutoffs options on the mixes at energy and techno level
#         '''
#
#         self.name = 'Test'
#         self.ee = ExecutionEngine(self.name)
#         name = 'Test'
#         model_name = 'EnergyMix'
#         func_manager_name = 'FunctionManagerDisc'
#         repo = 'energy_models.sos_processes.energy.MDA'
#         builder = self.ee.factory.get_builder_from_process(
#             repo, 'energy_process_v0')
#
#         self.ee.factory.set_builders_to_coupling_builder(builder)
#         self.ee.configure()
#         usecase = Study_open(execution_engine=self.ee)
#         usecase.study_name = self.name
#         values_dict = usecase.setup_usecase()
#
#         low_production_dict = {'Test.EnergyMix.energy_investment':
#             pd.DataFrame(
#                 {GlossaryCore.Years: [2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030,
#                            2031, 2032, 2033, 2034, 2035, 2036, 2037, 2038, 2039, 2040, 2041,
#                            2042, 2043, 2044, 2045, 2046, 2047, 2048, 2049, 2050],
#                  GlossaryCore.EnergyInvestmentsValue: 0.0})}
#         energy_list = values_dict[-1]['Test.energy_list']
#         for energy_dict in values_dict:
#             for key in energy_dict.keys():
#                 if GlossaryCore.techno_list in key:
#                     try:
#                         energy = [
#                             energy for energy in energy_list if energy in key][0]
#                         technologies_list = energy_dict[key]
#                     except:
#                         # energy is CCS
#                         continue
#             for technology in technologies_list:
#                 low_production_dict[f'Test.EnergyMix.{energy}.{technology}.{GlossaryCore.InvestLevelValue}'] = 10
#                 low_production_dict[f'Test.EnergyMix.{energy}.{technology}.initial_production'] = 0.0001
#                 low_production_dict[f'Test.EnergyMix.{energy}.{technology}.initial_age_distribution'] = pd.DataFrame({
#                     'age': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22],
#                     'distrib': 0.001})
#                 invest_before_ystart = self.ee.dm.get_value(
#                     f'Test.EnergyMix.{energy}.{technology}.{GlossaryCore.InvestmentBeforeYearStartValue}')
#                 invest_before_ystart[GlossaryCore.InvestValue] = 10
#                 low_production_dict[f'Test.EnergyMix.{energy}.{technology}.{GlossaryCore.InvestmentBeforeYearStartValue}'] = invest_before_ystart
#             low_production_dict[f'Test.EnergyMix.{energy}.exp_min'] = False
#
#         low_production_dict[f'Test.EnergyMix.exp_min'] = False
#
#         ccs_list = values_dict[-1]['Test.ccs_list']
#         del energy
#         technologies_list = []
#         for energy_dict in values_dict:
#             for key in energy_dict.keys():
#                 if GlossaryCore.techno_list in key:
#                     try:
#                         energy = [
#                             energy for energy in ccs_list if energy in key][0]
#                         technologies_list = energy_dict[key]
#                     except:
#                         # energy is CCS
#                         continue
#             for technology in technologies_list:
#                 low_production_dict[f'Test.CCUS.{energy}.{technology}.{GlossaryCore.InvestLevelValue}'] = 10
#                 low_production_dict[f'Test.CCUS.{energy}.{technology}.initial_production'] = 0.0001
#                 low_production_dict[f'Test.CCUS.{energy}.{technology}.initial_age_distribution'] = pd.DataFrame({
#                     'age': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22],
#                     'distrib': 0.001})
#                 invest_before_ystart = self.ee.dm.get_value(
#                     f'Test.CCUS.{energy}.{technology}.{GlossaryCore.InvestmentBeforeYearStartValue}')
#                 invest_before_ystart[GlossaryCore.InvestValue] = 10
#                 low_production_dict[f'Test.CCUS.{energy}.{technology}.{GlossaryCore.InvestmentBeforeYearStartValue}'] = invest_before_ystart
#
#         low_production_dict['Test.minimum_energy_production'] = 5e3
#         values_dict.append(low_production_dict)
#
#         self.ee.display_treeview_nodes()
#         full_values_dict = {}
#         for dict_v in values_dict:
#             full_values_dict.update(dict_v)
#
#         full_values_dict[f'{name}.epsilon0'] = 1.0
#         full_values_dict[f'{name}.tolerance'] = 1.0e-8
#         full_values_dict[f'{name}.max_mda_iter'] = 50
#         self.ee.load_study_from_input_dict(full_values_dict)
#
#         self.ee.execute()
#
#         ppf = PostProcessingFactory()
#
#         disc = self.ee.dm.get_disciplines_with_name(
#             f'{self.name}.EnergyMix')[0]
#         filters = ppf.get_post_processing_filters_by_discipline(disc)
#         graph_list = ppf.get_post_processing_by_discipline(
#             disc, filters, as_json=False)
#
#         #         for graph in graph_list:
#         #             try:
#         #                 if graph.chart_name == 'Net Energies Total Production and Limit':
#         #                     graph.to_plotly().show()
#         #             except:
#         #                 pass
#
#         disc = self.ee.dm.get_disciplines_with_name(
#             f'{self.name}.EnergyMix')[0]
#         energy_list = full_values_dict['Test.energy_list']
#
#         inputs_names = [
#             f'{name}.{GlossaryCore.CO2TaxesValue}']
#         inputs_names.extend([
#             f'{name}.{model_name}.{energy}.{GlossaryCore.EnergyPricesValue}' for energy in energy_list])
#         inputs_names = [
#             f'{name}.{model_name}.{energy}.{GlossaryCore.EnergyProductionValue}' for energy in energy_list if
#             energy not in ['carbon_capture', 'carbon_storage']]
#         inputs_names.extend(
#             [f'{name}.{model_name}.{energy}.{GlossaryCore.EnergyConsumptionValue}' for energy in energy_list if
#              energy not in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.CCUS.{energy}.{GlossaryCore.EnergyConsumptionValue}' for energy in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.CCUS.{energy}.{GlossaryCore.EnergyProductionValue}' for energy in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.{model_name}.syngas.syngas_ratio'])
#         energy_mix_output = [f'{name}.{model_name}.{GlossaryCore.EnergyProductionValue}',
#                              f'{name}.{model_name}.co2_emissions_Gt',
#                              f'{name}.{func_manager_name}.energy_production_objective',
#                              f'{name}.{func_manager_name}.co2_emissions_objective',
#                              f'{name}.{model_name}.energy_mean_price',
#                              f'{name}.{model_name}.land_demand_df',
#                              f'{name}.{func_manager_name}.primary_energies_production',
#                              f'{name}.{func_manager_name}.total_prod_minus_min_prod_constraint_df',
#                              f'{name}.{model_name}.energy_prices_after_tax',
#                              f'{name}.{func_manager_name}.co2_emissions_objective',
#                              f'{name}.{func_manager_name}.energy_production_objective',
#                              f'{name}.{func_manager_name}.primary_energies_production',
#                              f'{name}.{func_manager_name}.carbon_storage_constraint']
#
#         self.check_jacobian(location=dirname(__file__), filename=f'jacobian_energy_mix_outputs_cutoff.pkl',
#                             discipline=disc, step=1.0e-12, derr_approx='complex_step', threshold=1e-5,
#                             local_data=disc.local_data,
#                             inputs=inputs_names, outputs=energy_mix_output, parallel=self.parallel)
#
#     def test_10_energy_mix_demand_dataframe(self):
#         self.name = 'Test'
#         self.ee = ExecutionEngine(self.name)
#         name = 'Test'
#         model_name = 'EnergyMix'
#         func_manager_name = 'FunctionManagerDisc'
#         repo = 'energy_models.sos_processes.energy.MDA'
#         builder = self.ee.factory.get_builder_from_process(
#             repo, 'energy_process_v0')
#
#         self.ee.factory.set_builders_to_coupling_builder(builder)
#         self.ee.configure()
#         usecase = Study_open(execution_engine=self.ee)
#         usecase.study_name = self.name
#         values_dict = usecase.setup_usecase()
#
#         self.ee.display_treeview_nodes()
#         full_values_dict = {}
#         for dict_v in values_dict:
#             full_values_dict.update(dict_v)
#
#         full_values_dict[f'{name}.epsilon0'] = 1.0
#         full_values_dict[f'{name}.tolerance'] = 1.0e-8
#         full_values_dict[f'{name}.max_mda_iter'] = 50
#         self.ee.load_study_from_input_dict(full_values_dict)
#
#         self.ee.execute()
#
#         disc = self.ee.dm.get_disciplines_with_name(
#             f'{self.name}.EnergyMix')[0]
#         energy_list = full_values_dict['Test.energy_list']
#
#         inputs_names = [
#             f'{name}.{model_name}.{energy}.{GlossaryCore.EnergyConsumptionValue}' for energy in energy_list]
#
#         energy_mix_output = [f'{name}.{model_name}.resources_demand']
#         # AbstractJacobianUnittest.DUMP_JACOBIAN = True
#         self.check_jacobian(location=dirname(__file__), filename=f'jacobian_energy_mix_demand_df.pkl',
#                             discipline=disc, step=1.0e-12, derr_approx='complex_step', threshold=1e-5,
#                             local_data=disc.local_data,
#                             inputs=inputs_names, outputs=energy_mix_output, parallel=self.parallel)
#
#     def test_11_energy_mix_detailed_co2_emissions(self):
#
#         self.name = 'Test'
#         self.ee = ExecutionEngine(self.name)
#         name = 'Test'
#         model_name = 'EnergyMix'
#         func_manager_name = 'FunctionManagerDisc'
#
#         repo = 'energy_models.sos_processes.energy.MDA'
#         builder = self.ee.factory.get_builder_from_process(
#             repo, 'energy_process_v0')
#
#         self.ee.factory.set_builders_to_coupling_builder(builder)
#         self.ee.configure()
#         usecase = Study_open(execution_engine=self.ee)
#         usecase.study_name = self.name
#         values_dict = usecase.setup_usecase()
#
#         self.ee.display_treeview_nodes()
#         full_values_dict = {}
#         for dict_v in values_dict:
#             full_values_dict.update(dict_v)
#
#         full_values_dict[f'{name}.epsilon0'] = 1.0
#         full_values_dict[f'{name}.tolerance'] = 1.0e-12
#         full_values_dict[f'{name}.max_mda_iter'] = 50
#         # full_values_dict[f'{name}.sub_mda_class'] = 'MDANewtonRaphson'
#         self.ee.load_study_from_input_dict(full_values_dict)
#
#         self.ee.execute()
#
#         disc = self.ee.dm.get_disciplines_with_name(
#             f'{name}.{model_name}')[0]
#         energy_list = full_values_dict['Test.energy_list']
#
#         inputs_names = [
#             f'{name}.{model_name}.{energy}.{GlossaryCore.EnergyProductionValue}' for energy in energy_list if
#             energy not in ['carbon_capture', 'carbon_storage']]
#         inputs_names.extend(
#             [f'{name}.{model_name}.{energy}.{GlossaryCore.EnergyConsumptionValue}' for energy in energy_list if
#              energy not in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.CCUS.{energy}.{GlossaryCore.EnergyConsumptionValue}' for energy in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.CCUS.{energy}.{GlossaryCore.EnergyProductionValue}' for energy in ['carbon_capture', 'carbon_storage']])
#         # AbstractJacobianUnittest.DUMP_JACOBIAN = True
#
#         self.check_jacobian(location=dirname(__file__), filename=f'jacobian_energymix_detailed_co2_emissions.pkl',
#                             discipline=disc, step=1.0e-16, derr_approx='complex_step', local_data=disc.local_data,
#                             inputs=inputs_names, outputs=[f'{name}.{model_name}.{GlossaryCore.EnergyProductionValue}',
#                                                           f'{name}.{model_name}.{GlossaryCore.EnergyCO2EmissionsValue}',
#                                                           f'{name}.{model_name}.energy_mean_price',
#                                                           f'{name}.{model_name}.land_demand_df',
#                                                           f'{name}.{func_manager_name}.primary_energies_production',
#                                                           f'{name}.{func_manager_name}.total_prod_minus_min_prod_constraint_df',
#                                                           f'{name}.{model_name}.energy_prices_after_tax',
#                                                           f'{name}.{func_manager_name}.energy_production_objective',
#                                                           f'{name}.{func_manager_name}.primary_energies_production',
#                                                           f'{name}.{func_manager_name}.ratio_objective',
#                                                           f'{name}.{model_name}.co2_emissions_needed_by_energy_mix'],
#                             parallel=self.parallel)
#
#     def test_13_energy_mix_co2_per_use_gradients(self):
#         '''
#         Test CO2 per use gradients
#         '''
#         self.name = 'Test'
#         self.ee = ExecutionEngine(self.name)
#         name = 'Test'
#         model_name = 'EnergyMix'
#         func_manager_name = 'FunctionManagerDisc'
#         repo = 'energy_models.sos_processes.energy.MDA'
#         builder = self.ee.factory.get_builder_from_process(
#             repo, 'energy_process_v0')
#
#         self.ee.factory.set_builders_to_coupling_builder(builder)
#         self.ee.configure()
#         usecase = Study_open(execution_engine=self.ee)
#         usecase.study_name = self.name
#         values_dict = usecase.setup_usecase()
#
#         self.ee.display_treeview_nodes()
#         full_values_dict = {}
#         for dict_v in values_dict:
#             full_values_dict.update(dict_v)
#
#         full_values_dict[f'{name}.epsilon0'] = 1.0
#         full_values_dict[f'{name}.tolerance'] = 1.0e-8
#         full_values_dict[f'{name}.max_mda_iter'] = 50
#
#         # full_values_dict[f'{name}.sub_mda_class'] = 'MDANewtonRaphson'
#         self.ee.load_study_from_input_dict(full_values_dict)
#
#         self.ee.execute()
#
#         disc = self.ee.dm.get_disciplines_with_name(
#             f'{name}.{model_name}')[0]
#         energy_list = full_values_dict['Test.energy_list']
#
#         inputs_names = [
#             f'{name}.{model_name}.{energy}.CO2_per_use' for energy in energy_list if
#             energy not in ['carbon_capture', 'carbon_storage']]
#
#         self.check_jacobian(location=dirname(__file__), filename=f'jacobian_energymix_mix_co2_per_use_gradients.pkl',
#                             discipline=disc, step=1.0e-16, derr_approx='complex_step',
#                             inputs=inputs_names, outputs=[f'{name}.{model_name}.{GlossaryCore.EnergyProductionValue}',
#                                                           f'{name}.{model_name}.co2_emissions_Gt',
#                                                           f'{name}.{model_name}.{GlossaryCore.EnergyCO2EmissionsValue}',
#                                                           f'{name}.{model_name}.energy_mean_price',
#                                                           f'{name}.{model_name}.land_demand_df',
#                                                           f'{name}.{func_manager_name}.primary_energies_production',
#                                                           f'{name}.{func_manager_name}.total_prod_minus_min_prod_constraint_df',
#                                                           f'{name}.{model_name}.energy_prices_after_tax',
#                                                           f'{name}.{func_manager_name}.energy_production_objective',
#                                                           f'{name}.{func_manager_name}.primary_energies_production', ],
#                             parallel=self.parallel)
#
#     def test_14_energy_mix_with_losses(self):
#         '''
#         Test CO2 per use gradients
#         '''
#         self.name = 'Test'
#         self.ee = ExecutionEngine(self.name)
#         name = 'Test'
#         model_name = 'EnergyMix'
#         func_manager_name = 'FunctionManagerDisc'
#         repo = 'energy_models.sos_processes.energy.MDA'
#         builder = self.ee.factory.get_builder_from_process(
#             repo, 'energy_process_v0')
#
#         self.ee.factory.set_builders_to_coupling_builder(builder)
#         self.ee.configure()
#         usecase = Study_open(execution_engine=self.ee)
#         usecase.study_name = self.name
#         values_dict = usecase.setup_usecase()
#
#         self.ee.display_treeview_nodes()
#         full_values_dict = {}
#         for dict_v in values_dict:
#             full_values_dict.update(dict_v)
#
#         full_values_dict[f'{name}.epsilon0'] = 1.0
#         full_values_dict[f'{name}.tolerance'] = 1.0e-8
#         full_values_dict[f'{name}.max_mda_iter'] = 50
#         # full_values_dict[f'{name}.sub_mda_class'] = 'MDANewtonRaphson'
#         self.ee.load_study_from_input_dict(full_values_dict)
#
#         self.ee.execute()
#
#         disc = self.ee.dm.get_disciplines_with_name(
#             f'{name}.{model_name}')[0]
#         energy_list = full_values_dict['Test.energy_list']
#
#         inputs_names = [
#             f'{name}.{model_name}.{energy}.{GlossaryCore.EnergyProductionValue}' for energy in energy_list if
#             energy not in ['carbon_capture', 'carbon_storage']]
#         inputs_names.extend(
#             [f'{name}.{model_name}.{energy}.{GlossaryCore.EnergyConsumptionValue}' for energy in energy_list if
#              energy not in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.CCUS.{energy}.{GlossaryCore.EnergyConsumptionValue}' for energy in ['carbon_capture', 'carbon_storage']])
#         inputs_names.extend(
#             [f'{name}.CCUS.{energy}.{GlossaryCore.EnergyProductionValue}' for energy in ['carbon_capture', 'carbon_storage']])
#
#         self.check_jacobian(location=dirname(__file__), filename=f'jacobian_energy_mix_with_losses.pkl',
#                             discipline=disc, step=1.0e-16, derr_approx='complex_step',
#                             inputs=inputs_names, outputs=[f'{name}.{model_name}.{GlossaryCore.EnergyProductionValue}',
#                                                           f'{name}.{model_name}.{GlossaryCore.EnergyProductionDetailedValue}',
#                                                           f'{name}.{model_name}.co2_emissions_needed_by_energy_mix',
#                                                           f'{name}.{model_name}.{GlossaryCore.EnergyCO2EmissionsValue}',
#                                                           f'{name}.{model_name}.energy_mean_price',
#                                                           f'{name}.{model_name}.land_demand_df',
#                                                           f'{name}.{func_manager_name}.primary_energies_production',
#                                                           f'{name}.{func_manager_name}.ratio_objective',
#                                                           f'{name}.{func_manager_name}.total_prod_minus_min_prod_constraint_df',
#                                                           f'{name}.{model_name}.energy_prices_after_tax',
#                                                           f'{name}.{func_manager_name}.energy_production_objective',
#                                                           f'{name}.{func_manager_name}.primary_energies_production', ])
#
#     def test_15_energy_mix_agriculture_mix(self):
#
#         name = 'Test'
#         model_name = 'EnergyMix'
#         agriculture_mix = 'AgricultureMix'
#         self.ee = ExecutionEngine(name)
#         ns_dict = {'ns_public': f'{name}',
#                    'ns_hydrogen': f'{name}',
#                    'ns_methane': f'{name}',
#                    'ns_energy_study': f'{name}',
#                    'ns_energy_mix': f'{name}.{model_name}',
#                    'ns_functions': f'{name}.{model_name}',
#                    'ns_resource': f'{name}.{model_name}.resource',
#                    'ns_ccs': f'{name}.{model_name}',
#                    'ns_ref': f'{name}.{model_name}',
#                    'ns_energy': f'{name}.{model_name}',
#                    'ns_witness': f'{name}'}
#         self.ee.ns_manager.add_ns_def(ns_dict)
#
#         mod_path = 'energy_models.core.energy_mix.energy_mix_disc.Energy_Mix_Discipline'
#         builder = self.ee.factory.get_builder_from_module(
#             model_name, mod_path)
#
#         self.ee.factory.set_builders_to_coupling_builder(builder)
#
#         self.ee.configure()
#         self.ee.display_treeview_nodes()
#
#         inputs_dict = {f'{name}.{model_name}.{GlossaryCore.YearStart}': self.year_start,
#                        f'{name}.{model_name}.{GlossaryCore.YearEnd}': self.year_end,
#                        f'{name}.{GlossaryCore.energy_list}': ['methane', 'biomass_dry'],
#                        f'{name}.{GlossaryCore.ccs_list}': [],
#                        f'{name}.is_dev': True,
#                        f'{name}.{model_name}.{GlossaryCore.EnergyPricesValue}': pd.DataFrame(
#                            {'hydrogen.gaseous_hydrogen': self.prices_hydro['hydrogen.gaseous_hydrogen'],
#                             'methane': self.cost_details['methane']}),
#                        f'{name}.{agriculture_mix}.{GlossaryCore.EnergyConsumptionValue}': self.energy_consumption_biomass,
#                        f'{name}.{agriculture_mix}.{GlossaryCore.EnergyConsumptionWithoutRatioValue}': self.energy_consumption_biomass,
#                        f'{name}.{agriculture_mix}.{GlossaryCore.EnergyProductionValue}': self.energy_production_biomass,
#                        f'{name}.{agriculture_mix}.{GlossaryCore.EnergyPricesValue}': self.energy_prices_biomass,
#                        f'{name}.{agriculture_mix}.CO2_per_use': self.CO2_per_use_biomass,
#                        f'{name}.{agriculture_mix}.{GlossaryCore.CO2EmissionsValue}': self.CO2_emissions_biomass,
#                        f'{name}.{agriculture_mix}.{GlossaryCore.LandUseRequiredValue}': self.land_use_required_biomass,
#                        f'{name}.{model_name}.methane.{GlossaryCore.EnergyConsumptionValue}': self.consumption,
#                        f'{name}.{model_name}.methane.{GlossaryCore.EnergyConsumptionWithoutRatioValue}': self.consumption,
#                        f'{name}.{model_name}.methane.{GlossaryCore.EnergyProductionValue}': self.production,
#                        f'{name}.{model_name}.methane.{GlossaryCore.EnergyProcductionWithoutRatioValue}': self.production,
#                        f'{name}.{model_name}.methane.{GlossaryCore.EnergyPricesValue}': self.cost_details,
#                        f'{name}.{model_name}.methane.CO2_per_use': pd.DataFrame(
#                            {GlossaryCore.Years: self.years, GlossaryCore.CO2Tax: 0.0, 'CO2_per_use': 0.0}),
#                        f'{name}.{model_name}.methane.{GlossaryCore.CO2EmissionsValue}': pd.DataFrame(
#                            {GlossaryCore.Years: self.years, 'methane': 0.0}),
#                        f'{name}.{model_name}.methane.{GlossaryCore.LandUseRequiredValue}': self.land_use_required_methane,
#                        f'{name}.{GlossaryCore.CO2TaxesValue}': self.co2_taxes,
#                        f'{name}.{model_name}.hydrogen.gaseous_hydrogen.loss_percentage': 1.0,
#                        f'{name}.{model_name}.methane.loss_percentage': 2.0,
#                        }
#
#         self.ee.load_study_from_input_dict(inputs_dict)
#
#         disc = self.ee.dm.get_disciplines_with_name(
#             f'{name}.EnergyMix')[0]
#
#         # AbstractJacobianUnittest.DUMP_JACOBIAN = True
#
#         self.check_jacobian(location=dirname(__file__), filename=f'jacobian_energy_mix_agriculture_mix.pkl',
#                             discipline=disc, step=1.0e-16, derr_approx='complex_step',
#                             inputs=[f'{name}.{model_name}.methane.{GlossaryCore.EnergyConsumptionValue}',
#                                     f'{name}.{model_name}.methane.{GlossaryCore.EnergyConsumptionWithoutRatioValue}',
#                                     f'{name}.{model_name}.methane.{GlossaryCore.EnergyProductionValue}',
#                                     f'{name}.{model_name}.methane.{GlossaryCore.EnergyPricesValue}',
#                                     f'{name}.{model_name}.methane.CO2_per_use',
#                                     f'{name}.{model_name}.methane.{GlossaryCore.CO2EmissionsValue}',
#                                     f'{name}.{model_name}.methane.{GlossaryCore.LandUseRequiredValue}',
#                                     f'{name}.AgricultureMix.{GlossaryCore.EnergyConsumptionValue}',
#                                     f'{name}.AgricultureMix.{GlossaryCore.EnergyConsumptionWithoutRatioValue}',
#                                     f'{name}.AgricultureMix.{GlossaryCore.EnergyProductionValue}',
#                                     f'{name}.AgricultureMix.{GlossaryCore.EnergyPricesValue}',
#                                     f'{name}.AgricultureMix.CO2_per_use',
#                                     f'{name}.AgricultureMix.{GlossaryCore.CO2EmissionsValue}',
#                                     f'{name}.AgricultureMix.{GlossaryCore.LandUseRequiredValue}'],
#                             outputs=[f'{name}.{model_name}.{GlossaryCore.EnergyProductionValue}',
#                                      f'{name}.{model_name}.{GlossaryCore.EnergyCO2EmissionsValue}',
#                                      f'{name}.{model_name}.energy_mean_price',
#                                      f'{name}.{model_name}.land_demand_df',
#                                      f'{name}.{model_name}.energy_prices_after_tax',
#                                      f'{name}.{model_name}.co2_emissions_needed_by_energy_mix'])
#
#
# if '__main__' == __name__:
#     # AbstractJacobianUnittest.DUMP_JACOBIAN = True
#     cls = EnergyMixJacobianTestCase()
#     cls.setUp()
#     # cls.test_04_energy_mix_discipline_co2_emissions_gt()
#     cls.test_10_energy_mix_demand_dataframe()
