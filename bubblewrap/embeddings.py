import dcel as dcel


def placeholder_gen(i, j):
    return dcel.Vertex()


def embedded_ring(nw, h=0, coord_gen=placeholder_gen):
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


    V = [[coord_gen(h, i) for i in range(nw)],
         [coord_gen(h+1, i) for i in range(nw)]]

    E = set()
    F = set()

    # Top triangles
    for i in range(nw):
        j = (i + 1) % nw
        EF, f = dcel.vertex_chain_to_face([V[1][j], V[0][j], V[0][i]])
        if i == 0:
            for e in EF:
                if e.src == V[0][1] and e.dst == V[0][0]:
                    etop = e
                    break
        E.update(EF)
        F.add(f)

    # Bottom triangles
    for i in range(nw):
        j = (i + 1) % nw
        EF, f = dcel.vertex_chain_to_face([V[0][i], V[1][i], V[1][j]])
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


def embedded_cylinder(nw, nh, coord_gen):
    """Generate DCEL for a triangulated cylinder of height h and circumference w"""
    tops = []
    bottoms = []
    D = dcel.DCEL()

    # Create h separate rings of height 1
    for i in range(nh):
        RD,t,b = embedded_ring(nw, i, coord_gen=coord_gen)
        tops.append(t)
        bottoms.append(b)
        D |= RD

    # Glue the rings top-to-bottom
    for i in range(nh-1):
        dcel.glue_boundary(D, bottoms[i], tops[i + 1])

    return D,tops[0],bottoms[-1]


def embedded_torus(nw, nh, stop=None, coord_gen=None):
    assert nw > 2 and nh > 2

    # Build dcel
    mD, t1, b1 = embedded_cylinder(nw, nh, coord_gen=coord_gen)

    if stop is None:
        dcel.glue_boundary(mD, b1, t1)
    else:
        t1stop = t1.boundary_forward(stop)
        dcel.glue_boundary(mD, t1, b1, t1stop)

    # return:
    # DCEL (mD, t1: starting edge)
    return mD, t1
