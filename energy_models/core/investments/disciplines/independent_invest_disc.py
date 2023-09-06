'''
mode: python; py-indent-offset: 4; tab-width: 8; coding: utf-8
Copyright (c) 2020 Airbus SAS.
All rights reserved.
'''
import numpy as np
import pandas as pd

from energy_models.core.energy_mix.energy_mix import EnergyMix
from energy_models.core.stream_type.energy_models.biomass_dry import BiomassDry
from energy_models.core.investments.base_invest import compute_norm_mix
from energy_models.core.investments.independent_invest import IndependentInvest
from sostrades_core.execution_engine.sos_wrapp import SoSWrapp
from sostrades_core.tools.post_processing.charts.chart_filter import ChartFilter
from sostrades_core.tools.post_processing.charts.two_axes_instanciated_chart import InstanciatedSeries, \
    TwoAxesInstanciatedChart
from sostrades_core.tools.post_processing.pie_charts.instanciated_pie_chart import InstanciatedPieChart
from sostrades_core.tools.base_functions.exp_min import compute_dfunc_with_exp_min, \
    compute_func_with_exp_min
from sostrades_core.tools.cst_manager.func_manager_common import smooth_maximum, get_dsmooth_dvariable
from sostrades_core.tools.cst_manager.constraint_manager import compute_delta_constraint, compute_ddelta_constraint
from climateeconomics.core.core_witness.climateeco_discipline import ClimateEcoDiscipline
from energy_models.core.ccus.ccus import CCUS


