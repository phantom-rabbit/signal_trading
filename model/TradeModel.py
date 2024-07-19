from datetime import datetime

import pytz
from sqlalchemy import Integer, Column, DateTime, String, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import JSON

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

beijing_tz = pytz.timezone('Asia/Shanghai')
def beijing_now():
    return datetime.now(beijing_tz)

class TradeRecord(Base):
    __tablename__ = 'TradeRecord'
    st_id = Column(Integer, nullable=False)
    group_id = Column(String(200))
    trade_id = Column(String(200), nullable=False)
    client_order_id = Column(String(200), nullable=False)
    symbol = Column(String(200), nullable=False)

    create_at = Column(DateTime, default=beijing_now, onupdate=beijing_now)
    updated_at = Column(DateTime, default=beijing_now, onupdate=beijing_now)
    timestamp = Column(String(20), nullable=False)

    exec_type = Column(String(20), nullable=False)
    price = Column(String(200), default='0')
    status = Column(String(20), nullable=False)
    side = Column(String(20), nullable=False)
    size = Column(String(200), default='0')
    executed_price = Column(String(200), default='0')
    executed_size = Column(String(200), default='0')
    cost = Column(String(200), default='0')
    fee = Column(JSON)

    __table_args__ = (
        PrimaryKeyConstraint('st_id', 'trade_id', name='trade_record_pk'),
    )

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Strategy(Base):
    __tablename__ = 'Strategy'
    st_id = Column(String(200), nullable=False, primary_key=True)
    st_group_id = Column(String(200), default='0')
    params = Column(JSON)
    init_cash = Column(String(200), default='0')
    commission = Column(String(200), default='0')
    slip_perc = Column(String(200), default='0')
    final_asset = Column(String(200), default='0')
    final_position = Column(String(200), default='0')
    final_cash = Column(String(200), default='0')
    earnings = Column(String(200), default='0')
    earnings_rate = Column(String(200), default='0')

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
