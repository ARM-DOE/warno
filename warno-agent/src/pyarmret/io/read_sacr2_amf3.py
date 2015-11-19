from __future__ import division
import time
import struct
import numpy as np
import os.path

def read_sacr2(filename):
    sacr_file = SACR2File(filename)
    return sacr_file

meta_header_size = 532 + 48
mh_padding = 128
ped_padding = 0
cal_constant_size = 48

class SACR2File(object):
    """Class representing a SACR2 file.

    """

    def __init__(self, filename):
        self.f_h = open(filename, 'r')
        self.file_size = os.path.getsize(filename)

        self._read_info_header()

        # This is an ugly way to do this, but I don't think there is another.
        self.num_moments = SACR2_moment_count[self.mode]
        self.ray_size = int(self.num_moments * self.num_gates * 4)
        header_size = self.f_h.tell()

        payload_size = (self.file_size - header_size)
        self.num_rays = int(payload_size / (self.ray_size + meta_header_size))

        self.moments = np.zeros((self.num_moments, self.num_rays, self.num_gates))
        self.cal_constants = np.zeros((12,self.num_rays))
        self._create_aux_fields()


        read_str = "%df" % self.num_gates

        self._setup_variables()

        self.range= np.arange(0,self.num_gates)* self.config['range_resolution_m']

        for i in range(0, self.num_rays):
            try:
                dyn_vars_i = self._read_meta_header()
                self.f_h.read(ped_padding)
                self.cal_constants[:,i] = struct.unpack("<12f",self.f_h.read(cal_constant_size))

                data_packet = self.f_h.read(self.ray_size)
            except Exception as e:
                print(e)
                break

            self.data_reshaped = np.reshape(np.array(struct.unpack(
                "<" + read_str * self.num_moments, data_packet)),
                (self.num_moments, self.num_gates))

            for moment in range(0,self.num_moments):
                self.moments[moment][i] = self.data_reshaped[moment]

            self._place_dyn_vars(dyn_vars_i, i)

        self.time = 0.5 * (self.sacr2_meta_header['begin_timestamp_seconds'] +\
            self.sacr2_meta_header['end_timestamp_seconds'])

        self._place_moments()

    def _place_dyn_vars(self, dyn_vars, i):
        '''Read the dynamic variables structure and insert it into the object
        '''

        for key in dyn_vars['rcb_status']:
            if 'padding' in key:
                continue
            self.rcb_status[key][i] = dyn_vars['rcb_status'][key]

        for key in dyn_vars['scope_powers']:
            if 'padding' in key:
                continue
            self.scope_powers[key][i] = dyn_vars['scope_powers'][key]

        for key in dyn_vars['orbit_ped_status']:
            if 'padding' in key:
                continue
            self.orbit_ped_status[key][i] = dyn_vars['orbit_ped_status'][key]

        for key in dyn_vars['mcc_priority_status']:
            if 'padding' in key:
                continue
            self.mcc_priority_status[key][i] = dyn_vars['mcc_priority_status'][key]

        for key in dyn_vars['sacr2_meta_header']:
            if 'padding' in key:
                continue
            if key in ['header_cap_id']:
                continue
            self.sacr2_meta_header[key][i] = dyn_vars['sacr2_meta_header'][key]

    def _place_moments(self):
        '''Apply name to moments array
        '''
        mode1_var_list = ['z_vh','reflectivity','v_vh','mean_doppler_velocity','sw_vh','spectral_width']

        mode16_var_list = ['z_vv','z_vh','reflectivity','z_hv','v_vv','v_vh','mean_doppler_velocity',
                           'v_hv','sw_vv','sw_vh','spectral_width','sw_hv']

        mode18_var_list = ['z_vv','z_vh','reflectivity','z_hv','v_vv','v_vh','mean_doppler_velocity',
                           'v_hv','sw_vv','sw_vh','spectral_width','sw_hv', 'unfolded_velocity',
                           'linear_depolarization_ratio','differential_reflectivity',
                           'copol_correlation_coef', 'differential_phase','rho_xh','phi_xh',
                           'rho_xv','phi_xv']


        cal_constant_list = ['ch_v_filtered_sky_noise', 'ch_v_measured_sky_noise',
            'ch_v_measured_cold_noise', 'ch_v_measured_hot_noise', 'ch_v_noise_figure',
            'ch_v_gain', 'ch_h_filtered_sky_noise', 'ch_h_measured_sky_noise',
            'ch_h_measured_cold_noise', 'ch_h_measured_hot_noise', 'ch_h_noise_figure',
            'ch_h_gain']

        self.fields = {}
        self.calibration_constants = {}

        if self.mode in [1,2,3]:
            for idx, key in enumerate(mode1_var_list):
                self.fields[key] = np.array(self.moments[idx])

        elif self.mode in [16,17]:
            for idx, key in enumerate(mode16_var_list):
                self.fields[key] = np.array(self.moments[idx])

        elif self.mode in [18,]:
            for idx, key in enumerate(mode18_var_list):
                self.fields[key] = np.array(self.moments[idx])

        for idx, key in enumerate(cal_constant_list):
            self.calibration_constants[key] = self.cal_constants[idx]

        del(self.cal_constants)


    def to_adi(self):
        '''Convert data structure to prepare for ADI writing. All naming should be consistent with
        PCM

        Returns:
        --------
        variables: dictionary
            Dictionary corresponding to variables to be written
        attributes: dictionary
            Dictionary corresponding to attributes to be written

        '''
        variables = {}
        attributes = {}

        # This will be ugly, just matching to PCM
        # variables['base_time'] = 0
        # variables['time_offset'] = 0
        # variables['time']
        variables['range'] = np.arange(0,self.num_gates) *\
            self.config['range_resolution_effective_m'] + self.config['zero_gate_range_proc_m']

        variables['azimuth'] = self.orbit_ped_status['az_pos']
        variables['elevation'] = self.orbit_ped_status['el_pos']
        variables['scan_rate'] = np.sqrt(np.power(self.orbit_ped_status['az_vel'],2) +\
            np.power(self.orbit_ped_status['el_vel'],2) )
        variables['antenna_transition'] = self.orbit_ped_status['transition_flag']
        variables['reflectivity'] = self.fields['reflectivity']
        variables['mean_doppler_velocity'] = self.fields['mean_doppler_velocity']
        variables['spectral_width'] = self.fields['spectral_width']
        variables['snr'] = np.zeros(self.fields['spectral_width'].size) # Need to Calculate this
        variables['linear_depolarization_ratio'] = self.fields['linear_depolarization_ratio']
        # variables['co_to_crosspol_correlation_coeff'] = self.fields['co_to_crosspol_correlation_coeff']
        # variables['cross_polar_differential_phase'] =
        variables['prt'] = self.config['pri_total_ns'] * 1e9
        variables['pulse_width'] = self.config['tx_pulse_width_ns'] * 1e9
        variables['nyquist_velocity'] = self.config['max_velocity_m_sec']
        variables['unambiguous_range'] = self.config['max_sampled_range_m']
        # variables['n_samples'] = self.config['post_avg_len'] * self.config['fft_len']
        if self.mode is 18:
            variables['n_samples'] = self.config['clutter_avg_len'] * 5

        variables['volume_number'] = 0
        variables['frequency'] =self.config['tx_freq_hz']
        # variables['sweep_number'] =
        # variables['fixed_angle'] =
        # variables['sweep_start_ray_index']
        # variables['sweep_end_ray_index']
        # variables['follow_mode']
        # variables['sweep_mode'] =
        # variables['prt_mode']
        # variables['polarization_mode'] =
        # variables['radar_antenna_gain_h'] =
        # variables['radar_antenna_gain_v'] =
        # variables['radar_beam_width_h'] =
        # variables['radar_beam_width_v']
        variables['radar_measured_transmit_power_h'] = self.calibration['tx_power_dbm']
        # variables['platform_type']
        # variables['instrument_type']
        # variables['primary_axis']
        # variables['time_coverage_start']
        # variables['time_coverage_end']
        # variables['r_calib_index']
        # variables['r_calib_time']
        # variables['r_calib_pulse_width']
        # variables['r_calib_two_way_radome_loss_h']
        # variables['r_calib_xmit_power_h']
        # variables['r_calib_receiver_gain_hc']
        # variables['r_calib_receiver_gain_vx']
        # variables['r_calib_noise_hc']
        # variables['r_calib_noise_vx']
        # variables['r_calib_noise_source_power_h']
        # variables['r_calib_noise_source_power_v']
        # variables['r_calib_radar_constant_h']
        # variables['r_calib_radar_constant_v']
        # variables['sky_noise_copol'] = self.calibration
        # variables['sky_noise_xpol']
        # variables['sky_power_copol']
        # variables['sky_power_xpol']
        # variables['latitude']
        # variables['longitude']
        # variables['altitude']
        # variables['altitude_agl']
        # variables['lat']
        # variables['lon']
        # variables['alt']


        attributes['asp_chan_1_enabled'] = self.config['asp_chan_1_enabled']
        attributes['asp_chan_2_enabled'] = self.config['asp_chan_2_enabled']
        # attributes['sampling_interval'] =
        # attributes['averaging_interval']
        attributes['chirp_attenuation'] = self.config['chirp_attenuation_db']
        attributes['clutter_filter_enabled'] = self.config['clutter_filter_enabled']
        attributes['double_hop_enabled'] = self.config['double_hop_enabled']
        attributes['fft_len'] = self.config['fft_len']

        return variables, attributes


    def _setup_variables(self):
        self.dyn_vars = {}
        self.rcb_status = {}
        self.scope_powers = {}
        self.orbit_ped_status = {}
        self.mcc_priority_status = {}
        self.sacr2_meta_header = {}

        for key in rcb_status_t:
            self.rcb_status[key[0]] = np.zeros(self.num_rays)
        for key in scope_powers_t:
            self.scope_powers[key[0]] = np.zeros(self.num_rays)
        for key in orbit_ped_status_t:
            self.orbit_ped_status[key[0]] = np.zeros(self.num_rays)
        for key in mcc_priority_status_t:
            self.mcc_priority_status[key[0]] = np.zeros(self.num_rays)
        for key in sacr2_meta_header_t:
            self.sacr2_meta_header[key[0]] = np.zeros(self.num_rays)


    def _read_meta_header(self):
        ''' Read metaheaders from ProSensing Data Format, and return dictionary
        '''

        sacr2_meta_header = self._unpack_structure(
            self.f_h.read(self._struct_size(sacr2_meta_header_t)), sacr2_meta_header_t)
            # Rds status
        rcb_status = self._unpack_structure(
            self.f_h.read(self._struct_size(rcb_status_t)), rcb_status_t)
        scope_powers = self._unpack_structure(
            self.f_h.read(self._struct_size(scope_powers_t)), scope_powers_t)
        orbit_ped_status = self._unpack_structure(
            self.f_h.read(self._struct_size(orbit_ped_status_t)), orbit_ped_status_t)
        self.f_h.read(mh_padding)  # Padding

            # mcc priority status
        mcc_priority_status = self._unpack_structure(
            self.f_h.read(self._struct_size(mcc_priority_status_t)), mcc_priority_status_t)

        return {'sacr2_meta_header':sacr2_meta_header, 'rcb_status':rcb_status,
            'scope_powers': scope_powers, 'orbit_ped_status':orbit_ped_status,
            'mcc_priority_status': mcc_priority_status}

    def _read_info_header(self):
        ''' Read the file_header structures for Prosensing format data file
        '''

        top_size = self._struct_size(sacr2_file_header_top_t)
        self.file_header_top = self._unpack_structure(
            self.f_h.read(top_size), sacr2_file_header_top_t)

        self.config = self._unpack_structure(self.f_h.read(self._struct_size(config_t)),
                                             config_t)

        self.private_config = self._unpack_structure(
            self.f_h.read(self._struct_size(private_config_t)), private_config_t)

        self.calibration = self._unpack_structure(
            self.f_h.read(self._struct_size(calibration_t)), calibration_t)

        bot_size = self._struct_size(sacr2_file_header_bot_t)
        self.file_header_bot = self._unpack_structure(
            self.f_h.read(bot_size), sacr2_file_header_bot_t)

        self.mode = self.config['server_mode']
        self.num_gates = self.file_header_bot['n_gates_proc']

        self.file_header_size = self.f_h.tell()


    def _unpack_structure(self, string, structure, offset=0):
        ''' Unpack a structure according to definition string. Calculates data read size from
        the structure string.

        Parameters:
        -----------
        string: string
            Datastring containing binary data.
        structure: list
            Structure definition in a packed list format.
        offset: optional, integer
            Offset in the string to parse from.

        Returns:
        --------
        read_struct: dictionary
            Dictionary with key-value pairs representing the structure in `structure`

        '''
        fmt = '<' + ''.join([i[1] for i in structure])
        tpl = struct.unpack(fmt, string[offset:offset + struct.calcsize(fmt)])
        return dict(zip([i[0] for i in structure], tpl))

    def _struct_size(self, structure):
        ''' Calculate size of a structure definition list.

        Parameters:
        ------------
        structure: list
            List containing structure definition.

        Returns:
        --------
        size: integer
            Size of the structure in bytes.
        '''
        fmt = '<' + ''.join([i[1] for i in structure])
        return struct.calcsize(fmt)

    def _safe_convert_value(self, value):
        ''' Safely convert a floating point value from string. If not a float, returns the string.

        Parameters:
        -----------
        value: string
            String to convert into a float

        Returns:
        --------
        value: float/string
            Returns a float if string represents a float, otherwise returns original stirng.
        '''
        try:
            val = float(value)
            return val
        except ValueError:
            return value
        return value  # This should be unreachable

    def _create_aux_fields(self):
        self.time = np.zeros(self.num_rays)
        self.azimuth = np.zeros(self.num_rays)
        self.elevation = np.zeros(self.num_rays)
        self.azimuth_cycle_cnt = np.zeros(self.num_rays)
        self.elevation_cycle_cnt = np.zeros(self.num_rays)
        self.program_cycle_cnt = np.zeros(self.num_rays)
        self.drive_power = np.zeros(self.num_rays)
        self.output_power = np.zeros(self.num_rays)
        self.sweep_number = np.zeros(self.num_rays)
        self.sweep_mode = np.zeros(self.num_rays)
        self.fixed_angle = np.zeros(self.num_rays)
        self.antenna_transition = np.zeros(self.num_rays)
        self.azimuth_velocity = np.zeros(self.num_rays)
        self.elevation_velocity = np.zeros(self.num_rays)
        self.azimuth_total_distance= np.zeros(self.num_rays)
        self.elevation_total_distance = np.zeros(self.num_rays)
        self.roll = np.zeros(self.num_rays)


