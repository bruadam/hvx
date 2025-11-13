MERGE (p:SpatialEntity {id:'portfolio_1'})
  SET p.name = 'Default Portfolio', p.type = 'portfolio';

MERGE (b:SpatialEntity {id:'building_1'})
  SET b.name = 'Example Building', b.type = 'building';

MERGE (p)-[:HAS_CHILD]->(b);
