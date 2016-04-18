from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine

import config


db_cfg = config.get_config_context()['database']
s_db_cfg = config.get_config_context()['s_database']
engine = create_engine('postgresql://%s:%s@%s:%s/%s' %
                       (db_cfg['DB_USER'], s_db_cfg['DB_PASS'], db_cfg['DB_HOST'], db_cfg['DB_PORT'], db_cfg['DB_NAME']),convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    print("Initializing Database")
    import models
    Base.metadata.create_all(bind=engine)
