"""JSON-based serialization of circle packing projective structures"""

# Conventions for filenames used to store circle packings in the
# format supported by this module:

# Extension "CPJ" = Circle Packing, JSON
# Extension "CPZ" = Circle Packing, JSON, gzipped

import uuid
import json
import numpy as np
import base64
import cpps.dcel as dcel
import datetime
import gzip
import os
from collections import OrderedDict, Mapping

def gen_metadata(extra=None):
    """Header metadata for cpj files"""
    ts = datetime.datetime.utcnow().isoformat() + 'Z'
    m = { 'schema': 'cpj',
          'schema_version': '0.0',
          'timestamp': ts }
    if extra:
        m.update(extra)
    return m

# In these functions, "so" represents "seralization object"; that is,
# an object ready for the json module to dump to a string.

def verts_so(V):
    """vertex is stored as a 0-based index of its leaving edge"""
    return [ v.leaving.idx for v in V ]

def edge_so(e):
    return { 'src': e.src.idx,
             'next': e.next.idx,
             'prev': e.prev.idx,
             'twin': e.twin.idx if e.twin else None,
             'face': e.face.idx }

def edges_so(E):
    return [ edge_so(e) for e in E ]

def faces_so(F):
    """face is stored as a 0-based index of one of its (half-)edges"""
    return [ f.edge.idx for f in F ]

def idcel_so(D):
    """Create the serialization object for a DECL"""
    so = OrderedDict()
    so['uuid'] = str(D.uuid)
    so['vertices'] = verts_so(D.V)
    so['edges'] = edges_so(D.E)
    so['faces'] = faces_so(D.F)
    return so   

# Based on NumpyEncoder by tlausch, 2014
# http://stackoverflow.com/questions/3488934/simplejson-and-numpy-array
class CPPSEncoder(json.JSONEncoder):
    def default(self, obj):
        """If input object is an ndarray it will be converted into a dict 
        holding dtype, shape and the data, base64 encoded.

        If input object is an edge, vertex, or face object, it will be 
        converted to a 0-based index (its "idx" attribute).
        """
        if isinstance(obj, np.ndarray):
            if obj.flags['C_CONTIGUOUS']:
                obj_data = obj.data
            else:
                cont_obj = np.ascontiguousarray(obj)
                assert(cont_obj.flags['C_CONTIGUOUS'])
                obj_data = cont_obj.data
            # base64 data is always a subset of ascii, so decoding in next line is safe
            data_b64 = base64.b64encode(obj_data).decode('ascii')
            return dict(__ndarray__=data_b64,
                        dtype=str(obj.dtype),
                        shape=obj.shape)

        if isinstance(obj,dcel.HalfEdge):
            # Right now we only support serialization of chains of edges
            return obj.idx

        return json.JSONEncoder.default(self, obj)

# Based on NumpyEncoder by tlausch, 2014
# http://stackoverflow.com/questions/3488934/simplejson-and-numpy-array
def json_numpy_obj_hook(dct):
    """Decodes a previously encoded numpy ndarray with proper shape and dtype.

    :param dct: (dict) json encoded ndarray
    :return: (ndarray) if input was an encoded ndarray
    """
    if isinstance(dct, dict) and '__ndarray__' in dct:
        data = base64.b64decode(dct['__ndarray__'])
        return np.frombuffer(data, dct['dtype']).reshape(dct['shape'])
    return dct
    
def serialization_object(D,edge_lists=None,packings=None,meta=None):
    so = OrderedDict()
    so['metadata'] = gen_metadata(meta)
    so['dcel'] = idcel_so(D)
    so['edge_lists'] = edge_lists
    so['packings'] = packings
    return so
 
def stores(D,edge_lists=None,packings=None,meta=None):
    """Write JSON (CPJ) representation of DCEL to a string.  Optionally,
    edge lists and circle packing cross ratio vectors may also be
    stored.

    """
    return json.dumps(serialization_object(D,edge_lists=edge_lists,packings=packings,meta=meta),cls=CPPSEncoder)
    
def storefp(fp,D,edge_lists=None,packings=None,meta=None):
    """Write JSON (CPJ) representation of DCEL to a file-like object.
    Optionally, edge lists and circle packing cross ratio vectors may
    also be stored.

    """
    return json.dump(serialization_object(D,edge_lists=edge_lists,packings=packings,meta=meta),fp,cls=CPPSEncoder)

