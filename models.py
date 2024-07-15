from sqlalchemy import Column, String, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.mysql import INTEGER, LONGTEXT, DATE, DATETIME, TINYINT, TEXT
from sqlalchemy.orm import relationship
from datetime import datetime
from database.mariadb_session import Base

# DB model 추가
class Term(Base):
    __tablename__ = 'term'

    id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False, autoincrement=True)
    title = Column(String(125), nullable=False)
    content = Column(LONGTEXT, nullable=False)
    require = Column(TINYINT(1), nullable=False)

class UserTermAgree(Base):
    __tablename__ = 'user_term_agree'

    term_id = Column(INTEGER(unsigned=True), ForeignKey('term.id'), primary_key=True, nullable=False)
    user_id = Column(String(128), ForeignKey('user.uid'), primary_key=True, nullable=False)
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

class Follow(Base):
    __tablename__ = 'follow'

    follower_uid = Column(String(128), ForeignKey('user.uid'), primary_key=True ,nullable=False)
    following_uid = Column(String(128), ForeignKey('user.uid'), primary_key=True, nullable=False)

class Dronespot(Base):
    __tablename__ ='dronespot'

    id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False, autoincrement=True)
    name = Column(String(120), nullable=False)
    lat = Column(DOUBLE, nullable=False)
    lon = Column(DOUBLE, nullable=False)
    address = Column(String(200), nullable=False)
    photo_url = Column(Text, nullable=True)
    comment = Column(String(200), nullable=False)
    permit_flight = Column(TINYINT(1), nullable=False)
    permit_camera = Column(TINYINT(1), nullable=False)

class UserDronespotLike(Base):
    __tablename__ = 'user_dronespot_like'

    user_uid = Column(String(128), ForeignKey('user.uid'), primary_key=True, nullable=True)
    dronespot_id = Column(INTEGER(unsigned=True), ForeignKey('dronespot.id'), primary_key=True, nullable=False)

class Review(Base):
    __tablename__ = 'review'

    id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False, autoincrement=True)
    writer_uid = Column(String(128), ForeignKey('user.uid'), nullable=False)
    dronespot_id = Column(INTEGER(unsigned=True), ForeignKey('dronespot.id'), nullable=False)
    drone_type = Column(String(45), nullable=False)
    permit_flight = Column(TINYINT(1), nullable=False)
    permit_camera = Column(TINYINT(1), nullable=False)
    drone = Column(String(45), nullable=False)
    flight_date = Column(DateTime, nullable=False)
    comment = Column(Text, nullable=True)
    photo_url = Column(Text, nullable=True)

class UserReviewLike(Base):
    __tablename__ = 'user_review_like'

    user_uid = Column(String(128), ForeignKey('user.uid'), primary_key=True, nullable=True)
    review_id = Column(INTEGER(unsigned=True), ForeignKey('review.id'), primary_key=True, nullable=False)

class Place(Base):
    __tablename__ = 'place'

    id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False, autoincrement=True)
    name = Column(String(120), nullable=False)
    comment = Column(String(200), nullable=True)
    photo_url = Column(Text, nullable=True)
    type = Column(Integer, nullable=False)
    lat = Column(DOUBLE, nullable=False)
    lon = Column(DOUBLE, nullable=False)
    address = Column(String(200), nullable=False)
    place_type_id = Column(INTEGER(unsigned=True), ForeignKey('place_type.id'), nullable=False)

class PlaceType(Base):
    __tablename__ = 'place_type'

    id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False, autoincrement=True)
    name = Column(String(45), nullable=False)

class Course(Base):
    __tablename__ = 'course'

    id = Column(Integer(unsigned=True), primary_key=True, nullable=False, autoincrement=True)
    name = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    distance = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)

class CourseVisit(Base):
    __tablename__ = 'course_visit'

    course_id = Column(Integer(unsigned=True), ForeignKey('course.id'), primary_key=True, nullable=False)
    dronespot_id = Column(Integer(unsigned=True), ForeignKey('dronespot.id'), primary_key=True, nullable=True)
    place_id = Column(Integer(unsigned=True), ForeignKey('place.id'), primary_key=True, nullable=True)