moment_dict_base = ['z_vh','z_hh','v_vh','v_hh','sw_vh','sw_hh']
moment_dict_higher_modes = ['z_vv','z_vh','z_hh','z_hv','f']

SACR2_moment_count = {
        1 : 6,
        2 : 6,
        3 : 6,
        16 : 12,
        17 : 12,
        18 : 21
        }

sacr2_file_header_top_t = (
    ("header_cap_id", "4s"),
    ("header_cap_index", "l"),
    ("header_cap_size", "l"),
    ("version_major", "l"),
    ("version_minor", "l"),
    ("version_patch", "l"),
    ("file_type", "l"))

sacr2_file_header_bot_t = (
    ("asp_waveform", "32768s"),
    ("cal_constant_in_use_h_copol", "d"),
    ("cal_constant_in_use_h_crosspol", "d"),
    ("cal_constant_in_use_v_copol", "d"),
    ("cal_constant_in_use_v_crosspol", "d"),
    ("n_gates_proc", "l"),
    ("sacr2_file_header_padding", "43048s"
    ))


config_t = (
    ("ad_skip_count", "l"),
    ("ad_skip_count_override", "l"),
    ("ad_trig_delay_ns", "q"),
    ("ad_trig_delay_override_ns", "q"),
    ("asp_chan_1_enabled", "?"),
    ("asp_chan_2_enabled", "?"),
    ("asp_hop_phase_offsets_file_name", "256s"),
    ("asp_trig_delay_1_ns", "q"),
    ("asp_trig_delay_1_override_ns", "q"),
    ("asp_trig_delay_2_ns", "q"),
    ("asp_trig_delay_2_override_ns", "q"),
    ("asp_waveform_chan_1_file_path", "256s"),
    ("asp_waveform_chan_2_file_path", "256s"),
    ("auto_calculate_noise_regions", "?"),
    ("blanking_override", "l"),
    ("cal_constant_h_copol", "d"),
    ("cal_constant_h_crosspol", "d"),
    ("cal_constant_v_copol", "d"),
    ("cal_constant_v_crosspol", "d"),
    ("cal_switch_delay_1_ns", "q"),
    ("cal_switch_delay_2_ns", "q"),
    ("cal_switch_enabled", "?"),
    ("cal_switch_enabled_effective", "?"),
    ("cal_switch_width_1_ns", "q"),
    ("cal_switch_width_2_ns", "q"),
    ("center_main_bang_ns", "q"),
    ("chirp_amplitude_scaling", "d"),
    ("chirp_attenuation_db", "d"),
    ("chirp_attenuation_db_user", "d"),
    ("chirp_bandwidth_hz", "d"),
    ("chirp_center_freq_hz", "d"),
    ("chirp_delay_ns", "q"),
    ("chirp_pulse_width_ns", "q"),
    ("chirp_tukey_coef", "d"),
    ("chirp_tukey_coef_effective", "d"),
    ("chirp_tukey_correction", "d"),
    ("clutter_avg_len", "l"),
    ("clutter_filter_enabled", "?"),
    ("coherent_on_recv_before_sw_filter", "?"),
    ("coherent_on_recv_gate_h", "l"),
    ("coherent_on_recv_gate_v", "l"),
    ("cold_noise_region_len", "l"),
    ("cold_noise_region_offset", "l"),
    ("dec_clk_hz", "d"),
    ("dec_fir_filter_delay_ns", "q"),
    ("digrcv_filter_bandwidth_hz", "d"),
    ("digrcv_filter_bandwidth_effective_hz", "d"),
    ("digrcv_fir_dec", "l"),
    ("digrcv_fir_dec_effective", "l"),
    ("double_hop_enabled", "?"),
    ("double_hop_enabled_override", "?"),
    ("ems_1_manual", "?"),
    ("ems_1_override", "?"),
    ("ems_1_override_effective", "?"),
    ("ems_2_manual", "?"),
    ("ems_delay_ns", "q"),
    ("ems_delay_override_ns", "q"),
    ("ems_end_ns", "q"),
    ("enable_all_preproc_peekers", "?"),
    ("enable_coherent_on_receive", "?"),
    ("enable_data_trimming", "?"),
    ("enable_data_trimming_user", "?"),
    ("enable_duty_cycle_software_protection", "?"),
    ("enable_group_hopping", "?"),
    ("enable_pulse_compression_filter", "?"),
    ("enable_windower", "?"),
    ("external_ps_sync_desired_delay_ns", "q"),
    ("external_ps_sync_desired_freq_hz", "d"),
    ("fft_len", "l"),
    ("fft_taper", "l"),
    ("file_name_suffix", "16s"),
    ("hardware_dec", "l"),
    ("hop_center_freq_hz", "d"),
    ("hop_delay_1_ns", "q"),
    ("hop_delay_1_override_ns", "q"),
    ("hop_delay_2_ns", "q"),
    ("hop_delay_2_override_ns", "q"),
    ("hop_delta_freq_hz", "d"),
    ("hop_delta_freq_override_hz", "d"),
    ("hop_trigger_mode", "l"),
    ("hop_trigger_mode_override", "l"),
    ("hot_noise_region_len", "l"),
    ("hot_noise_region_offset", "l"),
    ("integration_time_ns", "q"),
    ("is_sync_slave", "?"),
    ("max_duty_cycle", "d"),
    ("max_sampled_range_m", "d"),
    ("max_velocity_m_sec", "d"),
    ("moments_noise_subtraction_scale_factor", "d"),
    ("n_gates", "l"),
    ("n_group_pulses", "l"),
    ("n_hops", "l"),
    ("n_pri_groups", "l"),
    ("noise_delay_ns", "q"),
    ("noise_delay_override_ns", "q"),
    ("noise_scale_factor_h", "d"),
    ("noise_scale_factor_h_effective", "d"),
    ("noise_scale_factor_v", "d"),
    ("noise_scale_factor_v_effective", "d"),
    ("noise_source", "l"),
    ("noise_source_1_override", "?"),
    ("noise_source_2_override", "?"),
    ("noise_width_ns", "q"),
    ("noise_width_override_ns", "q"),
    ("post_avg_len", "l"),
    ("ppp_moments_uses_crt_velocity_algorithm", "?"),
    ("pri_1_ns", "q"),
    ("pri_2_ns", "q"),
    ("pri_3_ns", "q"),
    ("pri_4_ns", "q"),
    ("pri_group_ns", "q"),
    ("pri_total_ns", "q"),
    ("pulse_compression_ratio", "d"),
    ("pulse_compression_ratio_effective", "d"),
    ("range_gate_spacing_post_sw_dec_m", "d"),
    ("range_gate_spacing_pre_sw_dec_m", "d"),
    ("range_resolution_m", "d"),
    ("range_resolution_effective_m", "d"),
    ("server_mode", "l"),
    ("server_state", "l"),
    ("signal_region_len", "l"),
    ("signal_region_offset", "l"),
    ("sky_noise_region_len", "l"),
    ("sky_noise_region_offset", "l"),
    ("software_dec", "l"),
    ("software_filter_real", "8192s"),
    ("software_filter_imag", "8192s"),
    ("software_filter_delay", "l"),
    ("software_filter_file_path", "256s"),
    ("software_filter_len", "l"),
    ("software_filter_output_len_samps", "l"),
    ("software_filter_output_offset_index", "l"),
    ("software_filter_output_trim_back", "l"),
    ("software_filter_output_trim_front", "l"),
    ("software_filter_power_threshold_ratio", "d"),
    ("software_filter_untrimmed_output_len", "l"),
    ("switch_1_protect", "?"),
    ("switch_2_protect", "?"),
    ("total_avg_len", "l"),
    ("tx_freq_hz", "d"),
    ("tx_pulse_bracketing_ns", "q"),
    ("tx_pulse_bracketing_override_ns", "q"),
    ("tx_pulse_width_ns", "q"),
    ("tx_trigger_delay_ns", "q"),
    ("tx_trigger_delay_override_ns", "q"),
    ("tx_trigger_enabled", "?"),
    ("tx_trigger_enabled_effective", "?"),
    ("use_digrcv_default_filter", "?"),
    ("use_digrcv_default_filter_effective", "?"),
    ("use_software_filter_parameters", "?"),
    ("velocity_spacing_m_sec", "d"),
    ("whole_noise_region_len", "l"),
    ("whole_noise_region_offset", "l"),
    ("zero_gate_range_proc_m", "d"),
    ("zero_gate_range_raw_m", "d"),
    ("zero_gate_time_proc_ns", "q"),
    ("zero_gate_time_raw_ns", "q"
    ))
