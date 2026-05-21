from pydantic import BaseModel


class Student(BaseModel):
    roll: str
    name: str
    attendance: int
