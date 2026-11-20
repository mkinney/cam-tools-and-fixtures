"""Standard twist-drill size series (facts, no vendor data).

- Inch: number drills #1-#80 and letter drills A-Z (decimal inch), and
  fractional sizes - the ANSI/ASME B94.11M size series.
- Jobber lengths (inch), fractional anchors: B94.11M straight-shank jobber
  flute length and overall length at each 1/64" fractional size
  (1/64-1/2). A number/letter size between two anchors takes the SHORTER
  neighbour's lengths unless a public product page states its own (see
  build_drills.py) - under-claiming reach is the safe side.
- Metric: ISO 235 (DIN 338) jobber series, flute length l2 and overall
  length l1 by diameter range "over a up to and including b".
"""
from fractions import Fraction as F

NUMBER = {1: .2280, 2: .2210, 3: .2130, 4: .2090, 5: .2055, 6: .2040, 7: .2010, 8: .1990, 9: .1960,
          10: .1935, 11: .1910, 12: .1890, 13: .1850, 14: .1820, 15: .1800, 16: .1770, 17: .1730,
          18: .1695, 19: .1660, 20: .1610, 21: .1590, 22: .1570, 23: .1540, 24: .1520, 25: .1495,
          26: .1470, 27: .1440, 28: .1405, 29: .1360, 30: .1285, 31: .1200, 32: .1160, 33: .1130,
          34: .1110, 35: .1100, 36: .1065, 37: .1040, 38: .1015, 39: .0995, 40: .0980, 41: .0960,
          42: .0935, 43: .0890, 44: .0860, 45: .0820, 46: .0810, 47: .0785, 48: .0760, 49: .0730,
          50: .0700, 51: .0670, 52: .0635, 53: .0595, 54: .0550, 55: .0520, 56: .0465, 57: .0430,
          58: .0420, 59: .0410, 60: .0400, 61: .0390, 62: .0380, 63: .0370, 64: .0360, 65: .0350,
          66: .0330, 67: .0320, 68: .0310, 69: .0292, 70: .0280, 71: .0260, 72: .0250, 73: .0240,
          74: .0225, 75: .0210, 76: .0200, 77: .0180, 78: .0160, 79: .0145, 80: .0135}
LETTER = {"A": .234, "B": .238, "C": .242, "D": .246, "E": .250, "F": .257, "G": .261, "H": .266,
          "I": .272, "J": .277, "K": .281, "L": .290, "M": .295, "N": .302, "O": .316, "P": .323,
          "Q": .332, "R": .339, "S": .348, "T": .358, "U": .368, "V": .377, "W": .386, "X": .397,
          "Y": .404, "Z": .413}


def _f(s):
    w, _, fr = s.partition("-")
    if "/" in w:
        return F(w)
    return F(int(w)) + (F(fr) if fr else 0)


# 64ths -> (flute length, overall length), inch, jobber series.
_JOBBER_IN = {
    1: ("3/16", "3/4"), 2: ("1/2", "1-3/8"), 3: ("3/4", "1-3/4"), 4: ("7/8", "1-7/8"),
    5: ("1", "2"), 6: ("1-1/4", "2-1/4"), 7: ("1-1/2", "2-5/8"), 8: ("1-5/8", "2-3/4"),
    9: ("1-3/4", "2-7/8"), 10: ("2", "3-1/8"), 11: ("2-1/8", "3-1/4"), 12: ("2-5/16", "3-1/2"),
    13: ("2-7/16", "3-5/8"), 14: ("2-1/2", "3-3/4"), 15: ("2-5/8", "3-7/8"), 16: ("2-3/4", "4"),
    17: ("2-7/8", "4-1/8"), 18: ("2-15/16", "4-1/4"), 19: ("3-1/16", "4-3/8"), 20: ("3-3/16", "4-1/2"),
    21: ("3-5/16", "4-5/8"), 22: ("3-7/16", "4-3/4"), 23: ("3-1/2", "4-7/8"), 24: ("3-5/8", "5"),
    25: ("3-3/4", "5-1/8"), 26: ("3-7/8", "5-1/4"), 27: ("3-15/16", "5-3/8"), 28: ("4-1/16", "5-1/2"),
    29: ("4-3/16", "5-5/8"), 30: ("4-5/16", "5-3/4"), 31: ("4-3/8", "5-7/8"), 32: ("4-1/2", "6"),
}
JOBBER_IN = {n: (float(_f(a)), float(_f(b))) for n, (a, b) in _JOBBER_IN.items()}


def jobber_inch(d_in):
    """(flute, oal, how) for an inch diameter from the fractional anchors."""
    n = d_in * 64
    if abs(n - round(n)) < 1e-6 and int(round(n)) in JOBBER_IN:
        return (*JOBBER_IN[int(round(n))], "B94.11M fractional")
    lo = int(n)  # the anchor at or below
    if lo < 1:
        lo = 1
    lo = min(lo, 32)
    return (*JOBBER_IN[lo], f"shorter neighbour {lo}/64 (between anchors)")


# ISO 235 jobber: (over, up to incl, l2 flute, l1 overall), mm.
ISO235 = [(0.95, 1.06, 12, 34), (1.06, 1.18, 14, 36), (1.18, 1.32, 16, 38), (1.32, 1.50, 18, 40),
          (1.50, 1.70, 20, 43), (1.70, 1.90, 22, 46), (1.90, 2.12, 24, 49), (2.12, 2.36, 27, 53),
          (2.36, 2.65, 30, 57), (2.65, 3.00, 33, 61), (3.00, 3.35, 36, 65), (3.35, 3.75, 39, 70),
          (3.75, 4.25, 43, 75), (4.25, 4.75, 47, 80), (4.75, 5.30, 52, 86), (5.30, 6.00, 57, 93),
          (6.00, 6.70, 63, 101), (6.70, 7.50, 69, 109), (7.50, 8.50, 75, 117), (8.50, 9.50, 81, 125),
          (9.50, 10.60, 87, 133), (10.60, 11.80, 94, 142), (11.80, 13.20, 101, 151)]


def jobber_metric(d):
    for a, b, l2, l1 in ISO235:
        if a < d <= b + 1e-9:
            return l2, l1
    return None


def gauge_to_inch(label):
    """'#7' -> .201, 'Q' -> .332, '1/4' -> .25; None if unknown."""
    s = label.strip().upper().replace("NO.", "#")
    if s.startswith("#") and s[1:].isdigit():
        return NUMBER.get(int(s[1:]))
    if len(s) == 1 and s in LETTER:
        return LETTER[s]
    try:
        return float(_f(s))
    except (ValueError, ZeroDivisionError):
        return None
