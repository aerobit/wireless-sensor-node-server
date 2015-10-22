import datetime

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, Integer, String, Float
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base

import settings

engine = sa.create_engine(settings.DATABASE, echo=settings.DATABASE_DEBUG)
Session = orm.sessionmaker(bind=engine)
BaseModel = declarative_base(bind=engine)


class Reading(BaseModel):
    __tablename__ = "readings"

    id = Column(Integer(), primary_key=True, nullable=False)
    created_at = Column(DateTime(),
                        nullable=False,
                        default=datetime.datetime.utcnow,
                        index=True)
    node_id = Column(Integer(), nullable=False)
    seq_no = Column(Integer(), nullable=False)
    reading_type = Column(String(10), nullable=False)
    reading = Column(Float(), nullable=False)
    checksum_sent = Column(Integer(), nullable=False)
    checksum_calc = Column(Integer(), nullable=False)
    
class Setpoint(BaseModel):
    __tablename__ = "setpoints"

    id = Column(Integer(), primary_key=True, nullable=False)
    created_at = Column(DateTime(),
                        nullable=False,
                        default=datetime.datetime.utcnow,
                        index=True)
    zone_id = Column(Integer(), nullable=False)
    temperature = Column(Float(), nullable=False)

class Name(BaseModel):
    __tablename__ = "names"
    id = Column(Integer(), primary_key=True, nullable=False)
    zone_id = Column(Integer(), nullable=False)
    name = Column(String(), nullable=False)

BaseModel.metadata.create_all()

