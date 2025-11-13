"""Namespace manager for Brick Schema URIs."""

from rdflib import Namespace


class BrickNamespaceManager:
    """
    Manages namespaces for Brick Schema and related ontologies.

    Provides easy access to Brick classes, predicates, and custom namespaces.
    """

    # Standard Brick Schema namespace
    BRICK = Namespace("https://brickschema.org/schema/Brick#")

    # Building topology namespace (part of Brick)
    TOPOLOGY = Namespace("https://brickschema.org/schema/Brick/topology#")

    # Related ontologies
    RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
    RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
    OWL = Namespace("http://www.w3.org/2002/07/owl#")
    SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
    QUDT = Namespace("http://qudt.org/schema/qudt/")
    UNIT = Namespace("http://qudt.org/vocab/unit/")

    # Custom namespace for your building instances
    BUILDING = Namespace("https://ieq-analytics.example.org/building/")
    SENSOR = Namespace("https://ieq-analytics.example.org/sensor/")
    POINT = Namespace("https://ieq-analytics.example.org/point/")

    @classmethod
    def bind_to_graph(cls, graph):
        """
        Bind all namespaces to an RDF graph.

        Args:
            graph: rdflib.Graph instance
        """
        graph.bind("brick", cls.BRICK)
        graph.bind("topology", cls.TOPOLOGY)
        graph.bind("rdf", cls.RDF)
        graph.bind("rdfs", cls.RDFS)
        graph.bind("owl", cls.OWL)
        graph.bind("skos", cls.SKOS)
        graph.bind("qudt", cls.QUDT)
        graph.bind("unit", cls.UNIT)
        graph.bind("bldg", cls.BUILDING)
        graph.bind("sensor", cls.SENSOR)
        graph.bind("point", cls.POINT)
