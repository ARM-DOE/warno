#!/usr/bin/env python
import struct
import numpy as np
import sys
#from netCDF4 import Dataset


class IWRFFile(object):
    """
    This class makes a few assumptions. First, we assume that number of gates is fixed for now.
    We assume 2 polarization, complex iq data
    """

    def __init__(self, filename):
        self.fh = open(filename, 'rb')
        self.detect_endian()
        self.fh.seek(0)
        self.iq_data_h = []
        self.iq_data_v = []

        self.num_channels = 2  # Just fix this for now, we can update in future

        self.headers = {x[0]: [] for x in irwf_pulse_header}

    def read_file(self):

        packet = True
        while True:
            packet = self.read_packet()
            if packet is None:
                break
            if packet[0]['id'] == 0x7777000c:
                self.iq_data_h.append(packet[2][:, 0])
                self.iq_data_v.append(packet[2][:, 1])
                for header in self.headers:
                    self.headers[header].append(packet[1][header])

        self.iq_data_h = np.array(self.iq_data_h, dtype=complex)
        self.iq_data_v = np.array(self.iq_data_v, dtype=complex)

        for header in self.headers:
            self.headers[header] = np.array(self.headers[header])

        self.fh.seek(0)

    def read_packet(self):
        offset = 0
        buffer = []
        packet_data = None
        packet_payload = None

        buffer = self.fh.read(56)
        if len(buffer) is 0:
            return None

        packet_header = self._unpack_structure(buffer, iwrf_packet_info)

        buffer = self.fh.read(packet_header['len_bytes'] - 56)
        id = packet_header['id']
        if id in packet_type:
            packet_payload = self._unpack_structure(buffer, packet_type[id])
        else:
            print("Unknown Packet Type %d" % id)

        if id == 0x7777000c:
            packet_data = np.zeros(
                (packet_payload['n_gates'], packet_payload['n_channels']), dtype=complex)
            offset += self._struct_size(packet_type[id])
            data_fmt_str = self.endian + str(packet_payload['n_data']) + 'f'
            data_buffer = np.array(
                struct.unpack(data_fmt_str, buffer[offset:]))
            # At this point we should split out burst pulse?
            for channel in range(1, 1 + packet_payload['n_channels']):
                start_gate = packet_payload['iq_offset_%d' % channel]
                num_gates = packet_payload['n_gates'] * 2
                row = data_buffer[start_gate:start_gate + num_gates]
                packet_data[:, channel - 1] = row[::2] + row[1::2] * 1j

        return (packet_header, packet_payload, packet_data)

    def detect_endian(self):
        "Call at beginning of file reading to determine endianness"
        self.endian = '<'
        id = self.fh.read(4)
        uid = struct.unpack("<i", id)[0]
        euid = struct.unpack(">i", id)[0]

        if uid < 0x77770fff and uid > 0x77770000:
            print('Native Endian')
            self.endian = '<'
        elif euid < 0x77770fff and uid > 0x77770000:
            print("other endian")
            self.endian = ">"

    def _unpack_structure(self, string, structure, offset=0):
        """ Unpack a structure """
        fmt = self.endian + ''.join([i[1] for i in structure])
        tpl = struct.unpack(fmt, string[offset:offset + struct.calcsize(fmt)])
        return dict(zip([i[0] for i in structure], tpl))

    def _struct_size(self, structure):
        """ Unpack a structure """
        fmt = self.endian + ''.join([i[1] for i in structure])
        return struct.calcsize(fmt)

    def write_to_nc(self, filename):
        pass
        # rootgrp = Dataset(filename, 'w', format='NETCDF4')
        # gate = rootgrp.createDimension('gate', None)
        # ray = rootgrp.createDimension('ray', None)

        # pulse_headers = {}
        # pulse_headers['pulse_seq_num'] = rootgrp.createVariable('pulse_seq_num', 'i8', ('ray'))
        # pulse_headers['pulse_seq_num'][:] = self.headers['pulse_seq_num']
        # # For 'i4' entries
        # header_ints = [x[0] for x in irwf_pulse_header if x[1] == 'i']
        # for hi in header_ints:
        #     pulse_headers[hi] = rootgrp.createVariable(hi, 'i4', ('ray'))
        #     pulse_headers[hi][:] = self.headers[hi]

        # # For 'f4' entries
        # header_floats = [x[0] for x in irwf_pulse_header if x[1] == 'f']
        # for hf in header_floats:
        #     pulse_headers[hf] = rootgrp.createVariable(hf, 'f4', ('ray'))
        #     pulse_headers[hf][:] = self.headers[hf]

        # pulse_headers['unused'] = rootgrp.createVariable('unused', str, ('ray'))
        # pulse_headers['unused'][:] = self.headers['unused']

        # iq_h_real = rootgrp.createVariable('iq_h_real', 'f4', ('ray', 'gate'))
        # iq_h_imag = rootgrp.createVariable('iq_h_imag', 'f4', ('ray', 'gate'))
        # iq_v_real = rootgrp.createVariable('iq_v_real', 'f4', ('ray', 'gate'))
        # iq_v_imag = rootgrp.createVariable('iq_v_imag', 'f4', ('ray', 'gate'))

        # iq_h_real[:] = np.real(self.iq_data_h)
        # iq_h_imag[:] = np.imag(self.iq_data_h)
        # iq_v_real[:] = np.real(self.iq_data_v)
        # iq_v_imag[:] = np.imag(self.iq_data_v)


