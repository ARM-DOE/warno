import struct
import os
import socket
import time
from select import select
import ConfigParser
import StringIO
import numpy as np
from math import log10
import datetime


class PAFClient(object):

    """Class representing a ProSensing Application Framework Configuration Connection

    """

    def __init__(self, hostname=None, port=3000, fmt='KAZR2'):
        """ Initializer for the PAFClient class.

        The PAFClient class manages communications with a ProSensing Application
        Framework enabled radar.

        Parameters
        ----------
        hostname: string
            An IP address or fully qualified domain name of a computer running a PAF Server.
        port: optional, integer
            Port to connect to. Defaults to 3000.
        fmt: optional, string
            Radar Format to select. ProSensing uses several different formats and this controls
            which one to use. Primary choices are KAZR2, KAZR1, or SACR2. Defaults to KAZR2

        Returns
        -------
        client: 'PAFClient' instance.
            Returns a application framework instance object to communicate with the server.

        """

        self.hostname = hostname
        self.port = port
        self.product_table = {}
        self.fmt = fmt

    def connect(self, hostname=None, port=3000):
        """ Connect to PAF server

        Connect to a PAF server at hostname and port.

        Parameters
        ----------
         hostname: string
            An IP address or fully qualified domain name of a computer running a PAF Server.
        port: optional, integer
            Port to connect to. Defaults to 3000.
        """

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if hostname is None and self.hostname is None:
            print("No hostname set, please set a hostname and try again")
            return

        try:
            if hostname is None:
                self.s.connect((self.hostname, self.port))
                self.s.setblocking(0)
            else:
                self.s.connect((hostname, port))
        except Exception, e:
            print("Exception Encountered in Client Connect: %s" % e)

    def close(self):
        """ Disconnect from PAF server.
        """

        self.s.close()
        self.s = None

    def reconnect(self):
        """ Reconnect to a PAF Server.

        Closes the connection and then re-opens and reconnects to the PAF Server
        """

        self.close()
        self.connect()

    def ping_server(self):
        """server ping command, checks for good connection. Currently only works for version one formats.

        Returns
        -------
        success: boolean
            Success of Ping Operation
        """

        self.s.send(server_request_type['ping'])
        self.msg_buffer = self.recvall(self.s)
        print(self.msg_buffer)
        if struct.unpack("<i", self.msg_buffer)[0] is 66:
            return True
        else:
            return False

    def get_all_text_dict(self):
        """ Query all text types and return as a single dictionary. This also tries to
        convert values into numerics instead of strings
        """

        all_dict = dict()
        all_dict.update(self.get_text_configuration())
        all_dict.update(self.get_text_status())
        all_dict.update(self.get_text_calibration())
        all_dict.update(self.get_text_device_status())
        all_dict.update(self.get_text_mod_status())
        all_dict.update(self.get_text_proc_header())

        for key in all_dict:
            all_dict[key] = self._safe_convert_value(all_dict[key])

        return all_dict

    def get_text_configuration(self):
        """ Request and parse the text configuration status. Currently this is the
        only way to get data out of the system.
        """
        if self.hostname in fw2_hosts:
            self.s.send(struct.pack(
                "<ib", server_request_type_fw2['CmdGetConfigText'], 0))
        else:
            self.s.send(struct.pack(
                "<i", server_request_type_fw2['CmdGetConfigText']))
        return self._parse_text_header()

    def get_text_status(self):
        """ Request and parse the text status packet. Currently this is the
        only way to get data out of the system.
        """

        if self.hostname in fw2_hosts:
            self.s.send(struct.pack(
                "<ib", server_request_type_fw2['CmdGetStatusText'], 0))
        else:
            self.s.send(struct.pack(
                "<i", server_request_type_fw2['CmdGetStatusText']))
        return self._parse_text_header()

    def get_text_calibration(self):
        """ Request and parse the text calibration packet. Currently this is the
        only way to get data out of the system.
        """

        if self.hostname in fw2_hosts:
            self.s.send(struct.pack(
                "<ib", server_request_type_fw2['CmdGetCalibrationText'], 0))
        else:
            self.s.send(struct.pack(
                "<i", server_request_type_fw2['CmdGetCalibrationText']))
        return self._parse_text_header()

    def get_text_device_status(self):
        """ Request and parse the text configuration status. Currently this is the
        only way to get data out of the system.
        """

        if self.hostname in fw2_hosts:
            self.s.send(struct.pack(
                "<ib", server_request_type_fw2['CmdGetDeviceStatusText'], 0))
        else:
            self.s.send(struct.pack(
                "<i", server_request_type_fw2['CmdGetDeviceStatusText']))
        return self._parse_text_header()

    def get_text_mod_status(self):
        """ Request and parse the text configuration status. Currently this is the
        only way to get data out of the system.
        """

        if self.hostname in fw2_hosts:
            self.s.send(struct.pack(
                "<ib", server_request_type_fw2['CmdGetModStatusText'], 0))
        else:
            self.s.send(struct.pack(
                "<i", server_request_type_fw2['CmdGetModStatusText']))
        return self._parse_text_header()

    def get_text_proc_header(self):
        """ Request and parse the text configuration status. Currently this is the
        only way to get data out of the system.
        """

        if self.hostname in fw2_hosts:
            self.s.send(struct.pack(
                "<ib", server_request_type_fw2['CmdGetProcHeaderText'], 0))
        else:
            self.s.send(struct.pack(
                "<i", server_request_type_fw2['CmdGetProcHeaderText']))
        return self._parse_text_header()

    def _parse_text_header(self):
        """Parse the results of a Cmd*Text request and return a dict of key value pairs
        """
        msgbuffer = self.recvall(self.s)
        config = ConfigParser.ConfigParser()
        config.readfp(StringIO.StringIO('[root]\n' + msgbuffer[4:]))
        return dict(config.items('root'))

    def get_configuration(self, config_only=False):
        if config_only:
            self.s.send(server_request_type['get_configuration'])
        else:
            self.s.send(server_request_type['get_configuration_and_status'])

        msgbuffer = self.recvall(self.s)
        self.msg_buffer = msgbuffer

        response, total_size, archive_idx, config_size, status_size =\
            struct.unpack("<5i", msgbuffer[0:20])
        offset = 20

        self.config_buffer = msgbuffer[20:config_size]
        offset += config_size

        self.status_buffer = msgbuffer[offset:offset + status_size]
        offset += status_size

        final_code = struct.unpack("<i", msgbuffer[-4:])

        if final_code == 72:
            print("No more data")
            return None
        elif final_code != 66:
            print("There may have been an error")

        return None

    def get_status(self):
        """ Request current server status.
        """

        self.s.send(server_request_type['get_status'])
        msgbuffer = self.recvall(self.s)
        self.msg_buffer = msgbuffer

        response_code, total_size, status_size = struct.unpack(
            "<3i", msgbuffer[0:12])
        offset = 12

        status_buffer = msgbuffer[offset: offset + status_size]
        offset += status_size

        final_code = struct.unpack("<i", msgbuffer[-4:])

        if final_code != 66:
            print("There may have been an error")

        return None

    def get_server_info(self):
        """ Get Server info from PAF
        """
        self.s.send(server_request_type['server_info'])
        time.sleep(0.001)  # Make sure server has time to respond

        msgbuffer = self.recvall(self.s)
        self.msgbuffer = msgbuffer
        response_code, struct_size = struct.unpack("<2i", msgbuffer[0:8])

        server_info_struct = self._parse_server_info_struct(msgbuffer[8:])

        final_code = struct.unpack("<i", msgbuffer[-4:])[0]
        if final_code is not server_status_codes['NETRES_OK']:
            print("Possible error in Server Info\n")
            print(msgbuffer[-4:])
        self.server_info_struct = server_info_struct

        return server_info_struct

    def get_data(self, product_code=1, num_blocks=1):
        ''' get_data Retrieves a given number of data blocks of a product type from the server_status_codes
        '''
        self._clear_socket(self.s)

        self.s.send(server_request_type['get_data'])

        # Size of Client Data Request Packet
        self.s.send(struct.pack("<i", 60))
        cdr = self._create_client_data_request_structure(product_code, num_blocks)
        self.s.send(cdr)

        time.sleep(0.1)

        msgbuffer = self.recvall(self.s)
        if(msgbuffer is ''):
            time.sleep(2)
            msgbuffer = self.recvall(self.s)

        self.msgbuffer = msgbuffer

        response_code, struct_size = struct.unpack("<2i", msgbuffer[0:8])
        data_response = self._parse_server_data_response_structure(
            msgbuffer[8:-4], product_code)
        self.data = data_response

        if struct.unpack("<i", msgbuffer[-4:])[0] != 66:
            print("There may have been an error")

        return data_response

    def _parse_server_data_response_structure(self, msgbuffer, type_code):
        '''Parse a returned Data Response Structure'''

        # Start with initial header

        product_type, time_stamp_s, time_stamp_ns = struct.unpack(
            "<3i", msgbuffer[0:12])
        offset = 12

        pedstatus = PedVector
        if self.fmt == 'KAZR1':
            rxconfig = DigRcvConfig_kazr1
        elif self.fmt == 'SACR1':
            rxconfig = DigRcvConfig
        else:
            rxconfig = DigRcvConfig

        digital_receiver_configuration = self._unpack_structure(
            msgbuffer, rxconfig, offset)
        offset += self._struct_size(rxconfig)

        server_data_response_header = self._unpack_structure(
            msgbuffer, ServerDataResponse, offset)
        offset += self._struct_size(ServerDataResponse)

        pedestal_status = self._unpack_structure(msgbuffer, pedstatus, offset)
        offset += self._struct_size(pedstatus)

        gps_status = self._unpack_structure(msgbuffer, GeoVector, offset)
        offset += self._struct_size(GeoVector)

        d1 = server_data_response_header['block_dimension_sizes_d1'] / 8
        d2 = server_data_response_header['block_dimension_sizes_d2']
        d3 = server_data_response_header['block_dimension_sizes_d3']
        d4 = server_data_response_header['block_dimension_sizes_d4']

        if(d2 == 0):
            d2 = 1
        if(d3 == 0):
            d3 = 1
        if(d4 == 0):
            d4 = 1

        sz_data = d1 * d2 * d3 * d4

        data_int_vec = []
        for x in range(server_data_response_header["num_blocks"]):
            start_offset = offset + (x) * server_data_response_header['block_size']
            end_offset = offset + (x + 1) * server_data_response_header['block_size']
            data_int_vec.append(np.array(
                struct.unpack("<%dd" % sz_data, msgbuffer[start_offset:end_offset])))

        if self.product_table[type_code]['number_interleaved_tracks'] == 2:
            for x in range(server_data_response_header["num_blocks"]):
                data_int_vec[x] = data_int_vec[x][::2] + 1j * data_int_vec[x][1::2]
            d1 = d1 / 2

        data_contents = []
        for di in data_int_vec:
            data_contents.append(di.reshape(d4, d3, d2, d1).squeeze())

        if self.product_table[type_code]['data_unit_type'] == 2:
            data_contents = [self._convert_count_to_dBm(np.sqrt(dc)).tolist() for dc in data_contents]
        elif self.product_table[type_code]['data_unit_type'] == 1:
            print("Before Conversion row 20 %s" % data_contents[0][20])
            data_contents = [self._convert_count_to_dBm(dc).tolist() for dc in data_contents]
            print("After Conversion row 20 %s" % data_contents[0][20])

        return {"digital_receiver_config": digital_receiver_configuration,
                "server_data_response_header": server_data_response_header,
                "pedestal_status": pedestal_status,
                "gps_status": gps_status,
                "data_contents": data_contents}

    def _create_client_data_request_structure(self, product_code, num_blocks=1):
        """ Internal method to setup client data request structure for transmission
        """
        cdr_tuple = (product_code, -1, 1, 1, num_blocks, 0, 0,
                     0, 0, -1, -1, -1, -1, -1, 0x02)
        cdr = struct.pack("<15i", *cdr_tuple)
        return cdr

    def _parse_server_info_struct(self, msgbuffer):
        """ Given a server info structure in a buffer, parse into structures
        """
        offset = 0
        name = struct.unpack('<128s', msgbuffer[:128])[0]
        offset += 128

        receiver_info = self._unpack_structure(msgbuffer, DigRcvInfo, offset)
        offset += self._struct_size(DigRcvInfo)

        receiver_spec = self._unpack_structure(msgbuffer, DigRcvSpec, offset)
        offset += self._struct_size(DigRcvSpec)

        product_count = struct.unpack('<i', msgbuffer[offset:offset + 4])[0]
        offset += 4

        if ((len(msgbuffer) - offset - 4) / 128) == product_count:
            dpi_struct = DataProductInfo_old_compat  # Old version for KAZR1
            self.fmt = 'KAZR1'
        elif ((len(msgbuffer) - offset - 4) / 320) == product_count:
            dpi_struct = DataProductInfo

        products = []
        for i in range(0, product_count):
            products.append(self._unpack_structure(
                msgbuffer, dpi_struct, offset))
            self.product_table[products[i]['type_code']] = products[i]
            offset += self._struct_size(dpi_struct)

        self._build_product_table(products)

        return {"name": name, "receiver_info": receiver_info, "receiver_spec": receiver_spec,
                "product_count": product_count, "products": products}

    def _build_product_table(self, products):
        self.sn_lut = dict(
            [(i['name_short'].rstrip('\x00'), i['type_code']) for i in products])
        self.ln_lut = dict(
            [(i['name_long'].rstrip('\x00'), i['type_code']) for i in products])
        self.sn_id_lut = dict(map(reversed, self.sn_lut.items()))
        self.ln_id_lut = dict(map(reversed, self.ln_lut.items()))

    def _unpack_structure(self, string, structure, offset=0):
        """ Unpack a structure """
        fmt = '<' + ''.join([i[1] for i in structure])
        tpl = struct.unpack(fmt, string[offset:offset + struct.calcsize(fmt)])
        return dict(zip([i[0] for i in structure], tpl))

    def _struct_size(self, structure):
        """ Unpack a structure """
        fmt = '<' + ''.join([i[1] for i in structure])
        return struct.calcsize(fmt)

    def recvall(self, sock):
        self.buffer = ""
        while sock in select([sock, ], [], [], 1)[0]:
            self.buffer += sock.recv(1000)
            if self.buffer is '':
                return self.buffer
        return self.buffer

    def _clear_socket(self, sock):
        self.buffer = ""
        while sock in select([sock, ], [], [], 0.1)[0]:
            self.buffer += sock.recv(1000)
            if self.buffer is '':
                return self.buffer
        return self.buffer

    def _safe_convert_value(self, value):
        try:
            val = float(value)
            return val
        except ValueError:
            return value
        return value  # This should be unreachable

    def _convert_mW_to_dBm(self, mW):
        """Convert power from mW to dBm"""
        return 10.*np.log10(mW)

    def _convert_count_to_dBm(self, counts):
        """Takes a NumPy array of counts and converts them to dBm in place"""
        max_dbm = 8.
        scale_factor = np.sqrt(np.power(10., (max_dbm / 10.)) / 10.) / 32767.
        dbm = 30. + 10.*np.log10(np.power(np.absolute(counts * scale_factor), 2.) / 50.)
        dbm[np.isinf(dbm)] = 30. + 10.*np.log10(np.power(np.absolute(1 * scale_factor), 2.) / 50.)
        return dbm


