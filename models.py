from sqlalchemy import Column, String, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.mysql import INTEGER, LONGTEXT, DATE, DATETIME, TINYINT, TEXT
from sqlalchemy.orm import relationship
from datetime import datetime
from database.mariadb_session import Base

# DB model 추가
class Term(Base):
    __tablename__ = 'term'

    id = Column(INTEGER, nullable=False)
    title = Column(String(125), primary_key=True, nullable=False)
    content = Column(LONGTEXT, nullable=False)
    require = Column(TINYINT(1), nullable=False)

class UserTermAgree(Base):
    __tablename__ = 'user_term_agree'

    term_id = Column(INTEGER(unsigned=True), ForeignKey('term.id'), nullable=False)
    user_id = Column(String(128), ForeignKey('user.uid'), nullable=False)
    created_at = Column(DATETIME, nullable=False)

class User(Base):
    __tablename__ = 'user'

    uid = Column(String(128), primary_key=True, nullable=False)
    name = Column(String(45), nullable=False)
    id = Column(String(20), nullable=False)
    email = Column(String(255), nullable=False)
    is_admin = Column(TINYINT(1), nullable=False)
    age = Column(INTEGER(unsigned=True), nullable=True)
    drone = Column(String(45), nullable=True)
    image = Column(TEXT, nullable=True)
    one_liner = Column(String(100), nullable=True)
