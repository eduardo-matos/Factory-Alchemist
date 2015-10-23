import random
import string
from datetime import date, timedelta, datetime
from sqlalchemy import Integer, String, SmallInteger, BigInteger, Boolean, Table, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base


BaseModel = None


def make(session, model_, **kwargs):
    if isinstance(model_, Table):
        table = model_
        model_ = type('', (declarative_base(),), {'__table__': table})

    record = model_(**kwargs)

    for column in _non_nullable_columns(model_):
        if column.foreign_keys:
            for foreign_key in column.foreign_keys:
                fk_value = make(session, _get_class_by_tablename(foreign_key.column.table.name))
                setattr(record, foreign_key.parent.name, getattr(fk_value, foreign_key.column.name))
        else:
            setattr(record, column.name, generate_value(column.type))

    session.add(record)
    session.flush()
    return record


def generate_value(type_):
    value_generator = TYPE_VALUE_GENERATOR_MAPPER.get(type_.__class__)

    if value_generator:
        return value_generator(type_)


def _generate_int(type_=None, max=2147483647):
    return random.randint(0, max)


def _generate_smallint(type_=None):
    return _generate_int(type_, 1)


def _generate_bigint(type_=None):
    return _generate_int(type_, 9223372036854775807)


def _generate_str(type_=None):
    length = type_.length if type_.length else 50
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(length))


def _generate_bool(type_=None):
    return random.choice((True, False))


def _generate_date(type_=None):
    return date(random.randint(1950, 2050), random.randint(1, 12), random.randint(1, 28))


def _generate_datetime(type_=None):
    return datetime(random.randint(1950, 2050), random.randint(1, 12), random.randint(1, 28),
                    random.randint(0, 23), random.randint(0, 59), random.randint(0, 59))


TYPE_VALUE_GENERATOR_MAPPER = {
    SmallInteger: _generate_smallint,
    Integer: _generate_int,
    BigInteger: _generate_bigint,
    String: _generate_str,
    Boolean: _generate_bool,
    Date: _generate_date,
    DateTime: _generate_datetime,
}


def _non_nullable_columns(model_):
    return {column[1] for column in model_.__table__.columns.items()
            if not column[1].nullable and not column[1].primary_key}


def _get_class_by_tablename(tablename):
  if not BaseModel:
      raise Exception('BaseModel must be defined')

  for c in BaseModel._decl_class_registry.values():
    if hasattr(c, '__tablename__') and c.__tablename__ == tablename:
      return c
