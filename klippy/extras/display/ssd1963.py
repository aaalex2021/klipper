# Support for SSD1963 TFT display controllers
#
# Copyright (C) 2018-2019  Kevin O'Connor <kevin@koconnor.net>
# Copyright (C) 2018  Eric Callahan  <arksine.code@gmail.com>
# Copyright (C) 2021  Alex Peuchert <aaalex2021@ki2s.com>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
#import pdb

import time
import logging
import mcu
#from .. import bus
#from . import font8x14
from . import font16x24

CHAR_HEIGHT = 24
CHAR_WIDTH = 16

class DisplayBase:
    def __init__(self, io, columns=128, rows=64, x_offset=0):
        self.send = io.send
        # framebuffers
        self.columns = columns
        self.rows = rows
        self.x_offset = x_offset
        self.vram = [bytearray(self.columns) for i in range(8)]
        self.all_framebuffers = [(self.vram[i], bytearray('~'*self.columns), i)
                                 for i in range(8)]
        # Cache fonts and icons in display byte order
        self.font = [self._swizzle_bits(bytearray(c))
                     for c in font8x14.VGA_FONT]
        self.icons = {}
    def flush(self):
        # Find all differences in the framebuffers and send them to the chip
        for new_data, old_data, page in self.all_framebuffers:
            if new_data == old_data:
                continue
            # Find the position of all changed bytes in this framebuffer
            diffs = [[i, 1] for i, (n, o) in enumerate(zip(new_data, old_data))
                     if n != o]
            # Batch together changes that are close to each other
            for i in range(len(diffs)-2, -1, -1):
                pos, count = diffs[i]
                nextpos, nextcount = diffs[i+1]
                if pos + 5 >= nextpos and nextcount < 16:
                    diffs[i][1] = nextcount + (nextpos - pos)
                    del diffs[i+1]
            # Transmit changes
            for col_pos, count in diffs:
                # Set Position registers
                ra = 0xb0 | (page & 0x0F)
                ca_msb = 0x10 | ((col_pos >> 4) & 0x0F)
                ca_lsb = col_pos & 0x0F
                self.send([ra, ca_msb, ca_lsb])
                # Send Data
                self.send(new_data[col_pos:col_pos+count], is_data=True)
            old_data[:] = new_data
    def _swizzle_bits(self, data):
        # Convert from "rows of pixels" format to "columns of pixels"
        top = bot = 0
        for row in range(8):
            spaced = (data[row] * 0x8040201008040201) & 0x8080808080808080
            top |= spaced >> (7 - row)
            spaced = (data[row + 8] * 0x8040201008040201) & 0x8080808080808080
            bot |= spaced >> (7 - row)
        bits_top = [(top >> s) & 0xff for s in range(0, 64, 8)]
        bits_bot = [(bot >> s) & 0xff for s in range(0, 64, 8)]
        return (bytearray(bits_top), bytearray(bits_bot))
    def set_glyphs(self, glyphs):
        for glyph_name, glyph_data in glyphs.items():
            icon = glyph_data.get('icon16x16')
            if icon is not None:
                top1, bot1 = self._swizzle_bits(icon[0])
                top2, bot2 = self._swizzle_bits(icon[1])
                self.icons[glyph_name] = (top1 + top2, bot1 + bot2)
    def write_text(self, x, y, data):
#        pdb.set_trace()
        logging.debug("DD.write_text x:%d y:%d data(%d):%s:", x, y, len(data), data)
        if x + len(data) > 16:
            data = data[:16 - min(x, 16)]
        pix_x = x * 8
        pix_x += self.x_offset
        page_top = self.vram[y * 2]
        page_bot = self.vram[y * 2 + 1]
        for c in bytearray(data):
            bits_top, bits_bot = self.font[c]
            page_top[pix_x:pix_x+8] = bits_top
            page_bot[pix_x:pix_x+8] = bits_bot
            pix_x += 8
    def write_graphics(self, x, y, data):
        logging.debug("DD.write_graphics x:%d y:%d data:%s:", x, y, data)
        if x >= 16 or y >= 4 or len(data) != 16:
            return
        bits_top, bits_bot = self._swizzle_bits(data)
        pix_x = x * 8
        pix_x += self.x_offset
        page_top = self.vram[y * 2]
        page_bot = self.vram[y * 2 + 1]
        for i in range(8):
            page_top[pix_x + i] ^= bits_top[i]
            page_bot[pix_x + i] ^= bits_bot[i]
    def write_glyph(self, x, y, glyph_name):
        logging.debug("DD.write_glyph x:%d y:%d data:%s:", x, y, glyph_name)
        icon = self.icons.get(glyph_name)
        if icon is not None and x < 15:
            # Draw icon in graphics mode
            pix_x = x * 8
            pix_x += self.x_offset
            page_idx = y * 2
            self.vram[page_idx][pix_x:pix_x+16] = icon[0]
            self.vram[page_idx + 1][pix_x:pix_x+16] = icon[1]
            return 2
        char = TextGlyphs.get(glyph_name)
        if char is not None:
            # Draw character
            self.write_text(x, y, char)
            return 1
        return 0
    def clear(self):
        zeros = bytearray(self.columns)
        for page in self.vram:
            page[:] = zeros
    def get_dimensions(self):
        return (self.width, self.height)