iwrf_packet_info = (
    ("id", "i"),
    ("len_bytes", "i"),
    ("seq_num", "l"),
    ("version_num", "i"),
    ("radar_id", "i"),
    ("time_secs_utc", "q"),
    ("time_nano_secs_utc", "i"),
    ("reserved", "5i")
)

iwrf_sync = (
    ("magic_code1", "i"),  # Should be 0x2a2a2a2a
    ("magic_code2", "i")  # Should be 0x7e7e7e7e
)

iwrf_radar_info = (
    ("latitude_deg", "f"),
    ("longitude_deg", "f"),
    ("altitude", "f"),
    ("platform_type", "i"),
    ("beamwidth_deg_h", "f"),
    ("beamwidth_deg_v", "f"),
    ("wavelength_cm", "f"),
    ("nominal_gain_ant_db_h", "f"),
    ("nominal_gain_ant_db_v", "f"),
    ("unused", "25f"),
    ("radar_name", "32s"),
    ("site_name", "32s")
)


iwrf_scan_segment = (
    ("scan_mode", "i"),
    ("follow_mode", "i"),
    ("volume_num", "i"),
    ("sweep_num", "i"),
    ("time_limit", "i"),
    ("az_manual", "f"),
    ("el_manual", "f"),
    ("az_start", "f"),
    ("el_start", "f"),
    ("scan_rate", "f"),
    ("left_limit", "f"),
    ("right_limit", "f"),
    ("up_limit", "f"),
    ("down_limit", "f"),
    ("step", "f"),
    ("current_fixed_angle", "f"),
    ("init_direction_cw", "i"),
    ("init_direction_up", "i"),
    ("n_sweeps", "i"),
    ("fixed_angles", "512f"),
    ("optimizer_rmax_km", "f"),
    ("optimizer_htmax_km", "f"),
    ("optimizer_res_m", "f"),
    ("sun_scan_sector_width_az", "f"),
    ("sun_scan_sector_width_el", "f"),
    ("unused", "458f"),
    ("segment_name", "32s"),
    ("project_name", "32s")
)

iwrf_antenna_correction = (
    ("az_correction", "f"),
    ("el_correctoin", "f"),
    ("unused", "16f")
)

iwrf_ts_processing = (
    ("xmit_rcv_mode", "i"),
    ("xmit_phase_mode", "i"),
    ("prf_mode", "i"),
    ("pulse_type", "i"),
    ("prt_usec", "f"),
    ("prt2_usec", "f"),
    ("cal_type", "i"),
    ("burst_range_offset_m", "f"),
    ("pulse_width_us", "f"),
    ("start_range_m", "f"),
    ("gate_spacing_m", "f"),
    ("integration_cycle_pulses", "i"),
    ("clutter_filter_number", "i"),
    ("range_gate_averaging", "i"),
    ("test_power_dbm", "f"),
    ("test_pulse_range_km", "f"),
    ("test_pulse_length_usec", "f"),
    ("pol_mode", "i"),
    ("xmit_flag_1", "i"),
    ("xmit_flag_2", "i"),
    ("beams_are_indexed", "i"),
    ("specify_dwell_width", "i"),
    ("indexed_beam_width_deg", "f"),
    ("indexed_beam_spacing_deg", "f"),
    ("num_prts", "i"),
    ("prt3_usec", "f"),
    ("prt4", "f"),
    ("block_mode_prt2_pulses", "i"),
    ("block_mode_prt3_pulses", "i"),
    ("block_mode_prt4_pulses", "i"),
    ("pol_sync_mode", "I"),
    ("unused", "18f")
)


iwrf_xmit_power = (
    ("power_dbm_h", "f"),
    ("power_dbm_v", "f"),
    ("unused", "16f")
)

iwrf_xmit_sample = (
    ("power_dbm_h", "f"),
    ("power_dbm_v", "f"),
    ("offset", "i"),
    ("n_samples", "i"),
    ("sampling_freq", "f"),
    ("scale_h", "f"),
    ("offset_h", "f"),
    ("scale_v", "f"),
    ("offset_v", "f"),
    ("samples_h", "512i"),
    ("samples_v", "512i"),
    ("unused", "1001")
)

