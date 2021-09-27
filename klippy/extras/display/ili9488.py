# Support for ILI9488 TFT display controllers
#
# Copyright (C) 2021  Kevin O'Connor <kevin@koconnor.net>
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import time
from . import textframebuffer
from . import i8080overFSMC

# The ILI9488 is a 16.7M single-chip SoC driver for a-Si TFT liquid crystal
# display panels with a resolution of 320(RGB) x 480 dots. The ILI9488 is
# comprised of a 960-channel source driver, a 480-channel gate driver, 345,600
# bytes GRAM for graphic data of 320 (RGB) x 480 dots, and power supply circuit.

class ILI9488(textframebuffer.TextFrameBuffer):
    def __init__(self, config):
        self.width = config.getint('lcd_width', 480, minval=0, maxval=864)
        self.height = config.getint('lcd_height', 320, minval=0, maxval=480)
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
        #REG(0xC0)
        self.io.send_cmd(0xC0,[0x0c,0x02,])
        #REG(0xC1);
        self.io.send_cmd(0xC1,[0x44])
        #REG(0xC5);
        self.io.send_cmd(0xC5,[0x00,0x16,0x80])
        #REG(0x36);
        self.io.send_cmd(0x36,[0x28])
        #REG(0x3A);
        self.io.send_cmd(0x3A,[0x55])
        #REG(0xB0);
        self.io.send_cmd(0xB0,[0])
        #REG(0xB1);
        self.io.send_cmd(0xB1,[0xB0])
        #REG(0xB4);
        self.io.send_cmd(0xB4,[2])
        #REG(0xB6);
        self.io.send_cmd(0xB6,[2,2])
        #REG(0xE9);
        self.io.send_cmd(0xE9,[0])
        #REG(0xF7);
        self.io.send_cmd(0xF7,[0xA9,0x51,0x2c,0x82])
        #REG(0x11);
        self.io.send_cmd(0x11)
        time.sleep(0.12)
        #REG(0x29);
        self.io.send_cmd(0x29)
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
