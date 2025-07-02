from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class SignUpSchema(BaseModel):
    email: str
    first_name: str 
    last_name: str 
    phone_number: str 
    password: str 
    repassword: str
    accountType: str


class UserUpdateSchema(BaseModel):
    id: int
    first_name: str 
    last_name: str 
    phone_number: str 
    address: str 
    dob: str 
    facebook: str 
    github: str 
    linkedin: str 
    medium: str 
    youtube: str 
    twitter: str 
    instagram: str 
    personal_website: str 