#!/usr/bin/python3
"""Print info about a CPJ or CPZ file"""
import serialization as ser
import dcel
import sys
import textwrap
import collections

import argparse
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('input',
                    help='Input file (CPJ or CPZ)')
args = parser.parse_args()

meta,D,ch,P = ser.zloadfn(args.input)

indent = '    '

print('Metadata:')
for k in sorted(meta.keys()):
    print(textwrap.fill(indent + str(k) + ': ' + str(meta[k])))

print('\nDCEL:')
print(indent + 'uuid: '+str(D.uuid))
print(indent + '#vert: '+str(len(D.V)))
print(indent + '#edge: '+str(len(D.E)))
print(indent + '#face: '+str(len(D.F)))
print(indent + '#uedge: '+str(len(D.UE))+' ( = vert/2 + %d )'%(len(D.UE) - len(D.E)//2))

print('\nEdge lists:')
if isinstance(ch,collections.Mapping):
    for k in sorted(ch.keys()):
        print(indent + str(k) + ': %d edges' % len(ch[k]))
else:
    for k,L in enumerate(ch):
        print(indent + str(k) + ': %d edges' % len(L))

print('\nPackings:')
print(indent + 'total: %d' % len(P))
