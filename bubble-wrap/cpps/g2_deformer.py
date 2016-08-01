#!/usr/bin/python3
"""Load a circle packing and deform by prescribing the change in some marked edges"""
import argparse
import datetime

import numpy as np

import cocycles
import lsons
import serialization as ser

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('input', help='Input file (CPJ or CPZ)')
parser.add_argument('vector', help='Cross ratio deformation vector (comma-seprated array of floats)')
parser.add_argument('--output', '-o', help='Output file')
parser.add_argument('--tmax', '-T', type=int, help='Attempt to deform until t=tmax, where t=1 means that log(xratio) changes by 1/|edges|^2',default=1000)
g = parser.add_mutually_exclusive_group(required=False)
g.add_argument('--nstep', '-n', type=int, help='Number of steps (default: 100)')
g.add_argument('--tstep', '-t', type=float, help='Time step')
parser.add_argument('--fixed-edge-key', '-k', help='Name or index of edge list containing the fixed edges',default='fixed_edges')
parser.add_argument('--initial-packing-key', '-p', help='Name or index of initial packing',default='0')
parser.add_argument('--normalize', help='Normalize deformation vector', action='store_true')
parser.add_argument('--description', '-d', help='Description to store in output file (defaut includes the deformation vector)')

args=parser.parse_args()
if args.tstep == None and args.nstep == None:
    tstep = args.tmax / 100.0
elif args.tstep == None:
    tstep = args.tmax / args.nstep
else:
    tstep = args.tstep

np.set_printoptions(suppress=True)

meta,D,ch,P = ser.zloadfn(args.input,cls=cocycles.InterstitialDCEL)

if not args.output:
    ustr = str(D.uuid)[-12:]
    tstr = datetime.datetime.utcnow().strftime('%Y-%m-%d-%H%M%S')
    args.output = 'deform-' + ustr + '-' + tstr + '.cpz'
    print('INFO: Using output filename "%s"' % args.output)

vector = np.fromstring(args.vector.strip().strip('[]'),sep=',')
if args.normalize:
    vector = vector / np.linalg.norm(vector)
print('INFO: Using deformation vector %s' % str(vector))
    
try:
    fixed_edges = ch[args.fixed_edge_key]
except TypeError:
    fixed_edges = ch[int(args.fixed_edge_key)]

try:
    X0 = P[args.initial_packing_key]
except TypeError:
    X0 = P[int(args.initial_packing_key)]
    
fixed_indices = [ e.uidx for e in fixed_edges ]
free_indices = [ i for i in range(D.nx) if i not in fixed_indices ]
invperm = np.argsort(fixed_indices + free_indices)

def deform_fun(LXfix,LXfree):
    LXperm = np.append(LXfix,LXfree)
    LX = np.array([LXperm[i] for i in invperm])
    X = np.exp(LX)
    Y = D.packing_defect(X)
    return Y

LX0 = np.log(X0)
LXfix0 = np.array( [ LX0[i] for i in fixed_indices ] )
LXfree0 = np.array( [ LX0[i] for i in free_indices ] )

epsilon = 1.0 / (D.nx**2)
print('INFO: epsilon = (1/edges)^2 =',epsilon)

def lift_path(f,xfix_path,xfree0,t0,t1,tstep,normgoal=1e-5):
    xfree = xfree0
    for t in np.arange(t0,t1,tstep):
        xfix = xfix_path(t)
        print('t=',t,'fix=',xfix)
        fun = lambda t:f(xfix,t)
        jac = lambda t:lsons.numjac(fun,t)
        xfree = lsons.lsroot(fun,jac,xfree,maxcond=1e20,maxiter=200,relax=0.8,normgoal=normgoal,verbose=True)
        yield t,xfree


def gamma(t):
    return LXfix0 + t*epsilon*vector

print('GOAL: t=%f, xfix=%s',(1,str(gamma(1))))
vectors = []

try:
    for t,LXfree in lift_path(deform_fun,gamma,LXfree0,0,args.tmax,tstep,normgoal=1e-8*np.sqrt(len(X0))):
        LXperm = np.append(gamma(t),LXfree)
        LX = np.array([LXperm[i] for i in invperm])
        X = np.exp(LX)
        vectors.append( (t,X) )
        print('max(X) = %f, min(X) = %f' % (max(X),min(X)))
except lsons.SolverException as e:
    print('Aborting on exception: ',e)

print('Final t=',t)

packings = dict(vectors)
desc = 'Deforming edge cross ratios in direction of V=%s' % str(args.vector)    
ser.zstorefn(args.output,D,edge_lists=ch,packings=packings,meta={'description':desc})
