from typing import List
try:
    import rdflib
except ImportError:
    rdflib = None

from core.models.spatial_entities import SpatialEntity, SpatialEntityType

def import_brick(file_path: str) -> List[SpatialEntity]:
    if rdflib is None:
        raise RuntimeError("rdflib is required to import Brick graphs")

    g = rdflib.Graph()
    g.parse(file_path, format="turtle")

    # This is a very small sketch; extend with full mapping.
    entities: List[SpatialEntity] = []
    for s, p, o in g.triples((None, rdflib.RDF.type, None)):
        o_str = str(o)
        if o_str.endswith("Building"):
            ent = SpatialEntity(
                id=str(s),
                name=str(s),
                type=SpatialEntityType.BUILDING,
                brick_class=o_str,
                brick_uri=str(s),
            )
            entities.append(ent)
    return entities
