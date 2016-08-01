# This script is only ever needed ONCE;  It marks some edges on a genus 2 DCEL previously stored.
import numpy as np

import serialization as ser

np.set_printoptions(suppress=True)
meta,D,ch,P = ser.zloadfn('output/KAT/g2-5x5-c4.KAT-cand6.cpz')

t1 = ch['t1'][0]
t2 = ch['t2'][0]
X0 = P[0]

def cyl_down(e):
    a = e.tri_cw
    b = a.vert_ccw
    c = b.vert_ccw
    return c

def cyl_right(e):
    a = e.vert_ccw
    b = a.vert_ccw
    c = b.tri_cw
    return c

def cyl_up(e):
    a = e.vert_cw
    b = a.vert_cw
    c = b.tri_ccw
    return c

def cyl_left(e):
    a = e.tri_ccw
    b = a.vert_cw
    c = b.vert_cw
    return c


m1a = cyl_right(cyl_right(cyl_down(cyl_down(t1))))
m1b = m1a.vert_ccw.vert_ccw
m1c = m1b.vert_ccw.vert_ccw

m2a = cyl_left(cyl_left(cyl_up(cyl_up(t2))))
m2b = m2a.vert_cw.vert_cw
m2c = m2b.vert_cw.vert_cw

ch['fixed_edges'] = [m1a,m1b,m1c,m2a,m2b,m2c]

ser.zstorefn('output/KAT/g2-5x5-c4.KAT.labeled.cpz',D,edge_lists=ch,packings=P,meta={'description':'KAT packing for a genus 2 surface obtained by doubling a one-holed torus obtained by partially gluing boundary curves of a 5x5 cylinder.  The separating curve has length 4.  Six curves are marked, comprising alternating triples at two vertices related by the orientation-reversing isometry.'} )