PedVector = (
    ("position_azimuth", "d"),
    ("position_elevation", "d"),
    ("velocity_azimuth", "d"),
    ("velocity_elevation", "d"),
    ("motor_current_azimuth", "d"),
    ("motor_current_elevation", "d"))

GeoVector = (
    ("hemisphere_lat", "i"),
    ("position_lat", "d"),
    ("hemisphere_lon", "i"),
    ("position_lon", "d"),
    ("altitude", "d"),
    ("heading_reference", "i"),
    ("heading", "d"),
    ("speed", "d"))


DataProductInfo = (
    ("type_code", "i"),
    ("name_short", "32s"),
    ("name_long", "256s"),
    ("digital_receiver_channel", "i"),
    ("positioner_device_index", "i"),
    ("gps_device_index", "i"),
    ("data_domain_type", "i"),
    ("data_unit_type", "i"),
    ("number_interleaved_tracks", "i"),
    ("number_matrix_dimensions", "i"))

DataProductInfo_old_compat = (
    ("type_code", "i"),
    ("name_short", "32s"),
    ("name_long", "64s"),
    ("digital_receiver_channel", "i"),
    ("positioner_device_index", "i"),
    ("gps_device_index", "i"),
    ("data_domain_type", "i"),
    ("data_unit_type", "i"),
    ("number_interleaved_tracks", "i"),
    ("number_matrix_dimensions", "i"))


