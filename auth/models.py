from datetime import datetime
from email.policy import default

import sqlalchemy as _sql
from sqlalchemy.orm import relationship
import passlib.hash as _hash

from auth.config import Base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, TEXT, Table


class Maintainer(Base):
    __tablename__ = "maintainers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, ForeignKey("users.email", ondelete="CASCADE"))
    service_list = Column(String, ForeignKey("services.service_name", ondelete="CASCADE"))

    def __repr__(self):
        return f"<{self.email} - {self.service_list}>"



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    date_created = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    service = relationship("Service", secondary='maintainers', backref='maintainer')
    # permission = _orm.relationship("Post", back_populates="owner")

    def verify_password(self, password: str):
        return _hash.bcrypt.verify(password, self.hashed_password)

    def __repr__(self):
        return f'<User: {self.email}>'



class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    # email = Column(String, ForeignKey("users.email"))
    service_name = Column(String, unique=True, index=True)
    label_type = Column(String, index=True)
    label_lang = Column(String, index=True)
    # label = Column(String)

    def __repr__(self):
        return f'<Service Name: {self.service_name} | {self.label_lang}>'
    # permission = _orm.relationship("User", back_populates="owner")
    # owner = relationship("User", back_populates="service_list")

