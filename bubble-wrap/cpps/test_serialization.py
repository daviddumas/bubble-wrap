"""Write and read back DCEL, compare results"""
import serialization as ser
import triangulations
import dcel
import cocycles
import numpy as np
from collections import defaultdict,Mapping

OUTPATH = 'output/test/'

mutableD,t,b = triangulations.cylinder(10,10)
dcel.glue_boundary(mutableD,t,b,t.boundary_forward(5))

chain_down = [t]
while True:
    e = chain_down[-1]
    a = e.tri_cw
    b = a.vert_ccw
    c = b.vert_ccw
    chain_down += [a,b,c]
    if c == t:
        break        

chain_right = [t]
while True:
    e = chain_right[-1]
    a = e.vert_ccw
    b = a.vert_ccw
    c = b.tri_cw
    chain_right += [a,b,c]
    if c == t:
        break

    # Freeze and index the DCEL
D = cocycles.InterstitialDCEL(mutableD)

def assert_DCELs_similar(D1,D2):
    topo1 = dcel.oriented_manifold_type(D1)
    topo2 = dcel.oriented_manifold_type(D2)
    for k in topo1:
        assert topo1[k] == topo2[k]
    for e1,e2 in zip(D1.E,D2.E):
        assert e1.idx == e2.idx
        assert e1.uidx == e2.uidx
        assert (e1.twin and e2.twin) or (not e1.twin and not e2.twin)
        assert e1.next.idx == e2.next.idx
        assert e1.prev.idx == e2.prev.idx
    for v1,v2 in zip(D1.V,D2.V):
        assert v1.idx == v2.idx
        assert v1.valence == v2.valence
        assert v1.is_interior == v2.is_interior
    for f1,f2 in zip(D1.F,D2.F):
        assert f1.edge.idx == f2.edge.idx
        
X = np.ones(D.nx) * 1.85

print('out1',end='')
with open(OUTPATH+'out1.cpj','wt',encoding='utf-8') as outfile:
    ser.storefp(outfile,D,edge_lists = {'basepoint': [t], 'A':chain_down, 'B':chain_right},packings=[X])
with open(OUTPATH+'out1.cpj','rt',encoding='utf-8') as infile:
    meta, Din, ELin, Pin = ser.loadfp(infile)
assert_DCELs_similar(D,Din)
assert ELin['basepoint'][0].idx == t.idx
    
print(' ✓\nout2',end='')
with open(OUTPATH+'out2.cpj','wt',encoding='utf-8') as outfile:
    s = ser.stores(D,edge_lists = [ [t], chain_down, chain_right ], packings={'first':X})
    outfile.write(s)
with open(OUTPATH+'out2.cpj','rt',encoding='utf-8') as infile:
    sin = infile.read()
meta, Din, ELin, Pin = ser.loads(sin)
assert_DCELs_similar(D,Din)
assert ELin[0][0].idx == t.idx
    
print(' ✓\nout3',end='')
ser.zstorefn(OUTPATH+'out3.cpj',D,edge_lists = [ [t], chain_down, chain_right ], packings=[X,1.1*X])
meta, Din, ELin, Pin = ser.zloadfn(OUTPATH+'out3.cpj')
assert_DCELs_similar(D,Din)
assert ELin[0][0].idx == t.idx
assert len(Pin) == 2

print(' ✓\nout4',end='')
ser.zstorefn(OUTPATH+'out4.cpz',D,edge_lists = [ [t], chain_down, chain_right ], packings=[X,1.1*X])
meta, Din, ELin, Pin = ser.zloadfn(OUTPATH+'out4.cpz')
assert_DCELs_similar(D,Din)
assert ELin[0][0].idx == t.idx
assert len(Pin) == 2

print(' ✓\nout5',end='')
unicode_description = 'Teichmüller Theory = 100€' # Test UTF-8
ser.zstorefn(OUTPATH+'out5.cpz',D,meta={'description':unicode_description})
meta, Din, ELin, Pin = ser.zloadfn(OUTPATH+'out5.cpz')
assert_DCELs_similar(D,Din)
assert meta['description'] == unicode_description
assert ELin == None
assert Pin == None

print(' ✓')
