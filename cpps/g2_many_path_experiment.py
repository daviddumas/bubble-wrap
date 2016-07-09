"""Print command lines for many genus 2 deformations"""

import itertools
import os

for v in itertools.product([0,1,-1],repeat=6):
    if v == (0,0,0,0,0,0):
        continue
    s = ''.join('0+-'[i] for i in v)
    fn = 'output/g2deform-many/g2deform.'+s+'.cpz'
    if not os.path.exists(fn):
        print('./g2_deformer.py --tmax 5000 --tstep 5 -o {} --normalize output/KAT/g2-5x5-c4.KAT.labeled.cpz "{}"'.format(fn,list(v)))

