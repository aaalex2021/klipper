# Support for SSD1963 TFT display controllers
#
# Copyright (C) 2021  Kevin O'Connor <kevin@koconnor.net>
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import time
import logging
from . import textframebuffer
from . import i8080overFSMC

# The SSD1963 is a display controller with a 1215K byte frame buffer and
# supports up to 864 x 480 x 24bit graphics content. It also equips a parallel
# MCU interface in different bus width to receive graphics data and command
# from the MCU.

class SSD1963(textframebuffer.TextFrameBuffer):
    def __init__(self, config):
        self.width = config.getint('lcd_width', 480, minval=0, maxval=864)
        self.height = config.getint('lcd_height', 272, minval=0, maxval=480)
        self.columns = config.getint('columns', 20, minval=16)
        self.rows = config.getint('rows', 4, minval=4)
        self.fgcolor = 0xFFFF
        self.bgcolor = 0x0000
        self.io = i8080overFSMC.I8080overFSMC(config)
        textframebuffer.TextFrameBuffer.__init__(self, self.io,
                                                 self.columns, self.rows,
                                                 self.width, self.height,
                                                 self.fgcolor, self.bgcolor)
    def init(self):
        #REG(0xE2);   // Set PLL
        #i8080_send_cmd_param8 oid=1 cmd=226 param=170454
        self.io.send_cmd(0xE2,[0x17,0x04,0x54])
        #REG(0xE0);   // Start PLL command
        #i8080_send_cmd_param8 oid=1 cmd=224 param=01
        self.io.send_cmd(0xE0,[0x01])
        time.sleep(0.01)
        #REG(0xE0);   // Start PLL command again
        #i8080_send_cmd_param8 oid=1 cmd=224 param=03
        self.io.send_cmd(0xE0,[0x03])
        time.sleep(0.01)
        #REG(0x01);   // Soft reset
        #i8080_send_cmd oid=1 cmd=1
        self.io.send_cmd(0x01)
        time.sleep(0.1)
        # hard coded TFT50 settings
        #REG(0xE6);   // 12Mhz
        #i8080_send_cmd_param8 oid=1 cmd=230 param=013332
        self.io.send_cmd(0xE6,[0x01, 0x33, 0x32])
        # hard coded TFT50 parameters 480x272 resolution
        #REG(0xB0);   // Set LCD mode
        #i8080_send_cmd_param8 oid=1 cmd=176 param=000001DF010F00
        self.io.send_cmd(0xB0,[0,0,1,0xDF,1,0x0F,0])
        #REG(0xB4);   // Set horizontal period
        #i8080_send_cmd_param8 oid=1 cmd=180 param=020A002900000000
        self.io.send_cmd(0xB4,[2,0x0A,0,0x29,0,0,0,0])
        #REG(0xB6);   // Set vertical period
        #i8080_send_cmd_param8 oid=1 cmd=182 param=011B000A010000
        self.io.send_cmd(0xB6,[1,0x1B,0,0x0A,1,0,0])
        #REG(0xF0);   // Set pixel data interface format
        #i8080_send_cmd_param8 oid=1 cmd=240 param=03
        self.io.send_cmd(0xF0,[3])
        #REG(0xBC);   // postprocessor for contrast/brightness/saturation.
        #i8080_send_cmd_param8 oid=1 cmd=188 param=40804001
        self.io.send_cmd(0xBC,[0x40,0x80,0x40,1])
        #REG(0x29);   // Set display on
        #i8080_send_cmd oid=1 cmd=41
        self.io.send_cmd(0x29)
        #REG(0x36);   // Set address mode
        #i8080_send_cmd_param8 oid=1 cmd=54 param=00
        self.io.send_cmd(0x36,[0])
        self.clear_all()


    def clear_all(self):
        ex= self.width - 1
        self.send_cmd(0x2A,[0,0,ex>>8,ex&0xFF])
        ey= self.height - 1
        self.send_cmd(0x2B,[0,0,ey>>8,ey&0xFF])
        self.send_cmd(0x2C)
        self.send_fill(0x0000, self.width * self.height)

    def _fill_into_region(self, x_from, x_to, y_from, y_to, words):
        self.send_cmd(0x2A,[x_from>>8, x_from&0xFF, x_to>>8, x_to&0xFF])
        self.send_cmd(0x2B,[y_from>>8, y_from&0xFF, y_to>>8, y_to&0xFF])
        self.send_cmd(0x2C)
        for d in words: self.send_data(d)
