from pydantic import BaseModel, EmailStr

# ------------------ Item Schemas ------------------ #

class ItemBase(BaseModel):
    title: str
    description: str

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: int

    class Config:
        orm_mode = True

# ------------------ User Schemas ------------------ #

class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str

class UserLogin(UserBase):
    password: str
    repassword: str

class UserInDB(UserBase):
    id: int
    hashed_password: str

    class Config:
        orm_mode = True
