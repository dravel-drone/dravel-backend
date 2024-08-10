from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# 약관(Term) pydantic 스키마
class TermBase(BaseModel):
    title: str
    content: str
    require: int
class TermCreate(TermBase):
    pass
class Term(TermBase):
    id: int
    class Config:
        from_attributes = True


# UserTermAgree pydantic 스키마
class UserTermAgreeBase(BaseModel):
    term_id: int
    user_uid: str
    created_at: datetime
class UserTermAgreeCreate(UserTermAgreeBase):
    pass
class UserTermAgree(UserTermAgreeBase):
    term: Term
    class Config:
        from_attributes = True


# User pydantic 스키마
class UserBase(BaseModel):
    name: str
    id: str
    email: str
    is_admin: int
    password: str
    age: Optional[int]
    drone: Optional[str]
    image: Optional[str]
    one_liner: Optional[str]
class UserCreate(UserBase):
    pass
class User(UserBase):
    uid: str
    class Config:
        from_attributes = True


# Follow pydantic 스키마
class FollowBase(BaseModel):
    follower_uid: str
    following_uid: str
class FollowCreate(FollowBase):
    pass
class Follow(FollowBase):
    class Config:
        from_attributes = True


# Dronespot pydantic 스키마
class DronespotBase(BaseModel):
    name: str
    lat: float
    lon: float
    address: str
    photo_url: Optional[str]
    comment: str
    permit_flight: int
    permit_camera: int
class DronespotCreate(DronespotBase):
    pass
class Dronespot(DronespotBase):
    id: int
    class Config:
        from_attributes = True


# UserDronespotLike pydantic 스키마
class UserDronespotLikeBase(BaseModel):
    user_uid: str
    dronespot_id: int
class UserDronespotLikeCreate(UserDronespotLikeBase):
    pass
class UserDronespotLike(UserDronespotLikeBase):
    class Config:
        from_attributes = True


# Review pydantic 스키마
class ReviewBase(BaseModel):
    writer_uid: str
    dronespot_id: int
    drone_type: str
    permit_flight: int
    permit_camera: int
    drone: str
    flight_date: datetime
    comment: Optional[str]
    photo_url: Optional[str]
class ReviewCreate(ReviewBase):
    pass
class Review(ReviewBase):
    id: int
    class Config:
        from_attributes = True


# UserReviewLike pydantic 스키마
class UserReviewLikeBase(BaseModel):
    user_uid: str
    review_id: int
class UserReviewLikeCreate(UserReviewLikeBase):
    pass
class UserReviewLike(UserReviewLikeBase):
    class Config:
        from_attributes = True


# Place pydantic 스키마
class PlaceBase(BaseModel):
    name: str
    comment: Optional[str]
    photo_url: Optional[str]
    type: int
    lat: float
    lon: float
    address: str
    place_type_id: int
class PlaceCreate(PlaceBase):
    pass
class Place(PlaceBase):
    id: int
    class Config:
        from_attributes = True


# PlaceType pydantic 스키마
class PlaceTypeBase(BaseModel):
    name: str
class PlaceTypeCreate(PlaceTypeBase):
    pass
class PlaceType(PlaceTypeBase):
    id: int
    class Config:
        from_attributes = True


# Course pydantic 스키마
class CourseBase(BaseModel):
    name: str
    content: str
    distance: int
    duration: int
class CourseCreate(CourseBase):
    pass
class Course(CourseBase):
    id: int
    class Config:
        from_attributes = True


# CourseVisit pydantic 스키마
class CourseVisitBase(BaseModel):
    course_id: int
    dronespot_id: Optional[int]
    place_id: Optional[int]
class CourseVisitCreate(CourseVisitBase):
    pass
class CourseVisit(CourseVisitBase):
    class Config:
        from_attributes = True