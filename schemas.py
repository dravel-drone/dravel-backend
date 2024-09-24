from pydantic import BaseModel
from typing import List, Optional, Union
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

# 회원가입 스키마
class Register(BaseModel):
    name: str
    id: str
    email: str
    password: str
    age: Optional[int]
    drone: Optional[str]
    image: Optional[str]
    one_liner: Optional[str]

    class Config:
        from_attributes = True

# User login 스키마
class Login(BaseModel):
    id: str
    password: str
    device_id: str

    class Config:
        from_attributes = True

class Logout(BaseModel):
    device_id: str
    uid: str

# 유저 프로필 스키마
class Profile(BaseModel):
    uid: str
    name: str
    image: Optional[str]
    post_count: int
    follower_count: int
    following_count: int
    one_liner: Optional[str]
    drone: Optional[str]
    is_following: Optional[int]

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

class Following(BaseModel):
    uid: str
    name: str
    email: str
    drone: Optional[str]
    image: Optional[str]
    one_liner: Optional[str]


# Refresh pydantic 스키마
class RefreshTokenRequest(BaseModel):
    device_id: str

class AccessTokenResponse(BaseModel):
    access_token: str
    access_token_expire: datetime

# Dronespot pydantic 스키마
class Location(BaseModel):
    lat: float
    lon: float
    address: str

class Area(BaseModel):
    id: int
    name: str

class Permit(BaseModel):
    flight: int
    camera: int

class DronespotBase(BaseModel):
    name: str
    location: Location
    comment: str
    permit: Permit

class DronespotCreate(DronespotBase):
    pass

class Dronespot(DronespotBase):
    id: int
    is_like: Optional[int] = 0
    likes_count: Optional[int] = 0
    reviews_count: Optional[int] = 0
    photo: Optional[str]
    area: List[Area]
    drone_type: Optional[int] = 0

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
class Writer(BaseModel):
    uid: str
    name: str

class Review(BaseModel):
    id: int
    writer: Optional[Writer]
    place_name: str
    permit: Permit
    drone_type: str
    date: str
    comment: str
    photo: Optional[str]
    like_count: int
    is_like: int

    class Config:
        from_attributes = True

class ReviewDronespot(Review):
    drone: str

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
    comment: Optional[str] = None
    photo_url: Optional[str] = None
    location: Location
    place_type_id: Optional[int] = None
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
class CourseCreate(BaseModel):
    name: str
    content: str
class Course(CourseBase):
    id: int
    class Config:
        from_attributes = True
class CourseDronespot(Course):
    photo_url: Optional[str]
    class Config:
        from_attributes = True

class CourseWithPlaces(Course):
    places: List[Union[Place, Dronespot]] = []

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

class Places(BaseModel):
    accommodations: List[Place]
    restaurants: List[Place]

class Whether(BaseModel):
    tmp: int
    sky: int
    pty: int

class DronespotResponse(BaseModel):
    id: int
    name: str
    whether: Optional[Whether] = None
    is_like: Optional[int] = 0
    likes_count: Optional[int] = 0
    reviews_count: Optional[int] = 0
    photo_url: Optional[str]
    comment: str
    location: Location
    area: List[Area]
    permit: Permit
    reviews: List[ReviewDronespot]
    courses: List[CourseDronespot]
    places: Places

