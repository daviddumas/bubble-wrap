"""Generate DCELs for some triangulated surfaces"""


import dcel as dcel

def ring(w):
    """Generate DCEL for a triangulated ring of height 1 and circumference w.

    Looks like:.. --T----------------...
                  |\  |\  |\  |\  |\
                \ | \ | \ | \ | \ | \
                 \|  \|  \|  \|  \|  \
                ..--B-----------------...
    Returns typle (D,T,B)
    D -- DCEL of the ring
    T -- a "top" half-edge
    B -- a "bottom" half edge directly below T
    """

    # We create the vertices first in a 2d array; later the indices
    # will correspond to position in the ring as follows:
    #
    # 00---01---02---03---04---05
    # |\   |\   |\   |\   |\   |
    # | \  | \  | \  | \  | \  |
    # |  \ |  \ |  \ |  \ |  \ | 
    # |   \|   \|   \|   \|   \|
    # 10---11---12---13---14---15
    

    V = [[dcel.Vertex() for i in range(w)],
         [dcel.Vertex() for i in range(w)]]

    E = set()
    F = set()

    # Top triangles
    for i in range(w):
        j = (i+1) % w
        EF,f = dcel.vertex_chain_to_face([V[1][j], V[0][j], V[0][i]])
        if i == 0:
            for e in EF:
                if e.src == V[0][1] and e.dst == V[0][0]:
                    etop = e
                    break
        E.update(EF)
        F.add(f)

    # Bottom triangles
    for i in range(w):
        j = (i+1) % w
        EF,f = dcel.vertex_chain_to_face([V[0][i], V[1][i], V[1][j]])
        if i == 0:
            for e in EF:
                if e.src == V[1][0] and e.dst == V[1][1]:
                    ebot = e
                    break
        E.update(EF)
        F.add(f)

    # TODO: inefficient to search blindly for twin pairs, when we know
    # exactly which ones are present.  Make this more efficient.
    # (Since vertex_chain_to_face doesn't expose any details about the
    # order of edges returned, it is probably best to just manually
    # create all of half-edges and store in an array like V.
    dcel.set_twins(E)

    return dcel.DCEL(V[0] + V[1], E, F), etop, ebot


def cylinder(w,h):
    """Generate DCEL for a triangulated cylinder of height h and circumference w"""
    tops = []
    bottoms = []
    D = dcel.DCEL()

    # Create h separate rings of height 1
    for i in range(h):
        RD,t,b = ring(w)
        tops.append(t)
        bottoms.append(b)
        D |= RD

    # Glue the rings top-to-bottom
    for i in range(h-1):
        dcel.glue_boundary(D, bottoms[i], tops[i + 1])

    return D,tops[0],bottoms[-1]

if __name__=="__main__":
    # Genus two test
    #
    # Surface composed from four cylinders.
    
    
    #   /-D1-\            /-D4-\
    #  /      \          /      \
    # b        a-e-D3-f-c        d
    #  \      /          \      /
    #   \-D2-/            \-D5-/

    
    D1,T1,B1 = cylinder(5,10)
    D2,T2,B2 = cylinder(5,10)

    D3,T3,B3 = cylinder(4,10)

    D4,T4,B4 = cylinder(5,10)
    D5,T5,B5 = cylinder(5,10)

    D = D1 | D2 | D3 | D4 | D5
    new_bdry_edge_12 = B1.boundary_forward(3)     
    new_bdry_edge_45 = B4.boundary_forward(3)     

    dcel.glue_boundary(D, B1, T2, new_bdry_edge_12)  # a  -> D1,D2 form pair of pants
    dcel.glue_boundary(D, T1, B2)                   # b  -> Now punctured torus

    dcel.glue_boundary(D, B4, T5, new_bdry_edge_45)  # c  -> D4,D5 form pair of pants
    dcel.glue_boundary(D, T4, B5)                   # d  -> Now punctured torus

    # Join the two punctured tori along cylinder D3
    dcel.glue_boundary(D, new_bdry_edge_12, T3)     # e
    dcel.glue_boundary(D, B3, new_bdry_edge_45)     # f

    print('verts',len(D.V))
    print('hedges',len(D.E))
    print('faces',len(D.F))

    topo = dcel.oriented_manifold_type(D)
    for k in topo:
        print(k,topo[k])