DigRcvSpec = (
    ("number_input_channels", "i"),
    ("min_sample_clock", "i"),
    ("max_sample_clock", "i"),
    ("min_center_freq", "i"),
    ("max_center_freq", "i"),
    ("min_number_DMA_descriptors", "i"),
    ("max_number_DMA_descriptors", "i"),
    ("min_number_DMA_descriptor_packets", "i"),
    ("max_number_DMA_descriptor_packets", "i"),
    ("min_DMA_packet_size", "i"),
    ("max_DMA_packet_size", "i"),
    ("DMA_packet_size_granularity", "i"),
    ("min_burst_size", "i"),
    ("max_burst_size", "i"),
    ("burst_size_granularity", "i"),
    ("min_number_bursts_per_PCI_interrupt", "d"),
    ("max_number_bursts_per_PCI_interrupt", "d"),
    ("min_skip_count", "i"),
    ("max_skip_count", "i"),
    ("min_CIC_decimation_level", "i"),
    ("max_CIC_decimation_level", "i"),
    ("min_FIR_decimation_level", "i"),
    ("max_FIR_decimation_level", "i"),
    ("min_post_decimation_level", "i"),
    ("max_post_decimation_level", "i"),
    ("max_FIR_filter_length", "i"),
    ("min_FIR_gain", "d"),
    ("max_FIR_gain", "d"),
    ("full_scale_FIR_gain_level", "d"),
    ("min_analog_voltage_input", "d"),
    ("max_analog_voltage_input", "d"),
    ("analog_impedance", "d"),
    ("min_digitized_count_value", "i"),
    ("max_digitized_count_value", "i"),
    ("ad_resolution", "i"),
    ("digitized_count_size", "i"))


