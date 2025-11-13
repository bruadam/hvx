from typing import Iterable
try:
    import rdflib
except ImportError:
    rdflib = None

from core.models.spatial_entities import SpatialEntity

def export_to_brick(entities: Iterable[SpatialEntity], out_path: str) -> None:
    if rdflib is None:
        raise RuntimeError("rdflib is required to export Brick graphs")

    g = rdflib.Graph()
    BRICK = rdflib.Namespace("https://brickschema.org/schema/Brick#")

    for e in entities:
        uri = rdflib.URIRef(e.brick_uri or f"http://example.com/{e.id}")
        cls = rdflib.URIRef(e.brick_class or BRICK.Building)
        g.add((uri, rdflib.RDF.type, cls))

    g.serialize(out_path, format="turtle")
