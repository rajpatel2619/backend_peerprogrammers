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
