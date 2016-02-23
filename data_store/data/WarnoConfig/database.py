from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

engine = create_engine('postgresql://warno:warno@192.168.50.100:5432/warno')
Base = declarative_base()
class Yarp(Base):
    __tablename__ = 'yarp'

    id = Column(Integer, primary_key = True)
    name = Column(String)
    fullname = Column(String)
    password = Column(String)

def create_all(self):
    Base.metadata.create_all(engine)
    print "MEGACREATE!!!"

class Site(Base):
    __tablename__ = 'sites'

    id = Column("site_id", Integer, primary_key = True)
    name_short = Column(String(8), nullable=False)
    name_long = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    facility = Column(String(8))
    mobile = Column(Boolean)
    location_name = Column(String)

class User(Base):
    __tablename__ = "users"
    id = Column("user_id", Integer, primary_key = True)
    name = Column(String, nullable = False)
    email = Column("e-mail", String)
    location = Column(String)
    position = Column(String)
    password = Column(String)
    authorizations = Column(String)

class EventCode(Base):
    __tablename__ = "event_codes"

    event_code = Column(Integer, primary_key = True)
    description = Column(String, nullable = False)

class Instrument(Base):
    __tablename__  = "instruments"

    id = Column("instrument_id", Integer, primary_key = True)
    site_id = Column(Integer, ForeignKey('sites.site_id'))
    name_short = Column(String(8))
    name_long = Column(String)
    type = Column(String)
    vendor = Column(String)
    description = Column(String)
    frequency_band = Column(String(2))
    site = relationship(Site)

class InstrumentLog(Base):
    __tablename__ = "instrument_logs"

    id = Column("log_number", primary_key = True)
    time = Column(DateTime, nullable = False)
    instrument_id = Column(Integer, ForeignKey('instruments.instrument_id'))
    contents = Column(String)
    author_id = Column(Integer, ForeignKey('users.user_id'))
    status = Column(Integer)
    supporting_images = Column(String)
    instrument = relationship(Instrument)
    author = relationship(User)

class TableReference(Base):
    __tablename__ = "table_references"

    instrument_id = Column(Integer, ForeignKey('instruments.instrument_id'), primary_key = True)
    referenced_tables = Column(postgresql.ARRAY(String))
    instrument = relationship(Instrument)

class PulseCapture(Base):
    __tablename__ = "pulse_captures"

    pulse_id = Column(Integer, primary_key = True)
    instrument_id = Column(Integer, ForeignKey('instruments.instrument_id'), nullable = False)
    time = Column(DateTime, nullable = False)
    data = Column(postgresql.ARRAY(Float))
    instrument = relationship(Instrument)

class EventsWithText(Base):
    __tablename__ = "events_with_text"

    event_id = Column(Integer, primary_key = True)
    instrument_id = Column(Integer, ForeignKey('instruments.instrument_id'), nullable = False)
    event_code_id = Column("event_code", Integer, ForeignKey('event_codes.event_code'), nullable = False)
    time = Column(DateTime, nullable = False)
    text = Column(String)
    instrument = relationship(Instrument)
    event_code = relationship(EventCode)

class EventsWithValue(Base):
    __tablename__ = "events_with_value"

    event_id = Column(Integer, primary_key = True)
    instrument_id = Column(Integer, ForeignKey('instruments.instrument_id'), nullable = False)
    event_code_id = Column("event_code", Integer, ForeignKey('event_codes.event_code'), nullable = False)
    time = Column(DateTime, nullable = False)
    value = Column(Float)
    instrument = relationship(Instrument)
    event_code = relationship(EventCode)