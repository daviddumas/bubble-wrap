"""Doubly-connected edge list"""

import uuid
import numpy as np

class DCEL:
    """Doubly-connected edge list"""
    def __init__(self,V=set(),E=set(),F=set()):
        # Note: Any existing order on V,E,F will be destroyed
        self.V = set(V)
        self.E = set(E)
        self.F = set(F)

    def __or__(self,other):
        """Disjoint union"""
        return DCEL(self.V | other.V, self.E | other.E, self.F | other.F)

class ImmutableDCEL(DCEL):
    """Doubly-connected edge list"""
    def __init__(self,V,E,F):
        # Key propert: Any existing order on V,E,F preserved
        self.V = tuple(V)
        self.E = tuple(E)
        self.F = tuple(F)

    def __or__(self,other):
        raise TypeError('%s does not support disjoint union' % __class__)

class IndexedDCEL(ImmutableDCEL):
    """Indexed, immutable doubly-connected edge list, also indexing unoriented edges"""
    def __init__(self,D,set_uuid=None):
        """Assign indices to the elements of a given DCEL according to the
        following rules (NOTE: These conventions are an essential
        contract concerning the mapping between a mutable DCEL and the
        resulting indices.  They must not be changed or the ability to
        serialize DCELs to JSON files (as in the serialization module)
        will be broken):

        * Each vertex is given a new attribute "idx" which is its
          zero-based index in list(D.V); that is, if D.V is already an
          ordered collection, then the order is preserved.

        * Each edge is given a new attribute "idx" which is its
          zero-based index in list(D.E); that is, if D.E is already an
          ordered collection, then the order is preserved.

        * Each edge is given a new attribute "uidx" which is the
          number of distinct twin-equivalence classes that appear
          before it in list(D.E).  Equivalently, traversing list(D.E)
          in order, each edge is assigned a nonnegative integer uidx
          which is equal to that of its twin if the twin exists and
          has already been seen, and otherwise is the least
          nonnegative integer not yet assigned.

        * Each face is given a new attribute "idx" which is its
          zero-based index in list(D.F); that is, if D.F is already an
          ordered collection, then the order is preserved.

        """

        if set_uuid:
            self.uuid = uuid.UUID(set_uuid)
        else:
            self.uuid = uuid.uuid4()
        # Coerce core data structures to immutable types, preserving
        # order if there is one
        self.V = tuple(D.V)
        self.E = tuple(D.E)
        self.F = tuple(D.F)
        for k,v in enumerate(self.V):
            v.idx = k
        for k,f in enumerate(self.F):
            f.idx = k
        UE = []
        for k,e in enumerate(self.E):
            e.idx = k
            if e not in UE and e.twin not in UE:
                e.uidx = len(UE)
                if e.twin:
                    e.twin.uidx = len(UE)
                UE.append(e)
        self.UE = tuple(UE)

class Vertex:
    """Vertex object for use with DCEL.
    
    Attributes:
    leaving -- a HalfEdge 'e' with this vertex as e.src
    """
    def __init__(self,leaving=None):
        self.leaving = leaving

    @property
    def valence(self):
        # TODO: Make this work for boundary vertices
        return len(list(self.star()))

    @property
    def is_interior(self):
        e0 = self.leaving
        while e0.twin:
            e0 = e0.twin.next
            if e0 == self.leaving:
                return True
        return False
    
    def star(self):
        """Generator yielding all edges with this vertex as src in CCW order; WORKS ON BOUNDARY VERTICES TOO"""
        # Find clockwist-most outgoing edge (or self.leaving, if interior point)
        e0 = self.leaving
        while e0.twin:
            e0 = e0.twin.next
            if e0 == self.leaving:
                break

        # Yield edges starting with this one, proceeding counterclockwise
        e = e0
        yield e
        while e.prev.twin:
            e = e.prev.twin
            if e == e0:
                return
            yield e

    def interior_star(self):
        """Generator yielding all edges with this vertex as src in CCW order.
        WORKS ONLY ON INTERIOR VERTICES but is faster than star()."""
        # Yield edges starting with self.leaving
        e = self.leaving
        yield e
        while e.prev.twin:
            e = e.prev.twin
            if e == self.leaving:
                return
            yield e

class CoordinateVertex(Vertex):
    def __init__(self, coords=(0, 0, 0), leaving=None):
        self.coordinates = np.array(coords)  # transformed location
        self.coordinates.shape = (3, 1)

        super(CoordinateVertex, self).__init__(leaving)