iwrf_calibration = (
    ("wavelength_cm", "f"),
    ("beamwidth_deg_h", "f"),
    ("beamwidth_dev_v", "f"),
    ("gain_ant_db_h", "f"),
    ("gain_ant_db_v", "f"),
    ("pulse_width_us", "f"),
    ("xmit_power_dbm_h", "f"),
    ("xmit_power_dbm_v", "f"),
    ("two_way_waveguide_loss_db_h", "f"),
    ("two_way_waveguide_loss_db_v", "f"),
    ("two_way_radome_loss_db_h", "f"),
    ("two_way_radome_loss_db_v", "f"),
    ("receiver_mismatch_loss_db", "f"),
    ("radar_constant_h", "f"),
    ("radar_constant_v", "f"),
    ("noise_dbm_hc", "f"),
    ("noise_dbm_hx", "f"),
    ("noise_dbm_vc", "f"),
    ("noise_dbm_vx", "f"),
    ("receiver_gain_db_hc", "f"),
    ("receiver_gain_db_hx", "f"),
    ("receiver_gain_db_vc", "f"),
    ("receiver_gain_db_vx", "f"),
    ("base_dbz_1km_hc", "f"),
    ("base_dbz_1km_hx", "f"),
    ("base_dbz_1km_vc", "f"),
    ("base_dbz_1km_vx", "f"),
    ("sun_power_dbm_hc", "f"),
    ("sun_power_dbm_hx", "f"),
    ("sun_power_dbm_vc", "f"),
    ("sun_power_dbm_vx", "f"),
    ("noise_source_power_dbm_h", "f"),
    ("noise_source_power_dbm_v", "f"),
    ("power_meas_loss_db_h", "f"),
    ("power_meas_loss_db_v", "f"),
    ("coupler_forward_loss_db_h", "f"),
    ("coupler_forward_loss_db_v", "f"),
    ("test_power_dbm_h", "f"),
    ("test_power_dbm_v", "f"),
    ("zdr_correction_db", "f"),
    ("ldr_correction_db_h", "f"),
    ("ldr_correction_db_v", "f"),
    ("phidp_rot_deg", "f"),
    ("receiver_slope_hc", "f"),
    ("receiver_slope_hx", "f"),
    ("receiver_slope_vc", "f"),
    ("receiver_slope_vx", "f"),
    ("unused", "67i")
)

irwf_pulse_header = (
    ("pulse_seq_num", "q"),

    ("scan_mode", "i"),
    ("follow_mode", "i"),
    ("volume_num", "i"),
    ("sweep_num", "i"),

    ("fixed_el", "f"),
    ("fixed_az", "f"),
    ("elevation", "f"),
    ("azimuth", "f"),

    ("prt", "f"),
    ("prt_next", "f"),

    ("pulse_width_us", "f"),

    ("n_gates", "i"),

    ("n_channels", "i"),
    ("iq_encoding", "i"),
    ("hv_flag", "i"),

    ("antenna_transition", "i"),
    ("phase_cohered", "i"),
    ("status", "i"),
    ("n_data", "i"),
    ("iq_offset_1", "i"),
    ("iq_offset_2", "i"),
    ("iq_offset_3", "i"),
    ("iq_offset_4", "i"),
    ("burst_mag_1", "f"),
    ("burst_mag_2", "f"),
    ("burst_mag_3", "f"),
    ("burst_mag_4", "f"),
    ("burst_arg_1", "f"),
    ("burst_arg_2", "f"),
    ("burst_arg_3", "f"),
    ("burst_arg_4", "f"),
    ("burst_arg_diff_1", "f"),
    ("burst_arg_diff_2", "f"),
    ("burst_arg_diff_3", "f"),
    ("burst_arg_diff_4", "f"),
    ("scale", "f"),
    ("offset", "f"),
    ("n_gates_burst", "i"),
    ("start_range_m", "f"),
    ("gate_spacing_m", "f"),
    ("event_flags", "i"),
    ("txrx_state", "i"),
    ("unused", "24s")
)


packet_type = {
    0x77770001: iwrf_sync,
    0x77770002: iwrf_radar_info,
    0x77770003: iwrf_scan_segment,
    0x77770004: iwrf_antenna_correction,
    0x77770005: iwrf_ts_processing,
    0x77770006: iwrf_xmit_power,
    0x77770007: iwrf_xmit_sample,
    0x77770008: iwrf_calibration,
    0x7777000c: irwf_pulse_header
}

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Usage: read_iwrf filename_in filename_out")
    else:
        data_file = IWRFFile(sys.argv[1])
        data_file.read_file()

    if len(sys.argv) == 2:
        data_file.write_to_nc(sys.argv[1] + '.nc')
    elif len(sys.argv) == 3:
        data_file.write_to_nc(sys.argv[2])