class IndependentInvestDiscipline(SoSWrapp):
    # ontology information
    _ontology_data = {
        'label': 'InvestmentsDistribution',
        'type': 'Research',
        'source': 'SoSTrades Project',
        'validated': '',
        'validated_by': 'SoSTrades Project',
        'last_modification_date': '',
        'category': '',
        'definition': '',
        'icon': 'fas fa-coins fa-fw',
        'version': '',
    }
    energy_mix_name = EnergyMix.name
    DESC_IN = {
        'year_start': ClimateEcoDiscipline.YEAR_START_DESC_IN,
        'year_end': ClimateEcoDiscipline.YEAR_END_DESC_IN,
        'energy_investment': {'type': 'dataframe', 'unit': '100G$',
                              'dataframe_descriptor': {'years': ('float', None, False),
                                                       'energy_investment': ('float', None, True)},
                              'dataframe_edition_locked': False,
                              'visibility': 'Shared', 'namespace': 'ns_witness'},
        'scaling_factor_energy_investment': {'type': 'float', 'default': 1e2, 'user_level': 2, 'visibility': 'Shared',
                                             'namespace': 'ns_public'},
        'invest_mix': {'type': 'dataframe', 'unit': 'G$',
                       'dataframe_edition_locked': False,
                       'dataframe_descriptor': {'years': ('float', None, True),
                                                'electricity.SolarPv': ('float', None, True),
                                                'electricity.WindOnshore': ('float', None, True),
                                                'electricity.CoalGen': ('float', None, True),
                                                'methane.FossilGas': ('float', None, True),
                                                'methane.UpgradingBiogas': ('float', None, True),
                                                'hydrogen.gaseous_hydrogen.WaterGasShift': ('float', None, True),
                                                'hydrogen.gaseous_hydrogen.Electrolysis.AWE': ('float', None, True),
                                                'carbon_capture.direct_air_capture.AmineScrubbing': (
                                                'float', None, True),
                                                'carbon_capture.flue_gas_capture.CalciumLooping': ('float', None, True),
                                                'carbon_storage.DeepSalineFormation': ('float', None, True),
                                                'carbon_storage.GeologicMineralization': ('float', None, True),
                                                'methane.Methanation': ('float', None, True),
                                                'hydrogen.gaseous_hydrogen.PlasmaCracking': ('float', None, True),
                                                'hydrogen.gaseous_hydrogen.Electrolysis.SOEC': ('float', None, True),
                                                'hydrogen.gaseous_hydrogen.Electrolysis.PEM': ('float', None, True),
                                                'heat.high.highheattemperature': ('float', None, True),
                                                'heat.low.lowheattemperature': ('float', None, True),
                                                'heat.medium.mediumheattemperature': ('float', None, True),
                                                'biogas.AnaerobicDigestion': ('float', None, True),
                                                'syngas.BiomassGasification': ('float', None, True),
                                                'syngas.SMR': ('float', None, True),
                                                'syngas.Pyrolysis': ('float', None, True),
                                                'syngas.AutothermalReforming': ('float', None, True),
                                                'syngas.CoElectrolysis': ('float', None, True),
                                                'syngas.CoalGasification': ('float', None, True),
                                                'fuel.liquid_fuel.Refinery': ('float', None, True),
                                                'fuel.liquid_fuel.FischerTropsch': ('float', None, True),
                                                'fuel.hydrotreated_oil_fuel.HefaDecarboxylation': ('float', None, True),
                                                'fuel.hydrotreated_oil_fuel.HefaDeoxygenation': ('float', None, True),
                                                'solid_fuel.CoalExtraction': ('float', None, True),
                                                'solid_fuel.Pelletizing': ('float', None, True),
                                                'electricity.WindOffshore': ('float', None, True),
                                                'electricity.SolarThermal': ('float', None, True),
                                                'electricity.Geothermal': ('float', None, True),
                                                'electricity.Hydropower': ('float', None, True),
                                                'electricity.Nuclear': ('float', None, True),
                                                'electricity.CombinedCycleGasTurbine': ('float', None, True),
                                                'electricity.GasTurbine': ('float', None, True),
                                                'electricity.BiogasFired': ('float', None, True),
                                                'electricity.BiomassFired': ('float', None, True),
                                                'electricity.OilGen': ('float', None, True),
                                                'fuel.biodiesel.Transesterification': ('float', None, True),
                                                'fuel.ethanol.BiomassFermentation': ('float', None, True),
                                                'hydrogen.liquid_hydrogen.HydrogenLiquefaction': ('float', None, True),
                                                'carbon_capture.direct_air_capture.CalciumPotassiumScrubbing': (
                                                'float', None, True),
                                                'carbon_capture.flue_gas_capture.ChilledAmmoniaProcess': (
                                                'float', None, True),
                                                'carbon_capture.flue_gas_capture.CO2Membranes': ('float', None, True),
                                                'carbon_capture.flue_gas_capture.MonoEthanolAmine': (
                                                'float', None, True),
                                                'carbon_capture.flue_gas_capture.PiperazineProcess': (
                                                'float', None, True),
                                                'carbon_capture.flue_gas_capture.PressureSwingAdsorption': (
                                                'float', None, True),
                                                'carbon_storage.BiomassBuryingFossilization': ('float', None, True),
                                                'carbon_storage.DeepOceanInjection': ('float', None, True),
                                                'carbon_storage.DepletedOilGas': ('float', None, True),
                                                'carbon_storage.EnhancedOilRecovery': ('float', None, True),
                                                'carbon_storage.PureCarbonSolidStorage': ('float', None, True),
                                                'renewable.RenewableSimpleTechno': ('float', None, True),
                                                'fossil.FossilSimpleTechno': ('float', None, True),
                                                'carbon_capture.direct_air_capture.DirectAirCaptureTechno' : ('float', None, True),
                                                'carbon_capture.flue_gas_capture.FlueGasTechno': ('float', None, True),
                                                'carbon_storage.CarbonStorageTechno': ('float', None, True),
                                                }},
        'invest_objective_ref': {'type': 'float', 'unit': 'G$', 'default': 1.0, 'user_level': 2, 'visibility': 'Shared',
                                 'namespace': 'ns_ref'},
        'invest_sum_ref': {'type': 'float', 'unit': 'G$', 'default': 2., 'user_level': 2, 'visibility': 'Shared',
                           'namespace': 'ns_ref'},
        'invest_constraint_ref': {'type': 'float', 'unit': 'G$', 'default': 80.0, 'user_level': 2,
                                  'visibility': 'Shared', 'namespace': 'ns_ref'},
        'energy_list': {'type': 'list', 'subtype_descriptor': {'list': 'string'},
                        'possible_values': EnergyMix.energy_list,
                        'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study',
                        'editable': False, 'structuring': True},
        'ccs_list': {'type': 'list', 'subtype_descriptor': {'list': 'string'}, 'possible_values': CCUS.ccs_list,
                     'visibility': SoSWrapp.SHARED_VISIBILITY, 'namespace': 'ns_energy_study', 'editable': False,
                     'structuring': True},
        'invest_limit_ref': {'type': 'float', 'default': 300., 'unit': 'G$', 'user_level': 2, 'visibility': 'Shared',
                             'namespace': 'ns_ref'},
        'forest_investment': {'type': 'dataframe', 'unit': 'G$', 'visibility': 'Shared',
                              'dataframe_descriptor': {'years': ('float', None, False),
                                                       'forest_investment': ('float', None, False)}, 'namespace': 'ns_invest',
                              'dataframe_edition_locked': False},
    }

    energy_name = "one_invest"

    DESC_OUT = {
        'invest_constraint': {'type': 'dataframe', 'unit': '', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                              'namespace': 'ns_functions'},
        'invest_objective': {'type': 'array', 'unit': '', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                             'namespace': 'ns_functions'},
        'invest_objective_sum': {'type': 'array', 'unit': '', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                                 'namespace': 'ns_functions'},
        'invest_sum_cons': {'type': 'array', 'unit': '', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                            'namespace': 'ns_functions'},
        'invest_sum_eq_cons': {'type': 'array', 'unit': '', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                               'namespace': 'ns_functions'},
        'invest_sum_cons_dc': {'type': 'array', 'unit': '', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                               'namespace': 'ns_functions'},
        'invest_sum_ineq_cons': {'type': 'array', 'unit': '', 'visibility': SoSWrapp.SHARED_VISIBILITY,
                               'namespace': 'ns_functions'},
    }
    _maturity = 'Research'

    def init_execution(self):
        self.independent_invest_model = IndependentInvest()

    def setup_sos_disciplines(self):
        '''
        Construct the desc_out to couple energy invest levels to techno_invest_disc
        '''
        dynamic_outputs = {}
        dynamic_inputs = {}

        if 'energy_list' in self.get_data_in():
            energy_list = self.get_sosdisc_inputs('energy_list')
            if energy_list is not None:
                for energy in energy_list:
                    if energy == BiomassDry.name:
                        dynamic_inputs['managed_wood_investment'] = {
                            'type': 'dataframe', 'unit': 'G$', 'visibility': 'Shared',
                            'dataframe_descriptor': {'years': ('float', None, False),
                                                     'investment': ('float', None, False)},
                            'namespace': 'ns_forest', 'dataframe_edition_locked': False,}
                        dynamic_inputs['deforestation_investment'] = {
                            'type': 'dataframe', 'unit': 'G$', 'visibility': 'Shared',
                            'dataframe_descriptor': {'years': ('float', None, False),
                                                     'investment': ('float', None, False)},
                            'namespace': 'ns_forest', 'dataframe_edition_locked': False}
                        dynamic_inputs['crop_investment'] = {
                            'type': 'dataframe', 'unit': 'G$', 'visibility': 'Shared',
                            'dataframe_descriptor': {'years': ('float', None, False),
                                                     'investment': ('float', None, False)},
                            'namespace': 'ns_crop', 'dataframe_edition_locked': False}
                    else:
                        # Add technologies_list to inputs
                        dynamic_inputs[f'{energy}.technologies_list'] = {
                            'type': 'list', 'subtype_descriptor': {'list': 'string'}, 'structuring': True,
                            'visibility': 'Shared', 'namespace': 'ns_energy',
                            'possible_values': EnergyMix.stream_class_dict[energy].default_techno_list,
                            'default': EnergyMix.stream_class_dict[energy].default_techno_list}
                        # Add all invest_level outputs
                        if f'{energy}.technologies_list' in self.get_data_in():
                            technology_list = self.get_sosdisc_inputs(
                                f'{energy}.technologies_list')
                            if technology_list is not None:
                                for techno in technology_list:
                                    dynamic_outputs[f'{energy}.{techno}.invest_level'] = {
                                        'type': 'dataframe', 'unit': 'G$',
                                        'visibility': 'Shared', 'namespace': 'ns_energy'}

        if 'ccs_list' in self.get_data_in():
            ccs_list = self.get_sosdisc_inputs('ccs_list')
            if ccs_list is not None:
                for ccs in ccs_list:
                    # Add technologies_list to inputs
                    dynamic_inputs[f'{ccs}.technologies_list'] = {
                        'type': 'list', 'subtype_descriptor': {'list': 'string'}, 'structuring': True,
                        'visibility': 'Shared', 'namespace': 'ns_ccs',
                        'possible_values': EnergyMix.stream_class_dict[ccs].default_techno_list}
                    # Add all invest_level outputs
                    if f'{ccs}.technologies_list' in self.get_data_in():
                        technology_list = self.get_sosdisc_inputs(
                            f'{ccs}.technologies_list')
                        if technology_list is not None:
                            for techno in technology_list:
                                dynamic_outputs[f'{ccs}.{techno}.invest_level'] = {
                                    'type': 'dataframe', 'unit': 'G$', 'visibility': 'Shared', 'namespace': 'ns_ccs'}

        self.add_inputs(dynamic_inputs)
        self.add_outputs(dynamic_outputs)

    def run(self):

        input_dict = self.get_sosdisc_inputs()

        invest_constraint_df, invest_objective, abs_delta, abs_delta_cons, abs_delta_cons_dc, delta_eq_cons, dela_sum_cons_ineq = self.independent_invest_model.compute_invest_constraint_and_objective(
            input_dict)

        output_dict = {'invest_constraint': invest_constraint_df,
                       'invest_objective': invest_objective,
                       'invest_objective_sum': abs_delta,
                       'invest_sum_cons': abs_delta_cons,
                       'invest_sum_cons_dc': abs_delta_cons_dc,
                       'invest_sum_eq_cons': delta_eq_cons,
                       'invest_sum_ineq_cons' : dela_sum_cons_ineq
                       }

        for energy in input_dict['energy_list'] + input_dict['ccs_list']:
            if energy == BiomassDry.name:
                pass
            else:
                for techno in input_dict[f'{energy}.technologies_list']:
                    output_dict[f'{energy}.{techno}.invest_level'] = pd.DataFrame(
                        {'years': input_dict['energy_investment']['years'].values,
                         'invest': input_dict['invest_mix'][f'{energy}.{techno}'].values})

        self.store_sos_outputs_values(output_dict)

    def compute_sos_jacobian(self):

        inputs_dict = self.get_sosdisc_inputs()

        scaling_factor_energy_investment = inputs_dict['scaling_factor_energy_investment']
        invest_constraint_ref = inputs_dict['invest_constraint_ref']
        energy_investment = inputs_dict['energy_investment']
        invest_objective_ref = inputs_dict['invest_objective_ref']
        years = np.arange(inputs_dict['year_start'],
                          inputs_dict['year_end'] + 1)
        invest_sum_ref = inputs_dict['invest_sum_ref']
        techno_invests = inputs_dict['invest_mix'][[
            col for col in inputs_dict['invest_mix'] if col != 'years']]
        invest_limit_ref = inputs_dict['invest_limit_ref']
        techno_invest_sum = techno_invests.sum(axis=1).values
        energy_invest = energy_investment['energy_investment'].values * \
                        scaling_factor_energy_investment

        techno_invest_sum += inputs_dict['forest_investment']['forest_investment'].values
        energy_list = inputs_dict['energy_list']
        if BiomassDry.name in energy_list:
            techno_invest_sum += inputs_dict['managed_wood_investment']['investment'].values
            techno_invest_sum += inputs_dict['deforestation_investment']['investment'].values
            techno_invest_sum += inputs_dict['crop_investment']['investment'].values

        delta_years = len(years)
        idt = np.identity(delta_years)
        ddelta_dtech = -idt / energy_invest
        dconstrantineq_dtech = idt / invest_sum_ref / delta_years

        ddelta_dtot = (idt * energy_invest - (energy_invest -
                                              techno_invest_sum) * idt) / energy_invest ** 2

        dinvest_objective_dtechno_invest, dinvest_objective_dtotal_invest = self.compute_dinvest_objective_dinvest(
            techno_invest_sum,
            energy_invest,
            invest_objective_ref)

        dinvest_objective_sum_dtechno_invest, dinvest_objective_sum_dtotal_invest = self.compute_dinvest_objective_sum_dinvest(
            techno_invest_sum, energy_invest, invest_sum_ref)
        dinvest_objective_sum_cons_dtechno_invest, dinvest_objective_sum_cons_dtotal_invest = self.compute_dinvest_objective_sum_cons_dinvest(
            techno_invest_sum, energy_invest, invest_sum_ref, invest_limit_ref)
        dinvest_objective_sum_cons_dc_dtechno_invest, dinvest_objective_sum_cons_dc_dtotal_invest, _ = compute_ddelta_constraint(
            techno_invest_sum, energy_invest, tolerable_delta=invest_limit_ref, delta_type='abs',
            reference_value=invest_sum_ref * delta_years)
        dinvest_eq_cons_dtechno_invest, dinvest_eq_cons_dtotal_invest, _ = compute_ddelta_constraint(
            techno_invest_sum, energy_invest, tolerable_delta=invest_limit_ref, delta_type='normal',
            reference_value=invest_sum_ref * delta_years)

        for techno in self.independent_invest_model.distribution_list:
            self.set_partial_derivative_for_other_types(
                (f'{techno}.invest_level', 'invest'), ('invest_mix', techno), np.identity(len(years)))
            self.set_partial_derivative_for_other_types(
                ('invest_constraint', 'invest_constraint'), ('invest_mix', techno),
                ddelta_dtech / invest_constraint_ref)
            self.set_partial_derivative_for_other_types(
                ('invest_sum_ineq_cons',), ('invest_mix', techno),
                - dconstrantineq_dtech)
            self.set_partial_derivative_for_other_types(
                ('invest_objective', 'invest_objective'), ('invest_mix', techno), dinvest_objective_dtechno_invest)
            self.set_partial_derivative_for_other_types(
                ('invest_objective_sum',), ('invest_mix', techno), dinvest_objective_sum_dtechno_invest)
            self.set_partial_derivative_for_other_types(
                ('invest_sum_cons',), ('invest_mix', techno), -dinvest_objective_sum_cons_dtechno_invest / delta_years)
            self.set_partial_derivative_for_other_types(
                ('invest_sum_cons_dc',), ('invest_mix', techno), dinvest_objective_sum_cons_dc_dtechno_invest)
            self.set_partial_derivative_for_other_types(
                ('invest_sum_eq_cons',), ('invest_mix', techno), dinvest_eq_cons_dtechno_invest)

        self.set_partial_derivative_for_other_types(
            ('invest_constraint', 'invest_constraint'), ('forest_investment',
                                                         'forest_investment'),
            ddelta_dtech / invest_constraint_ref)
        self.set_partial_derivative_for_other_types(
            ('invest_objective', 'invest_constraint'), ('forest_investment',
                                                        'forest_investment'),
            dinvest_objective_dtechno_invest)

        self.set_partial_derivative_for_other_types(
            ('invest_objective_sum',), ('forest_investment', 'forest_investment'), dinvest_objective_sum_dtechno_invest)

        self.set_partial_derivative_for_other_types(
            ('invest_sum_cons',), ('forest_investment', 'forest_investment'),
            -dinvest_objective_sum_cons_dtechno_invest / delta_years)
        self.set_partial_derivative_for_other_types(
            ('invest_sum_cons_dc',), ('forest_investment', 'forest_investment'),
            dinvest_objective_sum_cons_dc_dtechno_invest)
        self.set_partial_derivative_for_other_types(
            ('invest_sum_eq_cons',), ('forest_investment', 'forest_investment'), dinvest_eq_cons_dtechno_invest)

        self.set_partial_derivative_for_other_types(
            ('invest_sum_ineq_cons',), ('forest_investment', 'forest_investment'),
            - dconstrantineq_dtech)

        if BiomassDry.name in energy_list:
            for techno in ['managed_wood_investment', 'deforestation_investment', 'crop_investment']:
                self.set_partial_derivative_for_other_types(
                    ('invest_constraint', 'invest_constraint'), (techno, 'investment'),
                    ddelta_dtech / invest_constraint_ref)
                self.set_partial_derivative_for_other_types(
                    ('invest_objective', 'invest_constraint'), (techno, 'investment'), dinvest_objective_dtechno_invest)

                self.set_partial_derivative_for_other_types(
                    ('invest_objective_sum',), (techno, 'investment'), dinvest_objective_sum_dtechno_invest)

                self.set_partial_derivative_for_other_types(
                    ('invest_sum_cons',), (techno, 'investment'),
                    -dinvest_objective_sum_cons_dtechno_invest / delta_years)
                self.set_partial_derivative_for_other_types(
                    ('invest_sum_cons_dc',), (techno, 'investment'), dinvest_objective_sum_cons_dc_dtechno_invest)
                self.set_partial_derivative_for_other_types(
                    ('invest_sum_eq_cons',), (techno, 'investment'), dinvest_eq_cons_dtechno_invest)

                self.set_partial_derivative_for_other_types(
                    ('invest_sum_ineq_cons',), (techno, 'investment'), - dconstrantineq_dtech)


        self.set_partial_derivative_for_other_types(
            ('invest_constraint', 'invest_constraint'), ('energy_investment',
                                                         'energy_investment'),
            ddelta_dtot * scaling_factor_energy_investment / invest_constraint_ref)
        
        self.set_partial_derivative_for_other_types(
                    ('invest_sum_ineq_cons',), ('energy_investment', 'energy_investment'), dconstrantineq_dtech * scaling_factor_energy_investment)
        
        self.set_partial_derivative_for_other_types(
            ('invest_objective', 'invest_objective'), ('energy_investment',
                                                       'energy_investment'),
            dinvest_objective_dtotal_invest * scaling_factor_energy_investment)

        self.set_partial_derivative_for_other_types(
            ('invest_objective_sum',), ('energy_investment', 'energy_investment'),
            dinvest_objective_sum_dtotal_invest * scaling_factor_energy_investment)

        self.set_partial_derivative_for_other_types(
            ('invest_sum_cons',), ('energy_investment', 'energy_investment'),
            -dinvest_objective_sum_cons_dtotal_invest * scaling_factor_energy_investment / delta_years)
        self.set_partial_derivative_for_other_types(
            ('invest_sum_cons_dc',), ('energy_investment', 'energy_investment'),
            dinvest_objective_sum_cons_dc_dtotal_invest * scaling_factor_energy_investment)

        self.set_partial_derivative_for_other_types(
            ('invest_sum_eq_cons',), ('energy_investment', 'energy_investment'),
            -dinvest_eq_cons_dtechno_invest * scaling_factor_energy_investment)

    def compute_dinvest_objective_dinvest(self, techno_invest_sum, invest_tot, invest_objective_ref):
        '''
        Compute derivative of investment objective relative to investment by techno and
        compared to total energy invest
        '''

        delta = (invest_tot - techno_invest_sum) / invest_tot
        abs_delta = np.sqrt(compute_func_with_exp_min(delta ** 2, 1e-15))
        # smooth_delta = np.asarray([smooth_maximum(abs_delta, alpha=10)])
        # invest_objective = abs_delta / invest_objective_ref

        idt = np.identity(len(invest_tot))

        ddelta_dtech = -idt / invest_tot
        ddelta_dtot = (idt * invest_tot - (invest_tot -
                                           techno_invest_sum) * idt) / invest_tot ** 2

        dabs_delta_dtech = 2 * delta / (2 * np.sqrt(compute_func_with_exp_min(
            delta ** 2, 1e-15))) * compute_dfunc_with_exp_min(delta ** 2, 1e-15) * ddelta_dtech
        dabs_delta_dtot = 2 * delta / (2 * np.sqrt(compute_func_with_exp_min(
            delta ** 2, 1e-15))) * compute_dfunc_with_exp_min(delta ** 2, 1e-15) * ddelta_dtot

        dsmooth_delta_dtech = get_dsmooth_dvariable(
            abs_delta, alpha=10) * dabs_delta_dtech.diagonal()
        dsmooth_delta_dtot = get_dsmooth_dvariable(
            abs_delta, alpha=10) * dabs_delta_dtot.diagonal()

        dobj_dtech = dsmooth_delta_dtech / invest_objective_ref
        dobj_dtot = dsmooth_delta_dtot / invest_objective_ref

        return dobj_dtech, dobj_dtot

    def compute_dinvest_objective_sum_dinvest(self, techno_invest_sum, invest_tot, invest_sum_ref):
        '''
        Compute derivative of investment objective relative to investment by techno and
        compared to total energy invest
        '''

        delta = (invest_tot - techno_invest_sum) / invest_sum_ref
        abs_delta = np.sqrt(compute_func_with_exp_min(delta ** 2, 1e-15))
        # smooth_delta = np.asarray([smooth_maximum(abs_delta, alpha=10)])
        # invest_objective = abs_delta

        idt = np.identity(len(invest_tot))

        ddelta_dtech = -idt / invest_sum_ref
        ddelta_dtot = idt / invest_sum_ref

        dabs_delta_dtech = 2 * delta / (2 * np.sqrt(compute_func_with_exp_min(
            delta ** 2, 1e-15))) * compute_dfunc_with_exp_min(delta ** 2, 1e-15) * ddelta_dtech
        dabs_delta_dtot = 2 * delta / (2 * np.sqrt(compute_func_with_exp_min(
            delta ** 2, 1e-15))) * compute_dfunc_with_exp_min(delta ** 2, 1e-15) * ddelta_dtot

        return dabs_delta_dtech, dabs_delta_dtot

    def compute_dinvest_objective_sum_cons_dinvest(self, techno_invest_sum, invest_tot, invest_sum_ref,
                                                   invest_limit_ref):
        '''
        Compute derivative of investment objective relative to investment by techno and
        compared to total energy invest
        '''

        delta = (invest_tot - techno_invest_sum)
        abs_delta = (np.sqrt(compute_func_with_exp_min(
            delta ** 2, 1e-15)) - invest_limit_ref) / invest_sum_ref

        idt = np.identity(len(invest_tot))

        ddelta_dtech = -idt
        ddelta_dtot = idt

        dabs_delta_dtech = 2 * delta / (2 * np.sqrt(compute_func_with_exp_min(
            delta ** 2, 1e-15))) * compute_dfunc_with_exp_min(delta ** 2, 1e-15) * ddelta_dtech / invest_sum_ref
        dabs_delta_dtot = 2 * delta / (2 * np.sqrt(compute_func_with_exp_min(
            delta ** 2, 1e-15))) * compute_dfunc_with_exp_min(delta ** 2, 1e-15) * ddelta_dtot / invest_sum_ref

        return dabs_delta_dtech, dabs_delta_dtot

    def get_chart_filter_list(self):

        chart_filters = []
        chart_list = ['Invest Distribution', 'Delta invest']
        chart_filters.append(ChartFilter(
            'Charts Investments', chart_list, chart_list, 'charts_invest'))

        return chart_filters

    def get_post_processing_list(self, filters=None):

        # For the outputs, making a graph for block fuel vs range and blocktime vs
        # range

        instanciated_charts = []
        charts = []

        # Overload default value with chart filter
        if filters is not None:
            for chart_filter in filters:
                if chart_filter.filter_key == 'charts_invest':
                    charts = chart_filter.selected_values

        if 'Invest Distribution' in charts:
            techno_invests = self.get_sosdisc_inputs(
                'invest_mix')

            chart_name = f'Distribution of investments on each energy vs years'

            new_chart_energy = TwoAxesInstanciatedChart('years', 'Invest [G$]',
                                                        chart_name=chart_name, stacked_bar=True)
            energy_list = self.get_sosdisc_inputs('energy_list')
            ccs_list = self.get_sosdisc_inputs('ccs_list')
            for energy in energy_list + ccs_list:
                techno_list = [
                    col for col in techno_invests.columns if col.startswith(f'{energy}.')]
                short_df = techno_invests[techno_list]
                chart_name = f'Distribution of investments for {energy} vs years'
                new_chart_techno = TwoAxesInstanciatedChart('years', 'Invest [G$]',
                                                            chart_name=chart_name, stacked_bar=True)

                for techno in techno_list:
                    serie = InstanciatedSeries(
                        techno_invests['years'].values.tolist(),
                        short_df[techno].values.tolist(), techno, 'bar')

                    new_chart_techno.series.append(serie)
                instanciated_charts.append(new_chart_techno)
                invest = short_df.sum(axis=1).values
                # Add total price
                serie = InstanciatedSeries(
                    techno_invests['years'].values.tolist(),
                    invest.tolist(), energy, 'bar')

                new_chart_energy.series.append(serie)

            forest_investment = self.get_sosdisc_inputs('forest_investment')
            chart_name = f'Distribution of reforestation investments vs years'
            agriculture_chart = TwoAxesInstanciatedChart('years', 'Invest [G$]',
                                                         chart_name=chart_name, stacked_bar=True)
            serie_agriculture = InstanciatedSeries(
                forest_investment['years'].values.tolist(),
                forest_investment['forest_investment'].values.tolist(), 'Reforestation', 'bar')
            agriculture_chart.series.append(serie_agriculture)
            instanciated_charts.append(agriculture_chart)
            serie = InstanciatedSeries(
                forest_investment['years'].values.tolist(),
                forest_investment['forest_investment'].tolist(), 'Reforestation', 'bar')

            new_chart_energy.series.append(serie)

            if BiomassDry.name in energy_list:
                chart_name = f'Distribution of agriculture sector investments vs years'
                agriculture_chart = TwoAxesInstanciatedChart('years', 'Invest [G$]',
                                                             chart_name=chart_name, stacked_bar=True)

                for techno in ['managed_wood_investment', 'deforestation_investment', 'crop_investment']:
                    invest = self.get_sosdisc_inputs(techno)
                    serie_agriculture = InstanciatedSeries(
                        invest['years'].values.tolist(),
                        invest['investment'].values.tolist(), techno.replace("_investment", ""), 'bar')
                    agriculture_chart.series.append(serie_agriculture)
                    serie = InstanciatedSeries(
                        invest['years'].values.tolist(),
                        invest['investment'].tolist(), techno.replace("_investment", ""), 'bar')
                    new_chart_energy.series.append(serie)
                instanciated_charts.append(agriculture_chart)
                instanciated_charts.insert(0, new_chart_energy)

            instanciated_charts.insert(0, new_chart_energy)
            if 'Delta invest' in charts:

                techno_invests = self.get_sosdisc_inputs(
                    'invest_mix')

                techno_invests_sum = techno_invests[
                    [column for column in techno_invests.columns if column != 'years']].sum(
                    axis=1)
                forest_investment = self.get_sosdisc_inputs(
                    'forest_investment')
                techno_invests_sum += forest_investment['forest_investment']
                if BiomassDry.name in energy_list:
                    for techno in ['managed_wood_investment', 'deforestation_investment', 'crop_investment']:
                        invest = self.get_sosdisc_inputs(techno)
                        techno_invests_sum += invest['investment']
                energy_investment = self.get_sosdisc_inputs(
                    'energy_investment')
                scaling_factor_energy_investment = self.get_sosdisc_inputs(
                    'scaling_factor_energy_investment')

                chart_name = 'Distributed and allocated investments for energy sector '
                new_chart_constraint = TwoAxesInstanciatedChart('years', 'Investments [G$]',
                                                                chart_name=chart_name)
                # , secondary_ordinate_axis_name='Constraint'
                serie = InstanciatedSeries(
                    energy_investment['years'].values.tolist(),
                    (energy_investment['energy_investment'].values *
                     scaling_factor_energy_investment).tolist(),
                    'Total allocated energy investments', )
                new_chart_constraint.series.append(serie)

                serie = InstanciatedSeries(
                    energy_investment['years'].values.tolist(),
                    techno_invests_sum.values.tolist(), 'Sum of distributed investments', )
                new_chart_constraint.series.append(serie)
                instanciated_charts.insert(0, new_chart_constraint)

        return instanciated_charts