ClientDataRequest = (
    ("product_type_code", "i"),
    ("block_offset", "i"),
    ("block_step_length", "i"),
    ("block_seen_step_length", "i"),
    ("max_number_blocks", "i"),
    ("matrix_subset_selection_extent_1", "4i"),
    ("matrix_subset_selection_extent_2", "4i"),
    ("expected_archive_index", "i"),
    ("format_flags", "i"))

DigRcvConfig = (
    ("mode", "i"),
    ("trigger_source", "i"),
    ("PCI_bus_freq", "i"),
    ("ad_sample_clock_frequency", "i"),


    ("data_trigger_PRI", "q"),

    ("number_DMA_descriptors", "i"),
    ("number_DMA_packets_per_descriptor", "i"),
    ("DMA_packet_size", "i"),
    ("block_size", "i"),
    ("reserved", "i"),

    ("number_blocks_per_PCI_interrupt", "d"),

    ("reserved", "i"),
    ("reserved", "i"),
    ("state_ch1", "i"),
    ("state_ch2", "i"),
    ("data_source_ch1", "i"),
    ("data_source_ch2", "i"),
    ("skip_count_ch1", "i"),
    ("skip_count_ch2", "i"),
    ("CIC_decimation_ch1", "i"),
    ("CIC_decimation_ch2", "i"),
    ("FIR_decimation_ch1", "i"),
    ("FIR_decimation_ch2", "i"),
    ("post_decimation_ch1", "i"),
    ("post_decimation_ch2", "i"),
    ("NCO_frequency_ch1", "i"),
    ("NCO_frequency_ch2", "i"))