class HalfEdge:
    """Oriented edge object for use with DCEL, associated with whichever
    face has this orientation as part of its oriented boundary.

    Attributes:
    src -- the vertex that this oriented edge points away from
    next
    prev
    twin

    """
    def __init__(self,src=None,next=None,prev=None,twin=None,face=None):
        self.src = src
        self.next = next
        self.prev = prev
        self.twin = twin
        self.face = face

    @property
    def dst(self):
        assert self.next, "e.next unset, so cannot compute e.dst := e.next.src"
        return self.next.src

    @property
    def is_boundary(self):
        return self.twin==None
    
    @property
    def boundary_next(self):
        """Assume this edge lies on a boundary component.  Find the next edge."""
        c = self.next
        while c.twin:
            c = c.twin.next
            if c == self:
                # We went all the way around without finding another boundary edge
                return None
        return c

    @property
    def boundary_prev(self):
        """Assume this edge lies on a boundary component.  Find the previous edge."""
        c = self.prev
        while c.twin:
            c = c.twin.prev
            if c == self:
                # We went all the way around without finding another boundary edge
                return None
        return c

    def boundary_forward(self,k):
        e = self
        for i in range(k):
            e = e.boundary_next
        return e

    def boundary_backward(self,k):
        e = self
        for i in range(k):
            e = e.boundary_prev
        return e

    @property
    def vert_ccw(self):
        return self.prev.twin

    @property
    def vert_cw(self):
        if not self.twin:
            return None
        return self.twin.next

    @property
    def tri_ccw(self):
        return self.next

    @property
    def tri_cw(self):
        return self.prev    
    
class Face:
    """Face object for use with DCEL.  Represents a face in an oriented
    2-complex, linked to the rest of the structure by recording one of
    the oriented edges of its boundary.
    """
    def __init__(self,edge=None):
        self.edge = edge

    @property
    def num_edges(self):
        n = 1
        e = self.edge.next
        while e != self.edge:
            e = e.next
            n += 1
        return n

    @property
    def num_vertices(self):
        return self.num_edges

def vertex_chain_to_face(verts):
    """Create edges and face object with a given chain of vertices as its oriented boundary; twins unset"""
    f = Face()
    E = []
    for v in verts:
        e = HalfEdge(v,face=f)
        E.append(e)
        if not v.leaving:
            v.leaving = e
    for eprev,e,enext in zip(E[-1:]+E[:-1], E, E[1:]+E[:1]):
        e.prev = eprev
        e.next = enext
    f.edge = E[0]
    return E,f

def set_twins(E):
    """Assume origin, next, prev of half edges are set, and set the twin for each half edge

    WARNING: O(N^2)"""
    for e in E:
        if e.twin == None:
            for eprime in E:
                if eprime.src == e.dst and eprime.dst == e.src:
                    e.twin = eprime
                    if not eprime.twin:
                        eprime.twin = e
                    assert eprime.twin == e, "half-edge twin() not involutive"
                    break


def coalesce_vertices(vkeep,vkill):
    """Absorb vkill into vkeep, assuming next/prev are already set correctly"""
    for e in vkill.star():
        e.src = vkeep

def glue_boundary(D,ea,eb,estop=None):
    """Glue boundary edges together, starting with ea glued to eb, moving
forward from ea and backward from eb.  If elast is reached it will be the last edge glued."""
    if estop in (ea,eb):
        return
    A = [ea]
    B = [eb]
    na = A[-1].boundary_next
    nb = B[-1].boundary_prev
    while na not in (estop,ea) and nb not in (estop,eb):
        A.append(na)
        B.append(nb)
        na = A[-1].boundary_next
        nb = B[-1].boundary_prev

    #print('Found',len(A),'vertices to glue')

    # TODO be less lazy; incorporate this into loop below, don't add each to dead_vertices twice
    dead_vertices = set()
    for cb in B:
        dead_vertices.add(cb.src)
        dead_vertices.add(cb.dst)
    
    for ca, cb in zip(A,B):
        # Coalesce the vertices
        coalesce_vertices(ca.src,cb.dst)
        # Make the edges twins
        ca.twin = cb
        cb.twin = ca
    # Possibly one final vertex left to glue
    coalesce_vertices(ca.dst,cb.src)

    # Remove unreferenced vertices
    D.V.difference_update(dead_vertices)

    # Expensive test: Make sure every edge has a source that is still in the vertex list.
    for e in D.E:
        assert e.src in D.V

