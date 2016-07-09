#!/usr/bin/python3
"""Render a list of circles with matplotlib, save as PNG"""

import sys
import os
import matplotlib.pyplot as plt

fn = sys.argv[1]
basefn,fn_ext = os.path.splitext(fn)
outfn = basefn + ".png"

def empty_circle(x,y,r,color="blue"):
    e = plt.Circle((x,y),r)
    ax = plt.gca()
    ax.add_artist(e)
    e.set_clip_box(ax.bbox)
    e.set_edgecolor(color)
    e.set_facecolor("none")
    e.set_alpha(0.5)


plt.figure(figsize=(10,10))
plt.ylim([-3,3])
plt.xlim([-3,3])
with open(fn,'rt') as infile:
    for line in infile:
        line = line.strip()
        if not line:
            continue
        x,y,r = [ float(s) for s in line.split() ]
        empty_circle(x,y,r)
plt.gca().set_aspect("equal")
plt.savefig(outfn)