private_config_t = (
    ("apply_compression_gain_compensation_to_cal_constant", "?"),
    ("asp_accepts_large_hop_count", "?"),
    ("asp_clock_rate_hz", "d"),
    ("asp_net_addr", "16s"),
    ("asp_net_port", "l"),
    ("beamwidth_phi_deg_ch_h", "d"),
    ("beamwidth_phi_deg_ch_v", "d"),
    ("beamwidth_theta_deg_ch_h", "d"),
    ("beamwidth_theta_deg_ch_v", "d"),
    ("chirp_attenuation_offset_db", "d"),
    ("custom_file_prefix", "16s"),
    ("data_file_dir_moments", "256s"),
    ("data_file_dir_pp", "256s"),
    ("data_file_dir_raw", "256s"),
    ("data_file_dir_spectra", "256s"),
    ("data_file_max_size", "q"),
    ("debug_asp_ch_1_always_cw", "?"),
    ("debug_asp_ch_2_always_cw", "?"),
    ("debug_asp_timing_messages", "?"),
    ("debug_digrcv_acq_data", "?"),
    ("debug_digrcv_config", "?"),
    ("debug_digrcv_data_rate", "?"),
    ("debug_digrcv_raw_data_copier", "?"),
    ("debug_digrcv_raw_proc_chunk_output", "?"),
    ("debug_digrcv_timestamp_interpolator", "?"),
    ("debug_input_gatherer_dropped_chunks", "?"),
    ("debug_meta_header_timestamps", "?"),
    ("debug_net_server", "?"),
    ("debug_pacsi_program_exec", "?"),
    ("debug_processing_pipeline_activity", "?"),
    ("debug_rcb_write_msg", "?"),
    ("debug_scope_data", "?"),
    ("dielectric_factor", "d"),
    ("digrcv_fir_gain_ch_h", "d"),
    ("digrcv_fir_gain_ch_v", "d"),
    ("digrcv_nco_freq_hz", "d"),
    ("digrcv_sample_clock_hz", "d"),
    ("enable_averaging", "?"),
    ("enable_cross_spectra", "?"),
    ("enable_gain_noise_figure_modules", "?"),
    ("enable_modulator_monitor", "?"),
    ("enable_moments_calc", "?"),
    ("enable_noise_filter_modules", "?"),
    ("enable_noise_pwr_modules", "?"),
    ("enable_ped_current_status", "?"),
    ("enable_power_spectra", "?"),
    ("enable_pp_moments_calc", "?"),
    ("enable_rcb_idle_on_exit", "?"),
    ("enable_zeroth_moment_dbz", "?"),
    ("finite_bandwidth_loss_db_ch_h", "d"),
    ("finite_bandwidth_loss_db_ch_v", "d"),
    ("gain_db_ch_h", "d"),
    ("gain_db_ch_v", "d"),
    ("have_asp", "?"),
    ("have_digrcv", "?"),
    ("have_pdu", "?"),
    ("have_pedestal", "?"),
    ("have_rcb", "?"),
    ("have_scope_card", "?"),
    ("hop_freq_internal_delay_ns", "q"),
    ("host_name", "16s"),
    ("listen_port", "l"),
    ("log_to_stderr", "?"),
    ("max_asp_configuration_attempts", "l"),
    ("max_fft_prime_factor", "l"),
    ("max_file_size", "q"),
    ("mc_srv_addr", "16s"),
    ("mc_srv_port", "l"),
    ("mc_srv_priority_status_port", "l"),
    ("mc_status_cycle_period_ns", "q"),
    ("modulator_max_ready_wait_time_ns", "q"),
    ("modulator_monitor_cycle_period_ns", "q"),
    ("modulator_pdu_outlet_index", "l"),
    ("modulator_post_high_voltage_off_delay_ns", "q"),
    ("modulator_post_pdu_outlet_on_delay_ns", "q"),
    ("modulator_power_restore_delay_ns", "q"),
    ("modulator_ready_wait_fault_grace_period_ns", "q"),
    ("moments_pwr_threshold_db", "d"),
    ("n_processing_threads", "l"),
    ("noise_source_enr_ch_h", "d"),
    ("noise_source_enr_ch_v", "d"),
    ("path_loss_to_lna_ch_h", "d"),
    ("path_loss_to_lna_ch_v", "d"),
    ("pdu_net_addr", "16s"),
    ("ped_device_path", "64s"),
    ("ped_offset_az", "d"),
    ("ped_offset_el", "d"),
    ("ped_read_only", "?"),
    ("ped_status_time_offset_ns", "q"),
    ("probert_jones_correction_db", "d"),
    ("radar_constant_offset_db_ch_h", "d"),
    ("radar_constant_offset_db_ch_v", "d"),
    ("radar_constant_offset_flag", "l"),
    ("radar_type", "16s"),
    ("radome_loss_twoway_db", "d"),
    ("rcb_net_addr", "16s"),
    ("rcb_net_port", "l"),
    ("rcb_status_init_timeout_ns", "q"),
    ("rcb_timing_message_out_file", "256s"),
    ("scope_drive_channel_coupling_factor_db", "d"),
    ("scope_drive_channel_lookup_file_path", "256s"),
    ("rx_path_loss_db_ch_h", "d"),
    ("rx_path_loss_db_ch_v", "d"),
    ("scope_output_channel_coupling_factor_db", "d"),
    ("scope_output_channel_lookup_file_path", "256s"),
    ("scope_net_addr", "16s"),
    ("scope_net_port", "l"),
    ("system_type", "16s"),
    ("toggle_modulator_pdu_outlet_on_fault", "?"),
    ("tx_blanking_ped_regions", "256s"),
    ("tx_path_loss_db_ch_h", "d"),
    ("tx_path_loss_db_ch_v", "d"),
    ("use_pacsi_init_file", "?"),
    ("private_config_padding", "5500s"
    ))

