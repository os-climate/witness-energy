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
import unittest

import numpy as np
import pandas as pd
from pandas.util.testing import assert_frame_equal
from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.energy_models.gaseous_hydrogen import GaseousHydrogen
from energy_models.core.stream_type.energy_models.methane import Methane
from sos_trades_core.execution_engine.execution_engine import ExecutionEngine
from sos_trades_core.tools.post_processing.post_processing_factory import PostProcessingFactory

import scipy.interpolate as sc


class EnergyMixTestCase(unittest.TestCase):
    """
    ENergyMix test class
    """

    def setUp(self):
        '''
        Initialize third data needed for testing
        '''
        self.year_start = 2020
        self.year_end = 2050
        self.years = np.arange(self.year_start, self.year_end + 1)
        self.energy_list = ['hydrogen.gaseous_hydrogen', 'methane']
        self.consumption_hydro = pd.DataFrame({'electricity (TWh)': np.array([5.79262302e+09, 5.96550630e+09, 6.13351314e+09, 6.29771389e+09,
                                                                              6.45887954e+09, 6.61758183e+09, 6.81571547e+09, 7.00833095e+09,
                                                                              7.19662898e+09, 7.38146567e+09, 7.56347051e+09, 7.58525158e+09,
                                                                              7.60184181e+09, 7.61413788e+09, 7.62282699e+09, 7.62844682e+09,
                                                                              7.63143167e+09, 7.63212186e+09, 7.63080121e+09, 7.62770511e+09,
                                                                              7.62303081e+09, 7.61658967e+09, 7.60887892e+09, 7.60002116e+09,
                                                                              7.59012249e+09, 7.57927528e+09, 7.56756653e+09, 7.55506132e+09,
                                                                              7.54182260e+09, 7.52790631e+09, 7.51336234e+09]) / 1.0e9,
                                               'methane (TWh)': np.array([1.30334018e+10, 1.34223892e+10, 1.38004046e+10, 1.41698563e+10,
                                                                          1.45324790e+10, 1.48895591e+10, 1.53353598e+10, 1.57687446e+10,
                                                                          1.61924152e+10, 1.66082977e+10, 1.70178086e+10, 1.70668161e+10,
                                                                          1.71041441e+10, 1.71318102e+10, 1.71513607e+10, 1.71640053e+10,
                                                                          1.71707213e+10, 1.71722742e+10, 1.71693027e+10, 1.71623365e+10,
                                                                          1.71518193e+10, 1.71373267e+10, 1.71199776e+10, 1.71000476e+10,
                                                                          1.70777756e+10, 1.70533694e+10, 1.70270247e+10, 1.69988880e+10,
                                                                          1.69691008e+10, 1.69377892e+10, 1.69050653e+10]) / 1.0e9,
                                               'water (Mt)': np.array([8.23100419e+09, 8.47666200e+09, 8.71539063e+09, 8.94871102e+09,
                                                                       9.17771870e+09, 9.40322607e+09, 9.68476326e+09, 9.95845946e+09,
                                                                       1.02260208e+10, 1.04886637e+10, 1.07472828e+10, 1.07782325e+10,
                                                                       1.08018063e+10, 1.08192784e+10, 1.08316251e+10, 1.08396106e+10,
                                                                       1.08438519e+10, 1.08448326e+10, 1.08429560e+10, 1.08385567e+10,
                                                                       1.08319147e+10, 1.08227622e+10, 1.08118056e+10, 1.07992193e+10,
                                                                       1.07851538e+10, 1.07697405e+10, 1.07531030e+10, 1.07353338e+10,
                                                                       1.07165222e+10, 1.06967480e+10, 1.06760818e+10]) / 1.0e9})

        self.production_hydro = pd.DataFrame({'hydrogen.gaseous_hydrogen': np.array([2.89631151e+10, 2.98275315e+10, 3.06675657e+10, 3.14885694e+10,
                                                                                     3.22943977e+10, 3.30879091e+10, 3.40785773e+10, 3.50416548e+10,
                                                                                     3.59831449e+10, 3.69073283e+10, 3.78173526e+10, 3.79262579e+10,
                                                                                     3.80092091e+10, 3.80706894e+10, 3.81141349e+10, 3.81422341e+10,
                                                                                     3.81571584e+10, 3.81606093e+10, 3.81540060e+10, 3.81385255e+10,
                                                                                     3.81151541e+10, 3.80829483e+10, 3.80443946e+10, 3.80001058e+10,
                                                                                     3.79506125e+10, 3.78963764e+10, 3.78378327e+10, 3.77753066e+10,
                                                                                     3.77091130e+10, 3.76395315e+10, 3.75668117e+10]) / 1.0e9,
                                              'hydrogen SMR (TWh)': np.array([1.44815575e+10, 1.49137658e+10, 1.53337829e+10, 1.57442847e+10,
                                                                              1.61471989e+10, 1.65439546e+10, 1.70392887e+10, 1.75208274e+10,
                                                                              1.79915724e+10, 1.84536642e+10, 1.89086763e+10, 1.89631289e+10,
                                                                              1.90046045e+10, 1.90353447e+10, 1.90570675e+10, 1.90711170e+10,
                                                                              1.90785792e+10, 1.90803046e+10, 1.90770030e+10, 1.90692628e+10,
                                                                              1.90575770e+10, 1.90414742e+10, 1.90221973e+10, 1.90000529e+10,
                                                                              1.89753062e+10, 1.89481882e+10, 1.89189163e+10, 1.88876533e+10,
                                                                              1.88545565e+10, 1.88197658e+10, 1.87834058e+10]) / 1.0e9,
                                              'CO2 (Mt)': np.array([1.45250457e+09, 1.49585518e+09, 1.53798303e+09, 1.57915649e+09,
                                                                    1.61956889e+09, 1.65936361e+09, 1.70904577e+09, 1.75734425e+09,
                                                                    1.80456012e+09, 1.85090806e+09, 1.89654591e+09, 1.90200753e+09,
                                                                    1.90616754e+09, 1.90925079e+09, 1.91142959e+09, 1.91283877e+09,
                                                                    1.91358722e+09, 1.91376029e+09, 1.91342913e+09, 1.91265278e+09,
                                                                    1.91148070e+09, 1.90986558e+09, 1.90793210e+09, 1.90571101e+09,
                                                                    1.90322891e+09, 1.90050897e+09, 1.89757299e+09, 1.89443730e+09,
                                                                    1.89111768e+09, 1.88762816e+09, 1.88398125e+09]) / 1.0e9,
                                              'hydrogen Electrolysis (TWh)': np.array([1.44815575e+10, 1.49137658e+10, 1.53337829e+10, 1.57442847e+10,
                                                                                       1.61471989e+10, 1.65439546e+10, 1.70392887e+10, 1.75208274e+10,
                                                                                       1.79915724e+10, 1.84536642e+10, 1.89086763e+10, 1.89631289e+10,
                                                                                       1.90046045e+10, 1.90353447e+10, 1.90570675e+10, 1.90711170e+10,
                                                                                       1.90785792e+10, 1.90803046e+10, 1.90770030e+10, 1.90692628e+10,
                                                                                       1.90575770e+10, 1.90414742e+10, 1.90221973e+10, 1.90000529e+10,
                                                                                       1.89753062e+10, 1.89481882e+10, 1.89189163e+10, 1.88876533e+10,
                                                                                       1.88545565e+10, 1.88197658e+10, 1.87834058e+10]) / 1.0e9,
                                              'O2 (Mt)': np.array([1.45250457e+09, 1.49585518e+09, 1.53798303e+09, 1.57915649e+09,
                                                                   1.61956889e+09, 1.65936361e+09, 1.70904577e+09, 1.75734425e+09,
                                                                   1.80456012e+09, 1.85090806e+09, 1.89654591e+09, 1.90200753e+09,
                                                                   1.90616754e+09, 1.90925079e+09, 1.91142959e+09, 1.91283877e+09,
                                                                   1.91358722e+09, 1.91376029e+09, 1.91342913e+09, 1.91265278e+09,
                                                                   1.91148070e+09, 1.90986558e+09, 1.90793210e+09, 1.90571101e+09,
                                                                   1.90322891e+09, 1.90050897e+09, 1.89757299e+09, 1.89443730e+09,
                                                                   1.89111768e+09, 1.88762816e+09, 1.88398125e+09]) / 1.0e9})

        self.prices_hydro = pd.DataFrame({'hydrogen.gaseous_hydrogen': np.array([0.076815, 0.07549102, 0.07433427, 0.07330841, 0.07238752,
                                                                                 0.07155253, 0.07050461, 0.06960523, 0.068821, 0.06812833,
                                                                                 0.06750997, 0.066893, 0.06635812, 0.06589033, 0.06547834,
                                                                                 0.06511344, 0.06478879, 0.06449895, 0.06423948, 0.06400678,
                                                                                 0.06379784, 0.06361016, 0.06344163, 0.06329045, 0.06315508,
                                                                                 0.0630342, 0.06292668, 0.06283151, 0.06274783, 0.06267487,
                                                                                 0.06261198]) * 1000.0,
                                          'hydrogen.gaseous_hydrogen_wotaxes': np.array([0.066815, 0.06549102, 0.06433427, 0.06330841, 0.06238752,
                                                                                         0.06155253, 0.06050461, 0.05960523, 0.058821, 0.05812833,
                                                                                         0.05750997, 0.056893, 0.05635812, 0.05589033, 0.05547834,
                                                                                         0.05511344, 0.05478879, 0.05449895, 0.05423948, 0.05400678,
                                                                                         0.05379784, 0.05361016, 0.05344163, 0.05329045, 0.05315508,
                                                                                         0.0530342, 0.05292668, 0.05283151, 0.05274783, 0.05267487,
                                                                                         0.05261198]) * 1000.0, })

        self.consumption = pd.DataFrame({'CO2 (Mt)': np.array([1.28473431e+09, 1.24026410e+09, 1.20920553e+09, 2.49446882e+10,
                                                               5.50034920e+10, 8.99877703e+10, 1.29098065e+11, 1.71931680e+11,
                                                               2.18234033e+11, 2.68123194e+11, 3.21458915e+11, 3.78134326e+11,
                                                               4.38214336e+11, 5.01623337e+11, 5.66820327e+11, 6.33674016e+11,
                                                               7.02070511e+11, 7.71909835e+11, 8.19285617e+11, 8.61586757e+11,
                                                               9.00230650e+11, 9.35836743e+11, 9.68739031e+11, 9.99135391e+11,
                                                               1.02697781e+12, 1.05232158e+12, 1.07519492e+12, 1.09560777e+12,
                                                               1.11355731e+12, 1.13049193e+12, 1.14650986e+12]) / 1.0e9,
                                         'hydrogen.gaseous_hydrogen (TWh)': np.array([7.83846196e+09, 7.56713887e+09, 7.37764337e+09, 1.52193327e+11,
                                                                                      3.35589060e+11, 5.49036255e+11, 7.87657231e+11, 1.04899505e+12,
                                                                                      1.33149645e+12, 1.63588179e+12, 1.96129539e+12, 2.30708521e+12,
                                                                                      2.67364729e+12, 3.06052031e+12, 3.45830226e+12, 3.86619212e+12,
                                                                                      4.28349500e+12, 4.70960091e+12, 4.99865154e+12, 5.25674061e+12,
                                                                                      5.49251596e+12, 5.70975699e+12, 5.91050148e+12, 6.09595672e+12,
                                                                                      6.26582979e+12, 6.42045801e+12, 6.56001356e+12, 6.68455710e+12,
                                                                                      6.79407140e+12, 6.89739345e+12, 6.99512256e+12]) / 1.0e9,
                                         'electricity (TWh)': np.array([1.24834354e+10, 2.26888500e+10, 3.13224798e+10, 4.16183686e+10,
                                                                        5.33137316e+10, 6.65015094e+10, 8.07396503e+10, 9.59308386e+10,
                                                                        1.12076605e+11, 1.29500242e+11, 1.48068984e+11, 1.67664859e+11,
                                                                        1.88614872e+11, 2.10307763e+11, 2.32534190e+11, 2.55258218e+11,
                                                                        2.78448193e+11, 3.02075958e+11, 3.26116264e+11, 3.50546301e+11,
                                                                        3.66620834e+11, 3.81434383e+11, 3.98191584e+11, 4.13453346e+11,
                                                                        4.27540649e+11, 4.40613006e+11, 4.52762555e+11, 4.64046630e+11,
                                                                        4.74445226e+11, 4.83975687e+11, 4.92647562e+11]) / 1.0e9,
                                         'biogas (TWh)': np.array([1.49773000e+11, 2.72214901e+11, 3.75798938e+11, 4.99326325e+11,
                                                                   6.39644238e+11, 7.97867754e+11, 9.68693252e+11, 1.15095316e+12,
                                                                   1.34466585e+12, 1.55371011e+12, 1.77649302e+12, 2.01159922e+12,
                                                                   2.26295200e+12, 2.52321765e+12, 2.78988452e+12, 3.06252149e+12,
                                                                   3.34074875e+12, 3.62422851e+12, 3.91265782e+12, 4.20576304e+12,
                                                                   4.39862108e+12, 4.57635017e+12, 4.77739870e+12, 4.96050534e+12,
                                                                   5.12952113e+12, 5.28635985e+12, 5.43212697e+12, 5.56751036e+12,
                                                                   5.69227000e+12, 5.80661398e+12, 5.91065688e+12]) / 1.0e9,
                                         'MEA (Mt)': np.array([7.43925657e+08, 1.35209717e+09, 1.86660126e+09, 2.48016441e+09,
                                                               3.17712645e+09, 3.96302600e+09, 4.81151986e+09, 5.71680869e+09,
                                                               6.67898370e+09, 7.71731095e+09, 8.82387839e+09, 9.99165585e+09,
                                                               1.12401304e+10, 1.25328754e+10, 1.38574154e+10, 1.52116089e+10,
                                                               1.65935696e+10, 1.80016196e+10, 1.94342541e+10, 2.08901139e+10,
                                                               2.18480439e+10, 2.27308280e+10, 2.37294403e+10, 2.46389349e+10,
                                                               2.54784398e+10, 2.62574611e+10, 2.69814895e+10, 2.76539416e+10,
                                                               2.82736254e+10, 2.88415743e+10, 2.93583576e+10]) / 1.0e9,
                                         'oil_resource (Mt)': np.array([7.43925657e+08, 1.35209717e+09, 1.86660126e+09, 2.48016441e+09,
                                                                   3.17712645e+09, 3.96302600e+09, 4.81151986e+09, 5.71680869e+09,
                                                                   6.67898370e+09, 7.71731095e+09, 8.82387839e+09, 9.99165585e+09,
                                                                   1.12401304e+10, 1.25328754e+10, 1.38574154e+10, 1.52116089e+10,
                                                                   1.65935696e+10, 1.80016196e+10, 1.94342541e+10, 2.08901139e+10,
                                                                   2.18480439e+10, 2.27308280e+10, 2.37294403e+10, 2.46389349e+10,
                                                                   2.54784398e+10, 2.62574611e+10, 2.69814895e+10, 2.76539416e+10,
                                                                   2.82736254e+10, 2.88415743e+10, 2.93583576e+10]) / 1.0e9})

        self.production = pd.DataFrame({'methane': np.array([1.16605879e+11, 2.09714671e+11, 2.88496631e+11, 4.30619647e+11,
                                                             5.98336737e+11, 7.89664048e+11, 9.98944599e+11, 1.22447365e+12,
                                                             1.46574928e+12, 1.72596317e+12, 2.00361864e+12, 2.29742180e+12,
                                                             2.61049046e+12, 2.93708922e+12, 3.27218360e+12, 3.61517937e+12,
                                                             3.96555667e+12, 4.32285576e+12, 4.63840191e+12, 4.94722388e+12,
                                                             5.17232979e+12, 5.37976418e+12, 5.59946957e+12, 5.80044012e+12,
                                                             5.98550982e+12, 6.15624743e+12, 6.31355157e+12, 6.45796597e+12,
                                                             6.58930224e+12, 6.71065379e+12, 6.82230688e+12]) / 1.0e9,
                                        'methane Emethane (TWh)': np.array([2.60340125e+09, 2.51328627e+09, 2.45034882e+09, 5.05482199e+10,
                                                                            1.11459746e+11, 1.82352314e+11, 2.61605891e+11, 3.48404451e+11,
                                                                            4.42232103e+11, 5.43328106e+11, 6.51408261e+11, 7.66256003e+11,
                                                                            8.88002867e+11, 1.01649564e+12, 1.14861161e+12, 1.28408474e+12,
                                                                            1.42268423e+12, 1.56420749e+12, 1.66021035e+12, 1.74592990e+12,
                                                                            1.82423835e+12, 1.89639097e+12, 1.96306457e+12, 2.02466013e+12,
                                                                            2.08108035e+12, 2.13243727e+12, 2.17878808e+12, 2.22015293e+12,
                                                                            2.25652610e+12, 2.29084262e+12, 2.32330155e+12]) / 1.0e9,
                                        'invest': np.array([8.87150e+09, 9.04400e+09, 9.21650e+09, 9.38900e+09, 9.56150e+09,
                                                            9.73400e+09, 9.93880e+09, 1.01436e+10, 1.03484e+10, 1.05532e+10,
                                                            1.07580e+10, 1.07294e+10, 1.07008e+10, 1.06722e+10, 1.06436e+10,
                                                            1.06150e+10, 1.05864e+10, 1.05578e+10, 1.05292e+10, 1.05006e+10,
                                                            1.04720e+10, 1.04434e+10, 1.04148e+10, 1.03862e+10, 1.03576e+10,
                                                            1.03290e+10, 1.03004e+10, 1.02718e+10, 1.02432e+10, 1.02146e+10,
                                                            1.01860e+10]) / 1.0e9,
                                        'water (Mt)': np.array([4.20719806e+08, 4.06156873e+08, 3.95985935e+08, 8.16878967e+09,
                                                                1.80123301e+10, 2.94688458e+10, 4.22765332e+10, 5.63035194e+10,
                                                                7.14664343e+10, 8.78039430e+10, 1.05270118e+11, 1.23829961e+11,
                                                                1.43504730e+11, 1.64269664e+11, 1.85620121e+11, 2.07513107e+11,
                                                                2.29911326e+11, 2.52782037e+11, 2.68296474e+11, 2.82149087e+11,
                                                                2.94804040e+11, 3.06464185e+11, 3.17238898e+11, 3.27192980e+11,
                                                                3.36310708e+11, 3.44610188e+11, 3.52100660e+11, 3.58785381e+11,
                                                                3.64663427e+11, 3.70209111e+11, 3.75454601e+11]) / 1.0e9,
                                        'methane UpgradingBiogas (TWh)': np.array([1.14002477e+11, 2.07201385e+11, 2.86046282e+11, 3.80071427e+11,
                                                                                   4.86876991e+11, 6.07311734e+11, 7.37338708e+11, 8.76069197e+11,
                                                                                   1.02351718e+12, 1.18263506e+12, 1.35221038e+12, 1.53116579e+12,
                                                                                   1.72248759e+12, 1.92059358e+12, 2.12357198e+12, 2.33109463e+12,
                                                                                   2.54287243e+12, 2.75864827e+12, 2.97819156e+12, 3.20129399e+12,
                                                                                   3.34809144e+12, 3.48337321e+12, 3.63640500e+12, 3.77577999e+12,
                                                                                   3.90442947e+12, 4.02381016e+12, 4.13476348e+12, 4.23781304e+12,
                                                                                   4.33277614e+12, 4.41981116e+12, 4.49900533e+12]) / 1.0e9,
                                        'CO2 (Mt)': np.array([5.62582867e+09, 1.02250365e+10, 1.41158983e+10, 1.87558795e+10,
                                                              2.40265528e+10, 2.99698028e+10, 3.63864132e+10, 4.32325272e+10,
                                                              5.05088346e+10, 5.83610321e+10, 6.67292861e+10, 7.55604318e+10,
                                                              8.50018377e+10, 9.47780320e+10, 1.04794671e+11, 1.15035562e+11,
                                                              1.25486437e+11, 1.36134608e+11, 1.46968696e+11, 1.57978422e+11,
                                                              1.65222627e+11, 1.71898553e+11, 1.79450412e+11, 1.86328331e+11,
                                                              1.92676964e+11, 1.98568198e+11, 2.04043557e+11, 2.09128877e+11,
                                                              2.13815145e+11, 2.18110176e+11, 2.22018273e+11]) / 1.0e9})

        self.cost_details = pd.DataFrame({'methane': np.array([0.19333753, 0.1874625, 0.18467199, 0.21320619, 0.2308158,
                                                               0.24196874, 0.25146023, 0.25909781, 0.26565857, 0.27142873,
                                                               0.27673861, 0.27989425, 0.28277203, 0.28558565, 0.28905927,
                                                               0.29229019, 0.29530982, 0.29853801, 0.29984838, 0.30094081,
                                                               0.30355508, 0.3071769, 0.31104297, 0.31440867, 0.31709487,
                                                               0.32047716, 0.32392652, 0.32739837, 0.33021771, 0.33313758,
                                                               0.3361545]) * 1000.0,
                                          'methane_wotaxes': np.asarray([0.18333753, 0.1774625, 0.17467199, 0.20320619, 0.2208158,
                                                                         0.23196874, 0.24146023, 0.24909781, 0.25565857, 0.26142873,
                                                                         0.26673861, 0.26989425, 0.27277203, 0.27558565, 0.27905927,
                                                                         0.28229019, 0.28530982, 0.28853801, 0.28984838, 0.29094081,
                                                                         0.29355508, 0.2971769, 0.30104297, 0.30440867, 0.30709487,
                                                                         0.31047716, 0.31392652, 0.31739837, 0.32021771, 0.32313758,
                                                                         0.3261545]) * 1000.0})
        self.energy_demand = {}
        self.energy_demand['hydrogen.gaseous_hydrogen.energy_demand'] = pd.DataFrame({'years': self.years,
                                                                                      'demand': np.arange(50, 81)})
        self.energy_demand['methane.energy_demand'] = pd.DataFrame({'years': self.years,
                                                                    'demand': np.arange(20, 51)})
        self.energy_demand['biogas.energy_demand'] = pd.DataFrame({'years': self.years,
                                                                   'demand': np.arange(10, 41)})

        self.land_use_required_mock = pd.DataFrame(
            {'years': self.years, 'random techno (Gha)': 0.0})

        years = np.arange(2020, 2051)
        co2_taxes_year = [2018, 2020, 2025, 2030, 2035, 2040, 2045, 2050]
        co2_taxes = [14.86, 17.22, 20.27,
                     29.01,  34.05,   39.08,  44.69,   50.29]
        func = sc.interp1d(co2_taxes_year, co2_taxes,
                           kind='linear', fill_value='extrapolate')

        self.co2_taxes = pd.DataFrame(
            {'years': years, 'CO2_tax': func(years)})

        self.minimum_energy_production = 1e4
        self.production_threshold = 1e-3
        self.total_prod_minus_min_prod_constraint_ref = 1e4
        self.scaling_factor_techno_consumption = 1e3
        self.scaling_factor_techno_production = 1e3
        demand_ratio_dict = dict(
            zip(EnergyMix.energy_list, np.ones((len(self.years), len(self.years)))))
        demand_ratio_dict['years'] = self.years
        self.all_streams_demand_ratio = pd.DataFrame(demand_ratio_dict)
        self.is_stream_demand = True
        self.liquid_hydrogen_percentage = np.ones(len(self.years))

    def test_01_energy_mix(self):
        """
        Test energy mix class

        Returns
        -------
        None.

        """

        inputs_dict = {'year_start': self.year_start,
                       'year_end': self.year_end,
                       'energy_list': ['hydrogen.gaseous_hydrogen', 'methane'],
                       'ccs_list': [],
                       'hydrogen.gaseous_hydrogen.energy_consumption': self.consumption_hydro,
                       'hydrogen.gaseous_hydrogen.energy_consumption_woratio': self.consumption_hydro,
                       'hydrogen.gaseous_hydrogen.energy_production': self.production_hydro,
                       'hydrogen.gaseous_hydrogen.energy_production_woratio': self.production_hydro,
                       'hydrogen.gaseous_hydrogen.energy_prices': self.prices_hydro,
                       'hydrogen.gaseous_hydrogen.energy_demand': self.energy_demand['hydrogen.gaseous_hydrogen.energy_demand'],
                       'hydrogen.gaseous_hydrogen.land_use_required': self.land_use_required_mock,
                       'hydrogen.gaseous_hydrogen.data_fuel_dict': GaseousHydrogen.data_energy_dict,
                       'methane.energy_consumption': self.consumption,
                       'methane.energy_consumption_woratio': self.consumption,
                       'methane.energy_production': self.production,
                       'methane.energy_production_woratio': self.production,
                       'methane.energy_prices': self.cost_details,
                       'methane.energy_demand': self.energy_demand['methane.energy_demand'],
                       'methane.land_use_required': self.land_use_required_mock,
                       'methane.data_fuel_dict': Methane.data_energy_dict,
                       'hydrogen.gaseous_hydrogen.CO2_per_use': pd.DataFrame({'years': self.years, 'CO2_tax': 0.0, 'CO2_per_use': 0.0}),
                       'hydrogen.gaseous_hydrogen.CO2_emissions': pd.DataFrame({'years': self.years, 'hydrogen.gaseous_hydrogen': 0.0}),
                       'methane.CO2_per_use': pd.DataFrame({'years': self.years, 'CO2_tax': 0.0, 'CO2_per_use': 0.0}),
                       'methane.CO2_emissions': pd.DataFrame({'years': self.years, 'methane': 0.0}),
                       'CO2_taxes': self.co2_taxes,
                       'minimum_energy_production': self.minimum_energy_production,
                       'total_prod_minus_min_prod_constraint_ref': self.total_prod_minus_min_prod_constraint_ref,
                       'production_threshold': self.production_threshold,
                       'scaling_factor_energy_production': 1.e3,
                       'scaling_factor_energy_consumption': 1e3,
                       'solid_fuel_elec_percentage': 0.3,
                       'solid_fuel_elec_constraint_ref': 100.0,
                       'liquid_hydrogen_percentage': 0.3,
                       'liquid_hydrogen_constraint_ref': 100.0,
                       'syngas_prod_ref': 100.,
                       'ratio_ref': 100.,
                       'is_dev': False,
                       'hydrogen.gaseous_hydrogen.losses_percentage': 1.,
                       'methane.losses_percentage': 2.,
                       'heat_losses_percentage': 5.

                       }

        EM = EnergyMix('EnergyMix')
        EM.configure(inputs_dict)
        EM.compute_energy_net_and_raw_production()
        EM.compute_price_after_carbon_tax()
        EM.compute_CO2_emissions()

    def test_02_energy_mix_discipline(self):
        """
        Test energy mix discipline

        Returns
        -------
        None.

        """

        name = 'Test'
        model_name = 'EnergyMix'
        ee = ExecutionEngine(name)
        ns_dict = {'ns_public': f'{name}',
                   'ns_hydrogen': f'{name}',
                   'ns_methane': f'{name}',
                   'ns_energy_study': f'{name}',
                   'ns_demand': f'{name}.{model_name}',
                   'ns_energy_mix': f'{name}.{model_name}',
                   'ns_functions': f'{name}.{model_name}',
                   'ns_resource': f'{name}.{model_name}.resource',
                   'ns_ccs': f'{name}.{model_name}',
                   'ns_ref': f'{name}.{model_name}',
                   'ns_energy': f'{name}.{model_name}'}
        ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.energy_mix.energy_mix_disc.Energy_Mix_Discipline'
        builder = ee.factory.get_builder_from_module(model_name, mod_path)

        ee.factory.set_builders_to_coupling_builder(builder)

        ee.configure()
        ee.display_treeview_nodes()

        inputs_dict = {f'{name}.{model_name}.year_start': self.year_start,
                       f'{name}.{model_name}.year_end': self.year_end,
                       f'{name}.energy_list': self.energy_list,
                       f'{name}.ccs_list': [],
                       f'{name}.is_dev': True,
                       f'{name}.{model_name}.energy_prices': pd.DataFrame({'hydrogen.gaseous_hydrogen': self.prices_hydro['hydrogen.gaseous_hydrogen'], 'methane': self.cost_details['methane']}),
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.energy_consumption': self.consumption_hydro,
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.energy_consumption_woratio': self.consumption_hydro,
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.energy_production': self.production_hydro,
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.energy_production_woratio': self.production_hydro,
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.energy_prices': self.prices_hydro,
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.CO2_per_use': pd.DataFrame({'years': self.years, 'CO2_tax': 0.0, 'CO2_per_use': 0.0}),
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.CO2_emissions': pd.DataFrame({'years': self.years, 'hydrogen.gaseous_hydrogen': 0.0}),
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.energy_demand': self.energy_demand['hydrogen.gaseous_hydrogen.energy_demand'],
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.land_use_required': self.land_use_required_mock,
                       f'{name}.{model_name}.methane.energy_consumption': self.consumption,
                       f'{name}.{model_name}.methane.energy_consumption_woratio': self.consumption,
                       f'{name}.{model_name}.methane.energy_production': self.production,
                       f'{name}.{model_name}.methane.energy_production_woratio': self.production,
                       f'{name}.{model_name}.methane.energy_prices': self.cost_details,
                       f'{name}.{model_name}.methane.CO2_per_use': pd.DataFrame({'years': self.years, 'CO2_tax': 0.0, 'CO2_per_use': 0.0}),
                       f'{name}.{model_name}.methane.CO2_emissions': pd.DataFrame({'years': self.years, 'methane': 0.0}),
                       f'{name}.{model_name}.methane.energy_demand': self.energy_demand['methane.energy_demand'],
                       f'{name}.{model_name}.methane.land_use_required': self.land_use_required_mock,
                       f'{name}.CO2_taxes': self.co2_taxes,
                       f'{name}.{model_name}.liquid_hydrogen_percentage': self.liquid_hydrogen_percentage,
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.loss_percentage': 1.0,
                       f'{name}.{model_name}.methane.loss_percentage': 2.0,
                       }

        ee.load_study_from_input_dict(inputs_dict)

        ee.execute()

        disc = ee.dm.get_disciplines_with_name(
            f'{name}.{model_name}')[0]
        ppf = PostProcessingFactory()
        filters = ppf.get_post_processing_filters_by_discipline(disc)
        graph_list = ppf.get_post_processing_by_discipline(
            disc, filters, as_json=False)

