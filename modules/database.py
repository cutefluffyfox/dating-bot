import logging

import sqlalchemy
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec

SqlAlchemyBase = dec.declarative_base()

__factory = None


def global_init(conn_str: str) -> None:
    """Connect and initialize database"""
    global __factory

    if __factory:
        return

    logging.info(f"Connecting to database")

    engine = sqlalchemy.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    import modules.models

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    """Creates session with orm.sessionmaker"""
    global __factory
    return __factory()