def storefn(fn,D,edge_lists=None,packings=None,meta=None):
    """Write JSON (CPJ) representation of DCEL to a file specified by
    name.  Optionally, edge lists and circle packing cross ratio
    vectors may also be stored.

    """
    with open(fn,'rt',encoding='utf-8') as fp:
        return json.dump(serialization_object(D,edge_lists=edge_lists,packings=packings,meta=meta),fp,cls=CPPSEncoder)

def zstorefn(fn,D,edge_lists=None,packings=None,meta=None,force_compression=False,clobber=False):
    """Write JSON (CPJ or compressed CPZ) representation of DCEL to a file
    specified by name.  Optionally, edge lists and circle packing
    cross ratio vectors may also be stored.  By default compression is
    applied only if the file extension matches CPZ case-insensitively.

    """
    fn_base, fn_ext = os.path.splitext(fn)
    if clobber:
        mode = 'wt'
    else:
        mode = 'xt'

    if force_compression or fn_ext.lower() == '.cpz':
        with gzip.open(fn,mode,encoding='utf-8') as fp:
            return json.dump(serialization_object(D,edge_lists=edge_lists,packings=packings,meta=meta),fp,cls=CPPSEncoder)
    else:
        with open(fn,mode,encoding='utf-8') as fp:
            return json.dump(serialization_object(D,edge_lists=edge_lists,packings=packings,meta=meta),fp,cls=CPPSEncoder)        

def zloadfn(fn,force_decompression=False,cls=dcel.IndexedDCEL):
    """Load DCEL and packings from a file by name, transparently decompressing if necessary"""

    fn_base, fn_ext = os.path.splitext(fn)
    if force_decompression or fn_ext.lower() == '.cpz':
        with gzip.open(fn,'rt',encoding='utf-8') as infile:
            so = json.load(infile,object_hook=json_numpy_obj_hook)
    else:
        with open(fn,'rt',encoding='utf-8') as infile:
            so = json.load(infile,object_hook=json_numpy_obj_hook)
    return deserialize(so,cls=cls)

def loadfn(fn,cls=dcel.IndexedDCEL):
    """Load DCEL and packings from a file by name"""
    with open(fn,'rt',encoding='utf-8') as infile:
        so = json.load(infile,object_hook=json_numpy_obj_hook)
    return deserialize(so,cls=cls)

def loadfp(fp,cls=dcel.IndexedDCEL):
    """Load DCEL and packings from a file-like object"""
    so = json.load(fp,object_hook=json_numpy_obj_hook)
    return deserialize(so,cls=cls)

def loads(s,cls=dcel.IndexedDCEL):
    """Load DCEL and packings from a string"""
    so = json.loads(s,object_hook=json_numpy_obj_hook)
    return deserialize(so,cls=cls)

def list_deref(L,indices):
    return [ L[i] for i in indices ]

def deserialize(so,cls=dcel.IndexedDCEL,dcel_ref=None):
    """Take a serialization object (as produced by dump()) and convert to
    an IndexedDCEL (or cls, if given) and collections of pointers to
    it.

    Returns: metadata, dcel, edge_lists, packings

    """
    dso = so['dcel']
#    for es in dso['edges']:
#        print('edgenext:',es['next'])
    E = [ dcel.HalfEdge() for _ in dso['edges'] ]
    V = [ dcel.Vertex(leaving=E[vs]) for vs in dso['vertices'] ]
    F = [ dcel.Face(edge=E[fs]) for fs in dso['faces'] ]
    for e,es in zip(E,dso['edges']):
        if es['twin'] != None:
            e.twin = E[es['twin']]
        e.next = E[es['next']]
        e.prev = E[es['prev']]
        e.src = V[es['src']]
        e.face = F[es['face']]

    # Assemble
    D0 = dcel.ImmutableDCEL(V,E,F)
    # Index, if applicable
    D = cls(D0,set_uuid=dso['uuid'])

    if 'edge_lists' not in so or so['edge_lists'] == None:
        edge_lists = None
    else:
        es = so['edge_lists']
        if isinstance(es,Mapping):
            # edge_lists is a dict-like
            edge_lists = { k:list_deref(D.E,v) for k,v in es.items() }
        else:
            # edge_lists is a list-like
            edge_lists = [ list_deref(D.E,v) for v in es ]

    if 'packings' not in so:
        packings = None
    else:        
        packings = so['packings']

    return so['metadata'], D, edge_lists, packings
