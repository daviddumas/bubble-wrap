"""Interstitial cocycles"""

# In the dual graph of a circle packing, triangles represent the
# interstices.  For each pair of interstices, there is a unique Mobius
# transformation which maps one to the other once a correspondence
# between cusps is chosen.  Preserving orientation means that it is
# sufficient to mark one cusp of each interstice, and to require these
# to be mapped to one another.  Thus a circle packing gives (and is
# determined by) a PSL(2,C)-valued 1-cocycle on the set of marked
# interstices.

# A marked interstice is determined by an oriented edge e of the dual
# graph of the circle packing.  Here if e is part of the oriented
# boundary of a triangle T of the dual graph, then T represents the
# interstice.  The unoriented edge underlying e represents a cusp of
# this interstice, and we take this as the marked one.

# Note all cocycles correspond to circle packings.  A necessary
# condition is that if two interstices meet at a cusp, then the
# associated Mobius map has the form (0 1; 1 *).  Any map with this
# property is called an _interstitial cocycle_ (IC).  The set of ICs
# is thus in bijection with R^(UE), where UE is the set of unoriented
# edges.

# Kamishima, Mizushima, and Tan show that the sufficient condition for
# X in R^(UE) to represent a circle packing is a flatness condition
# for each vertex of the dual graph, and an embeddedness condition
# represented by a set of inequalities for each vertex of the dual
# graph.

import numpy as np

import dcel as dcel


def _closeup(L):
    return L+L[:1]

class InterstitialDCEL(dcel.IndexedDCEL):
    """DCEL of closed triangulated surface supporting computations with interstitial cocycles"""
    @property
    def nx(self):
        """Number of unoriented edges = number of xratios"""
        return len(self.UE)

    @property
    def ny(self):
        """Number of vertices * 4 = rank of defect vector"""
        return 4*len(self.V)


    _factor_tri_ccw = np.array( [ [0, 1j], [1j, 1] ], dtype='cfloat')
    _factor_tri_cw = np.array( [ [1, -1j], [-1j, 0] ], dtype='cfloat')

    def _factor_vert_ccw(self,x):
        return np.array( [ [x, -1], [1, 0] ], dtype='cfloat')

    def _factor_vert_cw(self,x):
            return np.array( [ [0, 1], [-1, x] ], dtype='cfloat')        
    
    def holfactor(self,e1,e2,X):
        """Factor of holonomy matrix for a given cross ratio vector, x, and a basic move from marked triangle e1 to e2"""
        if e2 == e1.next:
            # CCW rotation about triangle
            return self._factor_tri_ccw
        elif e2 == e1.prev:
            # CW rotation about triangle
            return self._factor_tri_cw
        elif e2 == e1.prev.twin:
            # CCW rotation about vertex, crossed e2
            return self._factor_vert_ccw(X[e2.uidx])
        elif e2 == e1.twin.next:
            # CW rotation about vertex, crossed e1
            return self._factor_vert_cw(X[e1.uidx])
        else:
            raise ValueError("holonomy factor called on invalid pair of oriented edges")

    def hol(self,chain,X):
        """Compute holonomy of a chain of marked triangles"""
        M = np.eye(2,dtype='cfloat')
        for e1,e2 in zip(chain[:-1],chain[1:]):
            M = M.dot(self.holfactor(e1,e2,X))
        return M

    def hol_around_vertex(self,X,v):
        """Product of factors around a single vertex, index i"""
        # interior_star guarantees correct (CCW) order
        S = _closeup(list(v.interior_star()))
        return np.real(self.hol(S,X))

    def hol_around_vertices(self,X):
        return [ self.hol_around_vertex(X,v) for v in self.V ]

    def packing_defect(self,X):
        return np.array([ m + np.eye(2) for m in self.hol_around_vertices(X)]).flatten()