#        for graph in graph_list:
#            graph.to_plotly().show()

        #-- check demand violation value
        for e_name in self.energy_list:
            # ref data
            demand = self.energy_demand[f'{e_name}.energy_demand']['demand']
            net_prod_energy = disc.get_sosdisc_outputs('energy_production_detailed')[
                f'{EnergyMix.PRODUCTION} {e_name} (TWh)']
            ref_prod = pd.DataFrame({'years': self.years})
            normalization_value_demand_constraints = disc.get_sosdisc_inputs(
                'normalization_value_demand_constraints')
            ref_prod[EnergyMix.DEMAND_VIOLATION] = (
                net_prod_energy - demand) / normalization_value_demand_constraints
            # retrieve demand_violation discipline output
            dviol_name = f'{e_name}.{EnergyMix.DEMAND_VIOLATION}'
            demand_viol = disc.get_sosdisc_outputs(dviol_name)
            # compare output with ref
            for col in demand_viol:
                if col != 'years':
                    self.assertListEqual(
                        list(demand_viol[col].values), list(ref_prod[col].values))

    def test_03_energy_mix_discipline_exponential_limit(self):
        """
        Test energy mix discipline

        Returns
        -------
        None.

        """

        name = 'Test'
        model_name = 'EnergyMix'
        ee = ExecutionEngine(name)
        ns_dict = {'ns_public': f'{name}',
                   'ns_hydrogen': f'{name}',
                   'ns_methane': f'{name}',
                   'ns_energy_study': f'{name}',
                   'ns_demand': f'{name}.{model_name}',
                   'ns_energy_mix': f'{name}.{model_name}',
                   'ns_functions': f'{name}.{model_name}',
                   'ns_resource': f'{name}.{model_name}.resource',
                   'ns_ccs': f'{name}.{model_name}',
                   'ns_ref': f'{name}.{model_name}',
                   'ns_energy': f'{name}.{model_name}'}

        ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.energy_mix.energy_mix_disc.Energy_Mix_Discipline'
        builder = ee.factory.get_builder_from_module(model_name, mod_path)

        ee.factory.set_builders_to_coupling_builder(builder)

        ee.configure()
        ee.display_treeview_nodes()

        inputs_dict = {f'{name}.{model_name}.year_start': self.year_start,
                       f'{name}.{model_name}.year_end': self.year_end,
                       f'{name}.energy_list': self.energy_list,
                       f'{name}.ccs_list': [],
                       f'{name}.{model_name}.energy_prices': pd.DataFrame({'hydrogen.gaseous_hydrogen': self.prices_hydro['hydrogen.gaseous_hydrogen'], 'methane': self.cost_details['methane']}),
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.energy_consumption': self.consumption_hydro,
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.energy_consumption_woratio': self.consumption_hydro,
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.energy_production': self.production_hydro,
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.energy_production_woratio': self.production_hydro,
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.energy_prices': self.prices_hydro,
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.CO2_per_use': pd.DataFrame({'years': self.years, 'CO2_tax': 0.0, 'CO2_per_use': 0.0}),
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.CO2_emissions': pd.DataFrame({'years': self.years, 'hydrogen.gaseous_hydrogen': 0.0}),
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.energy_demand': self.energy_demand['hydrogen.gaseous_hydrogen.energy_demand'],
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.land_use_required': self.land_use_required_mock,
                       f'{name}.{model_name}.methane.energy_consumption': self.consumption,
                       f'{name}.{model_name}.methane.energy_consumption_woratio': self.consumption,
                       f'{name}.{model_name}.methane.energy_production': self.production,
                       f'{name}.{model_name}.methane.energy_production_woratio': self.production,
                       f'{name}.{model_name}.methane.energy_prices': self.cost_details,
                       f'{name}.{model_name}.methane.CO2_per_use': pd.DataFrame({'years': self.years, 'CO2_tax': 0.0, 'CO2_per_use': 0.0}),
                       f'{name}.{model_name}.methane.CO2_emissions': pd.DataFrame({'years': self.years, 'methane': 0.0}),
                       f'{name}.{model_name}.methane.energy_demand': self.energy_demand['methane.energy_demand'],
                       f'{name}.{model_name}.methane.land_use_required': self.land_use_required_mock,
                       f'{name}.CO2_taxes': self.co2_taxes,
                       f'{name}.{model_name}.liquid_hydrogen_percentage': self.liquid_hydrogen_percentage
                       }

        ee.load_study_from_input_dict(inputs_dict)

        ee.execute()

        ppf = PostProcessingFactory()

        disc = ee.dm.get_disciplines_with_name(
            f'{name}.{model_name}')[0]
        filters = ppf.get_post_processing_filters_by_discipline(disc)
        graph_list = ppf.get_post_processing_by_discipline(
            disc, filters, as_json=False)