calibration_t = (
    ("tx_power_dbm", "d"),
    ("rx_gain_db_ch_h", "d"),
    ("rx_gain_db_ch_v", "d"),
    ("rx_noise_dbm_ch_h", "d"),
    ("rx_noise_dbm_ch_v", "d"),
    ("noise_source_dbm_ch_h", "d"),
    ("noise_source_dbm_ch_v", "d"),
    ("default_cal_constant_h_copol", "d"),
    ("default_cal_constant_h_crosspol", "d"),
    ("default_cal_constant_v_copol", "d"),
    ("default_cal_constant_v_crosspol", "d"
    ))

rcb_status_t = (
    ("minus_five_vdc", "f"),
    ("five_vdc", "f"),
    ("five_point_two_vdc", "f"),
    ("eight_vdc", "f"),
    ("twelve_vdc", "f"),
    ("fifteen_vdc", "f"),
    ("twenty_eight_vdc", "f"),
    ("incl_pitch", "f"),
    ("incl_roll", "f"),
    ("rf_unit_temp", "f"),
    ("reverse_pwr_load_temp", "f"),
    ("lna_xpol_temp", "f"),
    ("lna_copol_temp", "f"),
    ("coolant_supply_temp", "f"),
    ("rtd6", "f"),
    ("rtd7", "f"),
    ("rtd8", "f"),
    ("outside_air_temp", "f"),
    ("power_supply_temp", "f"),
    ("modulator_external_temp", "f"),
    ("eika_temp", "f"),
    ("coolant_return_temp", "f"),
    ("rtd14", "f"),
    ("rtd15", "f"),
    ("rtd16", "f"),
    ("rcb_temp", "f"),
    ("rcb_humidity", "f"),
    ("antenna_temp", "f"),
    ("modulator_temp", "f"),
    ("antenna_humidity", "f"),
    ("plo1_lock_status", "?"),
    ("plo2_lock_status", "?"),
    ("plo3_lock_status", "?"),
    ("plo4_lock_status", "?"),
    ("modulator_filament_delay", "?"),
    ("modulator_power_valid", "?"),
    ("modulator_fault_interlock", "?"),
    ("modulator_fault_transmitter_temp", "?"),
    ("modulator_fault_mod", "?"),
    ("modulator_fault_sync", "?"),
    ("modulator_fault_sum", "?"),
    ("modulator_power_on_command", "?"),
    ("modulator_hv_on_command", "?"),
    ("modulator_fault_time_interlock_seconds", "L"),
    ("modulator_fault_time_interlock_nanoseconds", "L"),
    ("modulator_fault_time_transmitter_temp_seconds", "L"),
    ("modulator_fault_time_transmitter_temp_nanoseconds", "L"),
    ("modulator_fault_time_mod_seconds", "L"),
    ("modulator_fault_time_mod_nanoseconds", "L"),
    ("modulator_fault_time_sync_seconds", "L"),
    ("modulator_fault_time_sync_nanoseconds", "L"),
    ("modulator_fault_time_sum_seconds", "L"),
    ("modulator_fault_time_sum_nanoseconds", "L"),
    ("sacr2_rcb_status_padding", "128s"
    ))