class EmbeddedDCEL(InterstitialDCEL):
    """
    V: set of vertices
    E: set of Edges
    F: set of Faces
    e1: starting edge 1
    e2: starting edge 2, if applicable
    """
    def __init__(self, data):
        self.e1 = data[1]
        self.e2 = data[2] if len(data) > 2 else None

        super().__init__(data[0])

class MirroredInterstitialDCEL(InterstitialDCEL):
    """DCEL of closed triangulated surface with mirror boundary supporting IC calcuations"""
    def hol_around_vertex(self,X,v):
        """Product of factors around a single vertex (possibly a mirrored)"""
        if v.is_interior:
            # This vertex is interior, so call the hol_around_vertex()
            # of the immediate superclass, InterstitialDCEL, which handles
            # interior vertices correctly
            return super().hol_around_vertex(X,v)
        else:
            # Boundary vertex.  If its CCW star is '12345', then we
            # need to take a product '12345432'

            # TODO: Handle this in a prettier, more systematic way
            # without resorting to a matrix product.  E.g. fix hol().
            M = np.eye(2,dtype='cfloat')
            elist = list(v.star())
            elist.append(elist[0].boundary_prev)
            assert elist[0] == elist[-1].boundary_next, "Bad boundary edges"
            elist += elist[-2:0:-1]
            for e in elist:
                M = M.dot(self._factor_vert_ccw(X[e.uidx]))
            return np.real(M)
        
    def hol_around_vertices(self,X):
        return [ self.hol_around_vertex(X,v) for v in self.V ]


if __name__=="__main__":
    """Find a KAT point for a one-holed torus with mirror boundary"""
    import triangulations
    import lsons
    from collections import defaultdict
    np.set_printoptions(suppress=True)

    D,t,b = triangulations.cylinder(5,5)
    t2 = t.boundary_forward(2)
    dcel.glue_boundary(D, t, b, t2)

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
        
    print('verts',len(D.V))
    print('hedges',len(D.E))
    print('faces',len(D.F))

    topo = dcel.oriented_manifold_type(D)
    for k in topo:
        print(k,topo[k])

    verts_of_valence = defaultdict(int)
    for v in D.V:
        verts_of_valence[v.valence] += 1
    for k in verts_of_valence:
        print(verts_of_valence[k],'vertices of valence',k)
        
    # Freeze and index the DCEL
    ID = MirroredInterstitialDCEL(D)

    # Initial cross ratio set
    X0 = np.ones(ID.nx) * 1.9
    
    deriv_eps=1e-9
    def fun(X):
        Yv = ID.packing_defect(X)
        A = ID.hol(chain_down,X)
        B = ID.hol(chain_right,X)
        C = A.dot(B)
        ta,tb,tab = [np.trace(m) for m in [A,B,A.dot(B)]]
        return np.append(Yv,[np.imag(ta),np.imag(tb),np.imag(tab)])

    def jac(X):
        J = np.zeros((ID.ny+3,ID.nx))
        Y0 = fun(X)
        for i in range(ID.nx):
            deltaX = np.zeros(ID.nx)
            deltaX[i] = deriv_eps
            Y1 = fun(X + deltaX)
            Yprime = (Y1 - Y0) / deriv_eps
            J[:,i] = Yprime
        return J

    print('Initial cross ratio vector:\n',X0,'\n')

    print('SEARCHING for a Fuchsian circle packing.')
    X = lsons.lsroot(fun,jac,X0,args=(),verbose=False,maxcond=1e10,maxiter=50,relax=1.0)
    print('FOUND an apparent Fuchsian circle packing.\n')

    print('Final cross ratio vector:\n',X,'\n')

    A = ID.hol(chain_down,X)
    B = ID.hol(chain_right,X)
    C = A.dot(B)
    x = np.trace(A)
    y=np.trace(B)
    z=np.trace(C)

    print('Holonomy generators:')
    print('A=',A)
    print('B=',A)
    print()

    print('(tr(A), tr(B), tr(AB)) = ({},{},{})'.format(x,y,z))
    print('tr([A,B]) = ',x*x+y*y+z*z-x*y*z-2)
