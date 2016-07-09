#!/usr/bin/python

import sys
import re

PROD = re.compile('\s*\*+\s*')

def commasep(f):
    s = ''
    for line in sys.stdin:
        s = s + line.strip('\n')
        while ',' in s:
            f,s = s.split(',',1)
            yield f
    yield s


def clean(s):
    s = s.strip(' \t []')
    if s.startswith('Id('):
        return ''
    return s

def unroll(s):
    w = ''
    for t in PROD.split(s):
        if '^' in t:
            g,ns = t.split('^')
            n = int(ns)
            if n > 0:
                w += g*int(n)
            else:
                w += g.upper() * (-n)
        else:
            w += t
    return w

for e in commasep(sys.stdin):
    print(unroll(clean(e)))
