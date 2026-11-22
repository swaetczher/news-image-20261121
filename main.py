#!/usr/bin/env python3
"""The World in One Day -- world news summary for Saturday, 21 November 2026.

Renders one 1024x1024 PNG to /output/entry.png. Stdlib only (argparse,
hashlib, os, struct, sys, zlib). No network at run time. Fully deterministic:
two runs write byte-identical output.

Layout: newspaper poster. Masthead + big date, one hero panel (Strait of
Hormuz, two tankers hit), four medium panels (Mexico, Kryvyi Rih, markets,
COP31), one bottom strip (BepiColombo / Cyclone Akvan or Peru quake).
"""

import argparse
import hashlib
import math
import os
import struct
import sys
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette ---
PAPER = (247, 242, 232)
INK = (18, 26, 44)
NAVY = (22, 38, 66)
RED = (176, 32, 32)
SEA = (36, 96, 148)
SEA_DARK = (24, 68, 110)
SAND = (226, 205, 158)
SAND_DARK = (203, 178, 124)
WHITE = (255, 255, 255)
GREY = (110, 110, 105)
LIGHT_GREY = (228, 228, 222)
TEAL = (16, 104, 98)
ORANGE = (214, 106, 24)
GOLD = (198, 158, 40)
GREEN = (34, 120, 62)
STEEL = (96, 108, 124)
DARK_RED = (140, 20, 20)