scope_powers_t = (
    ("drive_power_dbm", "d"),
    ("output_power_dbm", "d"
    ))
orbit_ped_status_t = (
    ("az_mode", "l"),
    ("el_mode", "l"),
    ("az_pos", "f"),
    ("el_pos", "f"),
    ("az_vel", "f"),
    ("el_vel", "f"),
    ("az_current", "f"),
    ("el_current", "f"),
    ("az_at_ccw_hardware_limit", "?"),
    ("az_at_cw_hardware_limit", "?"),
    ("az_at_ccw_software_limit", "?"),
    ("az_at_cw_software_limit", "?"),
    ("el_at_ccw_hardware_limit", "?"),
    ("el_at_cw_hardware_limit", "?"),
    ("el_at_ccw_software_limit", "?"),
    ("el_at_cw_software_limit", "?"),
    ("sweep_count", "l"),
    ("transition_flag", "?"
    ))

mcc_priority_status_t = (
    ("timestamp_seconds", "L"),
    ("timestamp_nanoseconds", "L"),
    ("ped_sweep_count", "l"),
    ("ped_transition_flag", "?"
    ))

sacr2_meta_header_t = (
    ("header_cap_id", "4s"),
    ("header_cap_index", "l"),
    ("header_cap_size", "l"),
    ("begin_timestamp_seconds", "L"),
    ("begin_timestamp_nanoseconds", "L"),
    ("end_timestamp_seconds", "L"),
    ("end_timestamp_nanoseconds", "L"),
    ("rcb_status_valid", "?"))

if __name__ == '__main__':
    radar = read_sacr2('/Volumes/hard_lacie_hfs/data/amf3/ACMEV/sacr2/Ka/Ka_PP_MOMENTS_20150828-095124.cwrhi')