DigRcvConfig_kazr1 = (
    ("mode", "i"),
    ("trigger_source", "i"),
    ("PCI_bus_freq", "i"),
    ("ad_sample_clock_frequency", "i"),

    ("number_DMA_descriptors", "i"),
    ("number_DMA_packets_per_descriptor", "i"),
    ("DMA_packet_size", "i"),
    ("block_size", "i"),
    ("reserved", "i"),

    ("number_blocks_per_PCI_interrupt", "d"),

    ("reserved", "i"),
    ("reserved", "i"),
    ("state_ch1", "i"),
    ("state_ch2", "i"),
    ("data_source_ch1", "i"),
    ("data_source_ch2", "i"),
    ("skip_count_ch1", "i"),
    ("skip_count_ch2", "i"),
    ("CIC_decimation_ch1", "i"),
    ("CIC_decimation_ch2", "i"),
    ("FIR_decimation_ch1", "i"),
    ("FIR_decimation_ch2", "i"),
    ("post_decimation_ch1", "i"),
    ("post_decimation_ch2", "i"),
    ("NCO_frequency_ch1", "i"),
    ("NCO_frequency_ch2", "i"))


DigRcvInfo = (
    ("manufacturer_code", "i"),
    ("manufacturerer_name", "32s"),
    ("model_code", "i"),
    ("model_name", "32s"))  # Followed by DigRcvSpec Structure


