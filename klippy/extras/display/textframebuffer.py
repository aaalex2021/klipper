# TextFrameBuffer class provides a character display on top of a 16 bit
# graphics display. It uses an IO adapter to send the graphics t0 the display
#
# Copyright (C) 2021  Kevin O'Connor <kevin@koconnor.net>
# Copyright (C) 2021  Alex Peuchert <aaalex2021@ki2s.com>
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import logging
from . import font16x26

CHAR_HEIGHT = 26
CHAR_WIDTH = 16

class TextFrameBuffer:
    def __init__(self, io, columns=16, rows=4, screen_width=0, screen_height=0,
                 fgcolor=0xFFFF, bgcolor=0x0000):
        self.send_cmd = io.send_cmd
        self.send_data = io.send_data
        self.send_fill = io.send_fill
        self.columns = columns
        self.rows = rows
        self.x_offset = (screen_width - CHAR_WIDTH*self.columns) /2
        self.y_offset = (screen_height - CHAR_HEIGHT*self.rows) /2
        self.fgcolor = [fgcolor>>8, fgcolor & 0xFF]
        self.bgcolor = [bgcolor>>8, bgcolor & 0xFF]
        self.vram = [[0x00] * self.columns for i in range(self.rows)]
        self.font = [self._swizzle_bits(bytearray(c))
                     for c in font16x26.VGA_FONT_16x26]
        self.icons = {}
        self.tbuf_old = [['~' for j in range(self.columns)]
                         for i in range(self.rows)]
        self.clear()

    def get_dimensions(self):
        return (self.columns, self.rows)
    def set_glyphs(self, glyphs):
        for glyph_name, glyph_data in glyphs.items():
            icon = glyph_data.get('icon16x16')
            if icon is not None:
                icon_words = [ 0, 0, 0, 0, 0, 0, 0, 0]
                for ba in zip(icon[0],icon[1]):
                    icon_words = icon_words + [ba[1], ba[0]]
                icon_words = icon_words + [ 0, 0, 0, 0, 0, 0, 0, 0]
                self.icons[glyph_name] = self._swizzle_bits(icon_words)
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
    def clear(self):
        self.tbuf = [[' ' for j in range(self.columns)]
                     for i in range(self.rows)]
    def flush(self):
        for new_row, old_row, cy in zip(self.tbuf, self.tbuf_old,
                                        [self.y_offset+y*CHAR_HEIGHT
                                         for y in range(self.rows)]):
            for ch, old_ch, cx in zip(new_row, old_row,
                                      [self.x_offset+x*CHAR_WIDTH
                                       for x in range(self.columns)]):
                if ch == old_ch: continue
                if len(ch) != 1:
                    chx = self.icons.get(ch)
                else:
                    chx = self.font[ord(ch)]
                self._fill_into_region(cx, cx+(CHAR_WIDTH-1),
                                       cy, cy+(CHAR_HEIGHT-1),
                                       chx)
        self.tbuf_old = self.tbuf
    def write_text(self, x, y, data):
        if not len(data) or y >= self.rows: return
        if x + len(data) > self.columns:
            data = data[:self.columns - min(x, self.columns)]
        self.tbuf[y][x:x+len(data)] = data
    def write_glyph(self, x, y, glyph_name):
        if x >= self.columns or y >= self.rows:
            return 1
        self.tbuf[y][x] = glyph_name
        return 1
    def write_graphics(self, x, y, data):
        pass
