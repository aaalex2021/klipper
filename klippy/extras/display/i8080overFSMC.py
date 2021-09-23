# Support for using the Intel 8080 protocol via an STM32 FSMC
#
# Copyright (C) 2018-2019  Kevin O'Connor <kevin@koconnor.net>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
#import pdb

import logging
import mcu

class I8080overFSMC:
    def __init__(self, config):
        logging.info("I8080overFSMC __init__")

        # Determine FSMC control pins from config
        printer = config.get_printer()
        self.mcu = mcu.get_printer_mcu(printer, config.get('fsmc_mcu', 'mcu'))
        ppins = printer.lookup_object("pins")
        cs_pin_param = ppins.lookup_pin(config.get('fsmc_cs_pin'),
                                        share_type=None)
        self.cs_pin = cs_pin_param['pin']
        rs_pin_param = ppins.lookup_pin(config.get('fsmc_rs_pin'),
                                        share_type=None)
        self.rs_pin = rs_pin_param['pin']
        if cs_pin_param['chip'] != self.mcu or rs_pin_param['chip'] != self.mcu:
            raise ppins.error("%s: fsmc pins must be on same mcu" %
                              (config.get_name(),))
        self.oid = self.mcu.create_oid()
        self.config_fmt = ("config_i8080 oid=%d" % self.oid)
        self.cmd_queue = self.mcu.alloc_command_queue()
        self.mcu.register_config_callback(self.build_config)
    def get_oid(self):
        return self.oid
    def get_mcu(self):
        return self.mcu
    def get_command_queue(self):
        return self.cmd_queue
    def build_config(self):
        logging.debug("I8080overFSMC build_config")
        self.mcu.add_config_cmd(self.config_fmt)
        self.i8080_send_cmd_cmd = self.mcu.lookup_command(
            "i8080_send_cmd oid=%c cmd=%c", cq=self.cmd_queue)
        self.i8080_send_cmd_param8_cmd = self.mcu.lookup_command(
            "i8080_send_cmd_param8 oid=%c cmd=%c param=%*s", cq=self.cmd_queue)
        self.i8080_send_data16_cmd = self.mcu.lookup_command(
             "i8080_send_data16 oid=%c data=%*s", cq=self.cmd_queue)
        self.i8080_send_fill_cmd = self.mcu.lookup_command(
             "i8080_send_fill oid=%c color=%c count=%c", cq=self.cmd_queue)

    def send_data(self, data):
        self.i8080_send_data16_cmd.send([self.oid, data])

    def send_cmd(self, cmd, param=[]):
        if not param:
            self.i8080_send_cmd_cmd.send([self.oid, cmd])
        else:
            self.i8080_send_cmd_param8_cmd.send([self.oid, cmd,
                                                 bytearray(param)])

    def send_fill(self, color, count):
        self.i8080_send_fill_cmd.send([self.oid, color, count])