ServerDataResponse = (
    ("digital_receiver_FIR_filter_gain", 'd'),
    ("averaging_interval_length", "i"),
    ("archive_index", "i"),
    ("block_index", "q"),
    ("num_blocks", "i"),
    ("block_size", "i"),
    ("num_block_dimensions", "i"),
    ("block_dimension_sizes_d1", "i"),  # Followed by more structures
    ("block_dimension_sizes_d2", "i"),
    ("block_dimension_sizes_d3", "i"),
    ("block_dimension_sizes_d4", "i")
)
server_status_codes = {
    "NETRES_SRV_ERR": 65,
    "NETRES_OK": 66,
    "NETRES_CFG_TRANSITION": 67,
    "NETRES_LACK_CONTROL": 68,
    "NETRES_UNKNOWN_CMD": 69,
    "NETRES_UNKNOWN_DATA_TYPE": 70,
    "NETRES_WRONG_DATA_SIZE": 71,
    "NETRES_NO_DATA": 72,
    "NETRES_WRONG_ARCHIVE": 73,
    "NETRES_INVALID_INDEX": 74,
    "NETRES_INVALID_PARAM": 75,
    "NETRES_INVALID_TEXT": 76,
    "NETRES_NETCMD_BUSY": 77,
}


server_status_numbers = dict((v, k)
                             for k, v in server_status_codes.iteritems())

server_request_type = {
    "ping": "\x01\x00\x00\x00",
    "server_info": "\x05\x00\x00\x00",
    "get_data": "\x07\x00\x00\x00",
    "get_configuration": "\x02\x00\x00\x00",
    "get_configuration_and_status": "\x08\x00\x00\x00",
    "get_status": "\x04\x00\x00\x00"
}

server_request_type_fw2 = {
    "CmdPing": 2001,
    "CmdGetConfig": 2002,
    "CmdSetConfig": 2003,
    "CmdGetStatus": 2004,
    "CmdGetServerInfo": 2005,
    "CmdGetData": 2006,
    "CmdAcquireControl": 2007,
    "CmdRelinquishControl": 2008,
    "CmdPacsi": 2009,
    "CmdGetStatusText": 2010,
    "CmdGetConfigText": 2011,
    "CmdGetDeviceStatusText": 2012,
    "CmdGetCalibrationText": 2013,
    "CmdGetModStatusText": 2014,
    "CmdGetProcHeaderText": 2015,
    # I'm quite aware of how ugly this is. Fix Later
    "CmdKazr2GetProcHeader": 3000
}

fw2_hosts = [
    "ena-sacr",
    "sgp-sacr"
]


if __name__ == "__main__":
    client = Client("ena-kazr", 3000)
    client.connect()

    sis = client.get_server_info()
    print("Received %d products" % len(sis['products']))
