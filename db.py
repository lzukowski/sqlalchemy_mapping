from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base


metadata = MetaData()
Base = declarative_base(metadata=metadata)
memory_engine = create_engine('sqlite:///')
