"""Test DCEL manipulations"""

# TODO: Update this to do more; now it only tests reverse_orientation()

from collections import defaultdict

import dcel
import triangulations

D1,t1,b1 = triangulations.cylinder(5,5)
t1g = t1.boundary_forward(2)
dcel.glue_boundary(D1,t1,b1,t1g)

D2,t2,b2 = triangulations.cylinder(5,5)
t2g = t2.boundary_forward(2)
dcel.glue_boundary(D2,t2,b2,t2g)

def assert_DCELs_homeo(D1,D2):
    topo1 = dcel.oriented_manifold_type(D1)
    topo2 = dcel.oriented_manifold_type(D2)
    for k in topo1:
        assert topo1[k] == topo2[k]
    valences1 = defaultdict(int)
    valences2 = defaultdict(int)
    for v in D1.V:
        valences1[v.valence] += 1
    for v in D2.V:
        valences2[v.valence] += 1
    for k in valences1:
        assert k in valences2 and valences1[k]==valences2[k]


print('Same orientation')
assert_DCELs_homeo(D1,D2)
print('Opposite orientation')
dcel.reverse_orientation(D2)
assert_DCELs_homeo(D1,D2)
print('Doubled:')
D = D1 | D2
dcel.glue_boundary(D,t1g,t2g)

topo = dcel.oriented_manifold_type(D)
for k in topo:
    print(k,topo[k])