class TextFrameBuffer:
    def __init__(self, io, columns=20, rows=8):
        self.send_cmd = io.send_cmd
        self.send_data = io.send_data
        self.columns = columns
        self.rows = rows
        self.vram = [[0x00] * self.columns for i in range(self.rows)]
        # Cache fonts and icons in display byte order
        self.font = [self._swizzle_bits(bytearray(c))
                     for c in font16x24.VGA_FONT_16x24]
        self.icons = {}
    def set_glyphs(self, glyphs):
        logging.debug("TFB.set_glyphs %s", repr(glyphs))
        for glyph_name, glyph_data in glyphs.items():
            icon = glyph_data.get('icon16x16')
            if icon is not None:
                icon_words = [ 0, 0, 0, 0, 0, 0, 0, 0]
                for ba in zip(icon[0],icon[1]):
                    icon_words = icon_words + [ba[1], ba[0]]
                icon_words = icon_words + [ 0, 0, 0, 0, 0, 0, 0, 0]
                self.icons[glyph_name] = self._swizzle_bits(icon_words)
                logging.debug("TFB.set_glyphs %s: %s", glyph_name, repr(self.icons[glyph_name]))
    def _swizzle_bits(self, data):
        c = data
        c_out = []
        for i in range(len(c)/2):
            c_row = c.pop(0) | c.pop(0)<<8
            ar = []
            for b in format(c_row,'016b'):
                ar = ar + ([0,31] if b=='1' else [0,0])
            c_out.append(ar);
        return [ bytearray(row) for row in c_out ]
    def flush(self):
        logging.debug("TFB.flush")
    def _draw_char(self, x, y, bts):
        ex= x+(CHAR_WIDTH-1)
        self.send_cmd(0x2A,[x>>8,x&0xFF,ex>>8,ex&0xFF])
        ey= y+(CHAR_HEIGHT-1)
        self.send_cmd(0x2B,[y>>8,y&0xFF,ey>>8,ey&0xFF])
        self.send_cmd(0x2C)
        for d in bts:
            self.send_data(d)
    def write_text(self, x, y, data):
        if not len(data):
            return
#        import pdb; pdb.set_trace()
#        logging.debug("TFB.write_text x:%d y:%d data(%d):%s:", x, y, len(data), data)
        cx = x * CHAR_WIDTH
        cy = y * CHAR_HEIGHT
        for c in bytearray(data):
            self._draw_char(cx, cy, self.font[c])
            cx += CHAR_WIDTH
        
    def write_graphics(self, x, y, data):
#        logging.debug("TFB.write_graphics x:%d y:%d data:%s:", x, y, data)
        pass
    def write_glyph(self, x, y, glyph_name):
        logging.debug("TFB.write_glyph x:%d y:%d data:%s:", x, y, glyph_name)
        self._draw_char(x * CHAR_WIDTH, y * CHAR_HEIGHT, self.icons.get(glyph_name))
        return 1
    def clear(self):
#        logging.debug("TFB.clear")
        pass
    def get_dimensions(self):
        logging.debug("TFB.get_dimensions")
        return (self.rows, self.columns)
        
class I8080overFSMC:
    def __init__(self, config):
        logging.info("I8080overFSMC __init__")

        # Determine FSMC control pins from config
        printer = config.get_printer()
        self.mcu = mcu.get_printer_mcu(printer, config.get('fsmc_mcu', 'mcu'))
        ppins = printer.lookup_object("pins")
        cs_pin_param = ppins.lookup_pin(config.get('fsmc_cs_pin'), share_type=None)
        self.cs_pin = cs_pin_param['pin']
        rs_pin_param = ppins.lookup_pin(config.get('fsmc_rs_pin'), share_type=None)
        self.rs_pin = rs_pin_param['pin']
        if cs_pin_param['chip'] != self.mcu or rs_pin_param['chip'] != self.mcu:
            raise ppins.error("%s: fsmc pins must be on same mcu" % (config.get_name(),))
        
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
        
    def send_data(self, data):
#        logging.debug("I8080overFSMC.send_data:%r", repr(data))
        self.i8080_send_data16_cmd.send([self.oid, data])

    def send_cmd(self, cmd, param=[]):
#        logging.debug("I8080overFSMC send_cmd:%d %s", cmd, repr(param))
        if not param:
            self.i8080_send_cmd_cmd.send([self.oid, cmd])
        else:
            self.i8080_send_cmd_param8_cmd.send([self.oid, cmd, bytearray(param)])

# The SSD1963 is a display controller with a 1215K byte frame buffer and
# supports up to 864 x 480 x 24bit graphics content. It also equips a parallel
# MCU interface in different bus width to receive graphics data and command
# from the MCU.

# class SSD1963(DisplayBase):
#     def __init__(self, config):
#         self.width = config.getint('lcd_width', 480, minval=0, maxval=864)
#         self.height = config.getint('lcd_height', 272, minval=0, maxval=480)
#         self.io = I8080overFSMC(config)
# #        DisplayBase.__init__(self, self.io, columns=self.width, rows=self.height)
#         DisplayBase.__init__(self, self.io)
class SSD1963(TextFrameBuffer):
    def __init__(self, config):
        self.width = config.getint('lcd_width', 480, minval=0, maxval=864)
        self.height = config.getint('lcd_height', 272, minval=0, maxval=480)
        self.io = I8080overFSMC(config)
        TextFrameBuffer.__init__(self, self.io)
    def init(self):
        logging.debug("SSD1963.init")

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
        #REG(0xE6);   // 12Mhz
        #i8080_send_cmd_param8 oid=1 cmd=230 param=013332
        self.io.send_cmd(0xE6,[0x01, 0x33, 0x32])
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

#        self.io.get_mcu().lookup_command("i8080_fill oid=%c fact=%c", cq=self.io.get_command_queue()).send([self.io.get_oid(), 120])