def dst_including_bdry(e):
    if e.twin:
        return e.dst
    else:
        return e.boundary_next.src

def reverse_orientation(D):
    """Reverse orientation of a DCEL D representing a manifold with boundary """
    for v in D.V:
        v.leaving = v.leaving.prev
    destinations = { e:dst_including_bdry(e) for e in D.E }
    for e in D.E:
        e.next,e.prev = e.prev,e.next
        e.src = destinations[e]

def manifold_boundary_components(D):
    seen = set()
    cpnts = set()
    for e0 in D.E:
        if e0 not in seen and e0.is_boundary:
            k = 1
            seen.add(e0)
            e = e0.boundary_next
            while e != e0:
                seen.add(e)
                k = k + 1
                e = e.boundary_next
            cpnts.add( (e,k) )
    return cpnts

def oriented_manifold_type(D):
    # TODO: DON'T ASSUME CONNECTEDNESS
    topo = dict()
    BC = manifold_boundary_components(D)
    if BC:
        tot_bdry = 0
        for e,k in BC:
            tot_bdry += k
        assert (len(D.E) + tot_bdry) % 2 == 0, "Oriented edges + bdry edges not even"
        chi = len(D.V) - ((len(D.E) + tot_bdry)//2) + len(D.F)
        num_bdry = len(BC)
    else:
        assert len(D.E) % 2 == 0, "Closed surface with odd number of oriented edges."
        chi = len(D.V) - (len(D.E)//2) + len(D.F)
        assert chi % 2 == 0, "Closed oriented surface with odd Euler characteristic"
        num_bdry = 0

    topo['genus'] = 1 - (chi + num_bdry)//2
    topo['chi'] = chi
    topo['nbdry'] = num_bdry
    topo['bdry_lens'] = [ k for e,k in BC]
    return topo

MARKED_TRI_MOVES = {
    lambda x:x.tri_ccw,
    lambda x:x.tri_cw,
    lambda x:x.vert_ccw,
    lambda x:x.vert_cw,
}

def edge_chain_dfs(D,e0,moves=MARKED_TRI_MOVES):
    """Depth first search in the DCEL using basic moves, return list of paths from e0 to all accessible edges in the DCEL"""
    reached = {e0}  # edges
    interior = set() # chains
    frontier = set() # chains
    frontier.add( (e0,) )
    
    while frontier:
        new_frontier = set()
        for ch in frontier:
            e = ch[-1]
            for m in moves:
                eprime = m(e)
                if eprime and (eprime not in reached):
                    new_frontier.add( ch + (eprime,) )
                    reached.add(eprime)
        interior.update(frontier)
        frontier = new_frontier
    return interior
        
if __name__=="__main__":
    """Build a sample DCEL and report about it"""
    # Cube
    cubeverts = {}
    for x in range(2):
        for y in range(2):
            for z in range(2):
                cubeverts[(x,y,z)] = Vertex()
    ifront = [ (1,0,0), (1,1,0), (1,1,1), (1,0,1) ]
    iback = [ (0,0,0), (0,0,1), (0,1,1), (0,1,0) ]
    itop = [ (0,0,1), (1,0,1), (1,1,1), (0,1,1) ]
    ibottom = [ (1,0,0), (0,0,0), (0,1,0), (1,1,0) ]
    ileft = [ (0,0,1), (0,0,0), (1,0,0), (1,0,1) ]
    iright = [ (1,1,1), (1,1,0), (0,1,0), (0,1,1) ]

    E = set()
    F = set()
    for idx in [ ifront, iback, itop, ibottom, ileft, iright ]:
        EF, f = vertex_chain_to_face([cubeverts[i] for i in idx])
        E.update(EF)
        F.add(f)

    set_twins(E)
    D = DCEL(V=cubeverts.values(),E=E,F=F)

    print("CUBE")
    for v in D.V:
        print("Vertex with valence: ",v.valence)

    for f in D.F:
        print("Face with size: ",f.num_edges)

    for e in D.E:
        assert e.twin.twin == e, "half-edge twin() not involutive"

    ID = IndexedDCEL(D)
    for f in D.F:
        print('Face %d adjacent to faces:' % f.idx,end='')
        e = f.edge
        while True:
            print('%d ' % e.twin.face.idx,end='')
            e = e.next
            if e == f.edge:
                break
        print()
    
    print(len(ID.E),'oriented edges')
    print(len(ID.UE),'unoriented edges')
    print(oriented_manifold_type(D))
