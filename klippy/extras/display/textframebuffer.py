# TextFrameBuffer class provides a character display on top of a 16 bit
# graphics display. It uses an IO adapter to send the graphics ti the display
#
# Copyright (C) 2018-2019  Kevin O'Connor <kevin@koconnor.net>
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import logging
from . import font16x24

CHAR_HEIGHT = 24
CHAR_WIDTH = 16

class TextFrameBuffer:
    def __init__(self, io, columns=16, rows=4, fgcolor=0xFFFF, bgcolor=0x0000):
        self.send_cmd = io.send_cmd
        self.send_data = io.send_data
        self.send_fill = io.send_fill
        self.columns = columns
        self.rows = rows
        # [0,31]
        self.fgcolor = [fgcolor>>8, fgcolor & 0xFF]
        # [0,0]
        self.bgcolor = [bgcolor>>8, bgcolor & 0xFF]
        self.vram = [[0x00] * self.columns for i in range(self.rows)]
        # Cache fonts and icons in display byte order
        self.font = [self._swizzle_bits(bytearray(c))
                     for c in font16x24.VGA_FONT_16x24]
        self.icons = {}
    def set_glyphs(self, glyphs):
#        logging.debug("TFB.set_glyphs %s", repr(glyphs))
        for glyph_name, glyph_data in glyphs.items():
            icon = glyph_data.get('icon16x16')
            if icon is not None:
                icon_words = [ 0, 0, 0, 0, 0, 0, 0, 0]
                for ba in zip(icon[0],icon[1]):
                    icon_words = icon_words + [ba[1], ba[0]]
                icon_words = icon_words + [ 0, 0, 0, 0, 0, 0, 0, 0]
                self.icons[glyph_name] = self._swizzle_bits(icon_words)
#                logging.debug("TFB.set_glyphs %s: %s", glyph_name, repr(self.icons[glyph_name]))
    def _swizzle_bits(self, data):
        c = data
        c_out = []
        for i in range(len(c)/2):
            c_row = c.pop(0) | c.pop(0)<<8
            ar = []
            for b in format(c_row,'016b'):
                ar = ar + (self.fgcolor if b=='1' else self.bgcolor)
            c_out.append(ar);
        return [ bytearray(row) for row in c_out ]
    def flush(self):
        logging.debug("TFB.flush")
    def write_text(self, x, y, data):
#        import pdb; pdb.set_trace()
        if not len(data) or y >= self.rows: return
        if x + len(data) > self.columns:
            data = data[:self.columns - min(x, self.columns)]
        cx = x * CHAR_WIDTH
        cy = y * CHAR_HEIGHT
        for c in bytearray(data):
            self._fill_into_region(cx, cx+(CHAR_WIDTH-1), cy, cy+(CHAR_HEIGHT-1), self.font[c])
            cx += CHAR_WIDTH
        
    def write_graphics(self, x, y, data):
#        logging.debug("TFB.write_graphics x:%d y:%d data:%s:", x, y, data)
        pass
    def write_glyph(self, x, y, glyph_name):
        logging.debug("TFB.write_glyph x:%d y:%d data:%s:", x, y, glyph_name)
        if x >= self.columns or y >= self.rows:
            return 1
        self._fill_into_region(x * CHAR_WIDTH, x * CHAR_WIDTH +(CHAR_WIDTH-1),
                               y * CHAR_HEIGHT, y * CHAR_HEIGHT+(CHAR_HEIGHT-1),
                               self.icons.get(glyph_name))
        return 1
    def clear(self):
        logging.debug("TFB.clear")
    def get_dimensions(self):
        logging.debug("TFB.get_dimensions")
#        import pdb; pdb.set_trace()
        return (self.columns, self.rows)
        