#        for graph in graph_list:
#            try:
#                if graph.chart_name == 'Net Energies Total Production and Limit':
#                    graph.to_plotly().show()
#            except:
#                pass

    def test_04_energy_mix_resource(self):
        """
        Test energy mix resource

        Returns
        -------
        None.

        """

        name = 'Test'
        model_name = 'EnergyMix'
        ee = ExecutionEngine(name)
        ns_dict = {'ns_public': f'{name}',
                   'ns_hydrogen': f'{name}',
                   'ns_methane': f'{name}',
                   'ns_energy_study': f'{name}',
                   'ns_demand': f'{name}.{model_name}',
                   'ns_energy_mix': f'{name}.{model_name}',
                   'ns_functions': f'{name}.{model_name}',
                   'ns_resource': f'{name}.{model_name}.resource',
                   'ns_ccs': f'{name}.{model_name}',
                   'ns_ref': f'{name}.{model_name}',
                   'ns_energy': f'{name}.{model_name}'}
        ee.ns_manager.add_ns_def(ns_dict)

        mod_path = 'energy_models.core.energy_mix.energy_mix_disc.Energy_Mix_Discipline'
        builder = ee.factory.get_builder_from_module(model_name, mod_path)

        ee.factory.set_builders_to_coupling_builder(builder)

        ee.configure()
        ee.display_treeview_nodes()

        inputs_dict = {f'{name}.{model_name}.year_start': self.year_start,
                       f'{name}.{model_name}.year_end': self.year_end,
                       f'{name}.energy_list': self.energy_list,
                       f'{name}.ccs_list': [],
                       f'{name}.{model_name}.energy_prices': pd.DataFrame({'hydrogen.gaseous_hydrogen': self.prices_hydro['hydrogen.gaseous_hydrogen'], 'methane': self.cost_details['methane']}),
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.energy_consumption': self.consumption_hydro,
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.energy_consumption_woratio': self.consumption_hydro,
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.energy_production': self.production_hydro,
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.energy_production_woratio': self.production_hydro,
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.energy_prices': self.prices_hydro,
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.CO2_per_use': pd.DataFrame({'years': self.years, 'CO2_tax': 0.0, 'CO2_per_use': 0.0}),
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.CO2_emissions': pd.DataFrame({'years': self.years, 'hydrogen.gaseous_hydrogen': 0.0}),
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.energy_demand': self.energy_demand['hydrogen.gaseous_hydrogen.energy_demand'],
                       f'{name}.{model_name}.hydrogen.gaseous_hydrogen.land_use_required': self.land_use_required_mock,
                       f'{name}.{model_name}.methane.energy_consumption': self.consumption,
                       f'{name}.{model_name}.methane.energy_consumption_woratio': self.consumption,
                       f'{name}.{model_name}.methane.energy_production': self.production,
                       f'{name}.{model_name}.methane.energy_production_woratio': self.production,
                       f'{name}.{model_name}.methane.energy_prices': self.cost_details,
                       f'{name}.{model_name}.methane.CO2_per_use': pd.DataFrame({'years': self.years, 'CO2_tax': 0.0, 'CO2_per_use': 0.0}),
                       f'{name}.{model_name}.methane.CO2_emissions': pd.DataFrame({'years': self.years, 'methane': 0.0}),
                       f'{name}.{model_name}.methane.energy_demand': self.energy_demand['methane.energy_demand'],
                       f'{name}.{model_name}.methane.land_use_required': self.land_use_required_mock,
                       f'{name}.CO2_taxes': self.co2_taxes,
                       f'{name}.{model_name}.liquid_hydrogen_percentage': self.liquid_hydrogen_percentage
                       }

        ee.load_study_from_input_dict(inputs_dict)

        ee.execute()

        disc = ee.dm.get_disciplines_with_name(
            f'{name}.{model_name}')[0]
        all_demand = ee.dm.get_value(
            f'{name}.{model_name}.resource.All_Demand')
        scaling_factor = 1000
        zero_line = np.linspace(0, 0, len(all_demand.index))
        self.assertListEqual(list(self.consumption['oil_resource (Mt)'].values), list(
            all_demand['oil_resource'].values / scaling_factor))  # in (Mt)
        self.assertListEqual(list(zero_line), list(
            all_demand['coal_resource'].values))


if '__main__' == __name__:
    cls = EnergyMixTestCase()
    cls.setUp()
    cls.test_02_energy_mix_discipline()