# ------------------------------------------------------------- 5x7 bitmap ---
# Each glyph: 7 rows, 5 bits (bit 4 = leftmost column). Classic 5x7 face.
FONT = {
    ' ': (0, 0, 0, 0, 0, 0, 0),
    'A': (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    'B': (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    'C': (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    'D': (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    'E': (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    'F': (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    'G': (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    'H': (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    'I': (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    'J': (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    'K': (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    'L': (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    'M': (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    'N': (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    'O': (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    'P': (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    'Q': (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    'R': (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    'S': (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    'T': (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    'U': (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    'V': (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    'W': (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    'X': (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    'Y': (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    'Z': (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    '0': (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    '1': (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    '2': (0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F),
    '3': (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    '4': (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    '5': (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    '6': (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    '7': (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    '8': (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    '9': (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    '.': (0, 0, 0, 0, 0, 0x0C, 0x0C),
    ',': (0, 0, 0, 0, 0x0C, 0x04, 0x08),
    ':': (0, 0x0C, 0x0C, 0, 0x0C, 0x0C, 0),
    ';': (0, 0x0C, 0x0C, 0, 0x0C, 0x04, 0x08),
    '!': (0x04, 0x04, 0x04, 0x04, 0x04, 0, 0x04),
    '?': (0x0E, 0x11, 0x01, 0x02, 0x04, 0, 0x04),
    "'": (0x04, 0x04, 0x08, 0, 0, 0, 0),
    '-': (0, 0, 0, 0x1F, 0, 0, 0),
    '(': (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ')': (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    '/': (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    '%': (0x19, 0x19, 0x02, 0x04, 0x08, 0x13, 0x13),
    '&': (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    '+': (0, 0x04, 0x04, 0x1F, 0x04, 0x04, 0),
    '=': (0, 0, 0x1F, 0, 0x1F, 0, 0),
    '"': (0x0A, 0x0A, 0x0A, 0, 0, 0, 0),
    '*': (0, 0x04, 0x15, 0x0E, 0x15, 0x04, 0),
}

SPACE = FONT[' ']


def norm_char(ch):
    """Map lookalike punctuation to glyphs we actually have."""
    if ch in ('\u2019', '\u2018', '\u201c', '\u201d'):
        return "'"
    if ch in ('\u2013', '\u2014'):
        return '-'
    if ch == '\u2022':
        return '*'
    return ch.upper()


# ------------------------------------------------------------------ canvas ---
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def _px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = color[0]
            self.buf[i + 1] = color[1]
            self.buf[i + 2] = color[2]

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        r, g, b = color
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.buf[i] = r
                self.buf[i + 1] = g
                self.buf[i + 2] = b

    def rect(self, x, y, w, h, color, t=1):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def hline(self, x, y, w, color, t=1):
        self.fill_rect(x, y, w, t, color)

    def vline(self, x, y, h, color, t=1):
        self.fill_rect(x, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.fill_rect(x - t // 2, y - t // 2, t, t, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def poly(self, pts, color):
        """Fill a polygon by scanline fill (convex-ish shapes only)."""
        if not pts:
            return
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    if y1 != y0:
                        x = x0 + (y - y0) * (x1 - x0) // (y1 - y0)
                        xs.append(x)
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.hline(xs[k], y, xs[k + 1] - xs[k] + 1, color)

    def circle(self, cx, cy, r, color, fill=True):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                d2 = (x - cx) ** 2 + (y - cy) ** 2
                if fill:
                    if d2 <= r * r:
                        self._px(x, y, color)
                else:
                    if r * r - 2 * r <= d2 <= r * r:
                        self._px(x, y, color)

    def ring(self, cx, cy, r, color, t=3):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                d2 = (x - cx) ** 2 + (y - cy) ** 2
                if (r - t) ** 2 <= d2 <= r * r:
                    self._px(x, y, color)

    # ------------------------------------------------------------- text ------
    def text_w(self, s, sc):
        return len(s) * 6 * sc - sc if s else 0

    def text(self, x, y, s, sc, color):
        cx = x
        for raw in s:
            ch = norm_char(raw)
            glyph = FONT.get(ch, SPACE)
            for row in range(7):
                bits = glyph[row]
                if bits == 0:
                    continue
                for col in range(5):
                    if bits & (1 << (4 - col)):
                        self.fill_rect(cx + col * sc, y + row * sc, sc, sc, color)
            cx += 6 * sc
        return cx

    def text_center(self, cx, y, s, sc, color):
        self.text(cx - self.text_w(s, sc) // 2, y, s, sc, color)

    def wrap(self, s, sc, max_w):
        lines = []
        for para in s.split('\n'):
            words = para.split(' ')
            cur = ''
            for word in words:
                trial = word if not cur else cur + ' ' + word
                if self.text_w(trial, sc) <= max_w:
                    cur = trial
                else:
                    if cur:
                        lines.append(cur)
                    cur = word
            if cur:
                lines.append(cur)
        return lines

    def block(self, x, y, lines, sc, color, leading=None):
        if leading is None:
            leading = 9 * sc
        for ln in lines:
            self.text(x, y, ln, sc, color)
            y += leading
        return y


# -------------------------------------------------------------- illustrations -
def starburst(cv, cx, cy, r, c1, c2):
    for k in range(8):
        ang = k * math.pi / 4.0
        x2 = int(cx + r * math.cos(ang))
        y2 = int(cy + r * math.sin(ang))
        cv.line(cx, cy, x2, y2, c1, 3)
    cv.circle(cx, cy, max(3, r // 3), c2, fill=True)


def tanker(cv, x, y, w, h, hull, deck):
    cv.fill_rect(x, y + h // 3, w, (2 * h) // 3, hull)
    cv.fill_rect(x + w // 8, y, w // 4, h // 3, deck)
    cv.fill_rect(x + w // 2, y + h // 6, w // 6, h // 6, deck)
    cv.line(x + w, y + h // 3, x + w + w // 6, y + h // 3, hull, 3)
    # waterline
    cv.hline(x - 4, y + h, w + 8, WHITE, 2)


def hormuz_map(cv, x, y, w, h):
    """Stylised Strait of Hormuz: blue sea, two sandy coasts, two tankers."""
    cv.fill_rect(x, y, w, h, SEA)
    # Iran coast, top-left
    cv.poly([(x, y), (x + int(w * 0.52), y), (x + int(w * 0.34), y + int(h * 0.30)),
             (x + int(w * 0.12), y + int(h * 0.34)), (x, y + int(h * 0.22))], SAND)
    # Oman coast, bottom-right
    cv.poly([(x + w, y + h), (x + int(w * 0.58), y + h),
             (x + int(w * 0.66), y + int(h * 0.66)), (x + int(w * 0.86), y + int(h * 0.60)),
             (x + w, y + int(h * 0.52))], SAND)
    # shipping lane dashes through the strait
    for k in range(9):
        dx = x + int(w * 0.12) + k * int(w * 0.085)
        dy = y + int(h * 0.42) + k * int(h * 0.05)
        cv.line(dx, dy, dx + 16, dy + 8, WHITE, 2)
    # tanker 1 (stern hit, 11 NM north of Khasab)
    t1x, t1y = x + int(w * 0.16), y + int(h * 0.30)
    tanker(cv, t1x, t1y, 110, 34, INK, RED)
    starburst(cv, t1x + 8, t1y - 6, 16, GOLD, ORANGE)
    # tanker 2 (engine-room hit, 17 NM east of Khasab)
    t2x, t2y = x + int(w * 0.56), y + int(h * 0.52)
    tanker(cv, t2x, t2y, 120, 36, INK, RED)
    starburst(cv, t2x + 100, t2y - 4, 16, GOLD, ORANGE)
    # Khasab marker on the Oman coast
    kx, ky = x + int(w * 0.80), y + int(h * 0.72)
    cv.circle(kx, ky, 5, WHITE, fill=True)
    cv.circle(kx, ky, 5, RED, fill=False)
    # dark chips behind the small white labels so they stay readable
    # over both the blue sea and the pale sand
    def chip(tx, ty, s):
        cv.fill_rect(tx - 4, ty - 3, cv.text_w(s, 2) + 8, 20, NAVY)
        cv.text(tx, ty, s, 2, WHITE)
    chip(kx - 62, ky + 10, "KHASAB")
    chip(t1x - 6, t1y + 44, "11 NM N")
    chip(t2x - 6, t2y + 46, "17 NM E")
    # caption strip
    cv.fill_rect(x, y + h - 30, w, 30, NAVY)
    cv.text(x + 12, y + h - 24, "STRAIT OF HORMUZ - SATURDAY", 2, WHITE)


def handcuffs(cv, x, y, s):
    cv.ring(x, y, s, STEEL, 4)
    cv.ring(x + 3 * s, y, s, STEEL, 4)
    cv.line(x + s, y - s // 2, x + 2 * s, y - s // 2, STEEL, 4)
    cv.line(x + s, y + s // 2, x + 2 * s, y + s // 2, STEEL, 4)


def building_hit(cv, x, y, s):
    # small cracked building with a red-cross marker; sized to sit in a
    # panel kicker row without touching the headline below it
    cv.fill_rect(x, y, 3 * s, 4 * s, STEEL)
    for r in range(3):
        for c in range(2):
            cv.fill_rect(x + 3 + c * (s + 2), y + 4 + r * (s + 2), 4, 4, GOLD)
    cv.line(x, y, x + 3 * s, y + 4 * s, RED, 3)
    cs = 2 * s
    cv.fill_rect(x + 3 * s - 2, y - 3, cs, cs, RED)
    cv.fill_rect(x + 3 * s + cs // 2 - 4, y - 3 + 2, 8, cs - 4, WHITE)
    cv.fill_rect(x + 3 * s - 2 + 2, y - 3 + cs // 2 - 4, cs - 4, 8, WHITE)


def chart_fall(cv, x, y, w, h):
    cv.rect(x, y, w, h, LIGHT_GREY, 1)
    pts = [(x + 8, y + 12), (x + 26, y + 26), (x + 44, y + 20),
           (x + 62, y + 44), (x + 80, y + 40), (x + 98, y + 62)]
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], RED, 3)
    ex, ey = pts[-1]
    cv.line(ex, ey, ex - 12, ey - 2, RED, 3)
    cv.line(ex, ey, ex - 4, ey - 12, RED, 3)


def globe(cv, x, y, r):
    cv.circle(x, y, r, TEAL, fill=False)
    cv.hline(x - r, y, 2 * r, TEAL, 2)
    cv.line(x - int(r * 0.7), y - int(r * 0.7), x + int(r * 0.7), y - int(r * 0.7), TEAL, 2)
    cv.line(x - int(r * 0.7), y + int(r * 0.7), x + int(r * 0.7), y + int(r * 0.7), TEAL, 2)
    cv.text(x - 14, y - 8, "31", 2, TEAL)


def mercury(cv, x, y, r):
    cv.circle(x, y, r, (196, 164, 132), fill=True)
    cv.circle(x - r // 3, y - r // 4, r // 5, (150, 120, 92), fill=True)
    cv.circle(x + r // 4, y + r // 3, r // 6, (150, 120, 92), fill=True)
    cv.circle(x + r // 5, y - r // 2, r // 8, (150, 120, 92), fill=True)


def cyclone(cv, x, y, r):
    for k, rr in enumerate((r, int(r * 0.72), int(r * 0.45))):
        for a in range(0, 270, 6):
            import math
            rad = a * 3.141592653589793 / 180.0
            px = int(x + rr * math.cos(rad))
            py = int(y + rr * math.sin(rad))
            cv.fill_rect(px, py, 3, 3, TEAL if k % 2 == 0 else SEA)
    cv.circle(x, y, 4, TEAL, fill=True)


def quake(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, NAVY)
    pts = [(x + 4, y + h // 2), (x + 16, y + h // 2), (x + 22, y + 6),
           (x + 30, y + h - 6), (x + 38, y + h // 2), (x + 50, y + h // 2),
           (x + 56, y + 10), (x + 64, y + h - 8), (x + 72, y + h // 2),
           (x + w - 4, y + h // 2)]
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], GOLD, 2)


# ------------------------------------------------------------------ layout ---
def panel(cv, x, y, w, h, accent):
    cv.fill_rect(x, y, w, h, WHITE)
    cv.fill_rect(x, y, w, 8, accent)
    cv.rect(x, y, w, h, INK, 2)


def hero_text(cv, x, y, w):
    cv.text(x, y, "MIDDLE EAST", 2, RED)
    y += 22
    lines = cv.wrap("TWO TANKERS HIT IN THE STRAIT OF HORMUZ", 3, w)
    y = cv.block(x, y, lines, 3, INK)
    y += 10
    body = ("UKMTO confirms projectiles struck two ships "
            "off Oman. No casualties. Iran CLAIMS a third "
            "tanker hit a mine, and a US drone shot down - "
            "both unverified.")
    y = cv.block(x, y, cv.wrap(body, 2, w), 2, INK)
    return y


def build(variant):
    cv = Canvas(W, H, PAPER)
    # masthead
    cv.fill_rect(0, 0, W, 104, NAVY)
    cv.text_center(W // 2, 34, "THE WORLD IN ONE DAY", 5, WHITE)
    cv.fill_rect(0, 104, W, 46, RED)
    cv.text_center(W // 2, 113, "SATURDAY, 21 NOVEMBER 2026", 4, WHITE)

    # hero panel
    hx, hy, hw, hh = 24, 162, 976, 308
    cv.fill_rect(hx, hy, hw, hh, WHITE)
    cv.rect(hx, hy, hw, hh, INK, 3)
    if variant == 1:
        hormuz_map(cv, hx + 12, hy + 12, 430, hh - 24)
        hero_text(cv, hx + 462, hy + 22, hw - 486)
    else:
        hero_text(cv, hx + 24, hy + 22, 470)
        hormuz_map(cv, hx + hw - 442, hy + 12, 430, hh - 24)

    # four medium panels, 2x2
    px, py = 24, 482
    pw, ph = 480, 182
    gx, gy = 16, 12

    # --- Mexico: El Chapo Isidro
    panel(cv, px, py, pw, ph, GREEN)
    cv.text(px + 16, py + 20, "MEXICO", 2, GREEN)
    handcuffs(cv, px + pw - 58, py + 32, 7)
    cv.block(px + 16, py + 46, cv.wrap("MEXICO CAPTURES 'EL CHAPO ISIDRO'", 3, pw - 32), 3, INK)
    cv.block(px + 16, py + 112,
             cv.wrap("FBI top-10 fugitive seized in Sinaloa; 11 killed "
                     "in gun battle. US intelligence assisted.", 2, pw - 32),
             2, INK)

    # --- Kryvyi Rih
    x2 = px + pw + gx
    panel(cv, x2, py, pw, ph, RED)
    cv.text(x2 + 16, py + 20, "UKRAINE", 2, RED)
    building_hit(cv, x2 + pw - 46, py + 18, 6)
    cv.block(x2 + 16, py + 46, cv.wrap("KRYVYI RIH: RUSSIAN 'TRIPLE-TAP' STRIKE", 3, pw - 32), 3, INK)
    cv.block(x2 + 16, py + 112,
             cv.wrap("Child, 7, and paramedic, 20, killed; around 60 "
                     "wounded as drones hit rescuers.", 2, pw - 32),
             2, INK)

    # --- Markets
    y2 = py + ph + gy
    panel(cv, px, y2, pw, ph, ORANGE)
    cv.text(px + 16, y2 + 20, "MARKETS", 2, ORANGE)
    chart_fall(cv, px + pw - 128, y2 + 22, 112, 74)
    cv.block(px + 16, y2 + 46, cv.wrap("MARKETS PLUNGE AS AI TRADE UNRAVELS", 3, pw - 32 - 124), 3, INK)
    cv.block(px + 16, y2 + 112,
             cv.wrap("S&P 500 -3.7% - Nasdaq -5.3%, negative for the "
                     "year. Nikkei -5.1%.", 2, pw - 32),
             2, INK)

    # --- COP31
    panel(cv, x2, y2, pw, ph, TEAL)
    cv.text(x2 + 16, y2 + 20, "CLIMATE - ANTALYA", 2, TEAL)
    globe(cv, x2 + pw - 60, y2 + 52, 30)
    cv.block(x2 + 16, y2 + 46, cv.wrap("COP31: NO DEAL YET", 3, pw - 32), 3, INK)
    cv.block(x2 + 16, y2 + 112,
             cv.wrap("Climate talks run past deadline; draft drops all "
                     "fossil-fuel mention.", 2, pw - 32),
             2, INK)

    # bottom strip
    sy, sh = 870, 86
    cv.fill_rect(px, sy, 976, sh, WHITE)
    cv.rect(px, sy, 976, sh, INK, 2)
    cv.vline(px + 488, sy + 10, sh - 20, GREY, 2)
    # left: BepiColombo
    mercury(cv, px + 46, sy + sh // 2, 24)
    cv.text(px + 84, sy + 12, "ALSO TODAY", 2, TEAL)
    cv.block(px + 84, sy + 38,
             ["BEPICOLOMBO ENTERS MERCURY ORBIT",
              "ESA-JAXA, 8 YEARS ON THE WAY."],
             2, INK)
    # right: variant 1 = Cyclone Akvan, variant 2 = Peru quake
    rx = px + 504
    if variant == 1:
        cyclone(cv, rx + 40, sy + sh // 2, 26)
        cv.text(rx + 76, sy + 12, "ALSO TODAY", 2, TEAL)
        cv.block(rx + 76, sy + 38,
                 ["CYCLONE AKVAN: NO DEATHS -",
                  "440,000 EVACUATED IN INDIA."],
                 2, INK)
    else:
        quake(cv, rx + 16, sy + 18, 80, 50)
        cv.text(rx + 108, sy + 12, "ALSO TODAY", 2, TEAL)
        cv.block(rx + 108, sy + 38,
                 ["PERU QUAKE 6.9: NO CASUALTIES",
                  "- FELT IN LIMA; DEEP, 108 KM."],
                 2, INK)

    # footer
    cv.text_center(W // 2, 972, "SOURCES: UKMTO, REUTERS, AP, CNN, ESA - SATURDAY, 21 NOVEMBER 2026", 2, GREY)
    return cv


# --------------------------------------------------------------------- png ----
def _chunk(kind, data):
    out = struct.pack('>I', len(data)) + kind + data
    out += struct.pack('>I', zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path, cv):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.buf[y * stride:(y + 1) * stride]
    png = b'\x89PNG\r\n\x1a\n'
    png += _chunk(b'IHDR', struct.pack('>IIBBBBB', cv.w, cv.h, 8, 2, 0, 0, 0))
    png += _chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    png += _chunk(b'IEND', b'')
    outdir = os.path.dirname(path)
    if outdir:
        os.makedirs(outdir, exist_ok=True)
    with open(path, 'wb') as f:
        f.write(png)
    return len(png)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--variant', type=int, default=1, choices=(1, 2),
                    help='layout variant (1 or 2)')
    ap.add_argument('--out', default='/output/entry.png',
                    help='output PNG path')
    args = ap.parse_args(argv)
    cv = build(args.variant)
    size = write_png(args.out, cv)
    digest = hashlib.sha256(open(args.out, 'rb').read()).hexdigest()
    print('wrote %s (%dx%d, %d bytes, sha256 %s)'
          % (args.out, W, H, size, digest))
    return 0


if __name__ == '__main__':
    sys.exit(main())
