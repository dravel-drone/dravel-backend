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

    user_term_agree = relationship('UserTermAgree', back_populates='term')

class UserTermAgree(Base):
    __tablename__ = 'user_term_agree'

    term_id = Column(INTEGER(unsigned=True), ForeignKey('term.id'), primary_key=True, nullable=False)
    user_id = Column(String(128), ForeignKey('user.uid'), primary_key=True, nullable=False)
    created_at = Column(DATETIME, default=datetime.utcnow, nullable=False)

    term = relationship('Term', back_populates='user_term_agree')
    user = relationship('User', back_populates='user_term_agree')


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

    user_term_agree = relationship('UserTermAgree', back_populates='user')
    followers = relationship('Follow', foreign_keys='Follow.follower_uid', back_populates='follower')
    followings = relationship('Follow', foreign_keys='Follow.following_uid', back_populates='following')
    user_dronespot_likes = relationship('UserDronespotLike', back_populates='user')
    reviews = relationship('Review', back_populates='user')
    user_review_likes = relationship('UserReviewLike', back_populates='user')

class Follow(Base):
    __tablename__ = 'following_follower'

    follower_uid = Column(String(128), ForeignKey('user.uid'), primary_key=True ,nullable=False)
    following_uid = Column(String(128), ForeignKey('user.uid'), primary_key=True, nullable=False)

    follower = relationship('User', foreign_keys=[follower_uid], back_populates='followings')
    following = relationship('User', foreign_keys=[following_uid], back_populates='followers')

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

    user_dronespot_likes = relationship('UserDronespotLike', back_populates='dronespot')
    reviews = relationship('Review', back_populates='dronespot')
    course_visits = relationship('CourseVisit', back_populates='dronespot')

class UserDronespotLike(Base):
    __tablename__ = 'user_dronespot_like'

    user_uid = Column(String(128), ForeignKey('user.uid'), primary_key=True, nullable=True)
    dronespot_id = Column(INTEGER(unsigned=True), ForeignKey('dronespot.id'), primary_key=True, nullable=False)

    user = relationship('User', back_populates='user_dronespot_likes')
    dronespot = relationship('Dronespot', back_populates='user_dronespot_likes')

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

    user = relationship('User', back_populates='reviews')
    dronespot = relationship('Dronespot', back_populates='reviews')
    user_review_likes = relationship('UserReviewLike', back_populates='review')

class UserReviewLike(Base):
    __tablename__ = 'user_review_like'

    user_uid = Column(String(128), ForeignKey('user.uid'), primary_key=True, nullable=True)
    review_id = Column(INTEGER(unsigned=True), ForeignKey('review.id'), primary_key=True, nullable=False)

    user = relationship('User', back_populates='user_review_likes')
    review = relationship('Review', back_populates='user_review_likes')

class Place(Base):
    __tablename__ = 'place'

    id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False, autoincrement=True)
    name = Column(String(120), nullable=False)
    comment = Column(String(200), nullable=True)
    photo_url = Column(Text, nullable=True)
    type = Column(INTEGER, nullable=False)
    lat = Column(DOUBLE, nullable=False)
    lon = Column(DOUBLE, nullable=False)
    address = Column(String(200), nullable=False)
    place_type_id = Column(INTEGER(unsigned=True), ForeignKey('place_type.id'), nullable=False)

    place_type = relationship('PlaceType', back_populates='places')
    course_visits = relationship('CourseVisit', back_populates='place')

class PlaceType(Base):
    __tablename__ = 'place_type'

    id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False, autoincrement=True)
    name = Column(String(45), nullable=False)

    places = relationship('Place', back_populates='place_type')


class Course(Base):
    __tablename__ = 'course'

    id = Column(INTEGER(unsigned=True), primary_key=True, nullable=False, autoincrement=True)
    name = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    distance = Column(INTEGER, nullable=False)
    duration = Column(INTEGER, nullable=False)

    course_visits = relationship('CourseVisit', back_populates='course')

class CourseVisit(Base):
    __tablename__ = 'course_visit'

    course_id = Column(INTEGER(unsigned=True), ForeignKey('course.id'), primary_key=True, nullable=False)
    dronespot_id = Column(INTEGER(unsigned=True), ForeignKey('dronespot.id'), primary_key=True, nullable=True)
    place_id = Column(INTEGER(unsigned=True), ForeignKey('place.id'), primary_key=True, nullable=True)

    course = relationship('Course', back_populates='course_visits')
    dronespot = relationship('Dronespot', back_populates='course_visits')
    place = relationship('Place', back_populates='course_visits')