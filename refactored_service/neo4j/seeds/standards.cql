MERGE (s:Standard {id: 'en16798-1'})
  SET s.name = 'EN 16798-1 Indoor Environmental Input Parameters';

MERGE (s2:Standard {id: 'tail'})
  SET s2.name = 'TAIL Indoor Climate Standard';

MERGE (s3:Standard {id: 'br18'})
  SET s3.name = 'BR18 Danish Building Regulations';
