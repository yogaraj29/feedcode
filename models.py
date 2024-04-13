from sqlalchemy.schema import Column
from sqlalchemy.types import String, Integer, Date, BLOB,DATETIME
from sqlalchemy import Column, Integer, String, Date, BLOB, ForeignKey,JSON
from sqlalchemy.orm import relationship
from database import base,db_engine

class Question(base):
    __tablename__ = "questions"
    
    question_id = Column(Integer, primary_key=True, index=True)
    question_text = Column(String(100))
    topic = Column(String(100))
    constraint = Column(String(100))
    c_id = Column(String(100))
    
    # Define relationship with TestCases


class TestCase(base):
    __tablename__ = "test_cases"
    
    test_case_id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    question_id = Column(Integer)
    test_input = Column(String(100))
    expected_output = Column(String(100))



class signup(base):
    __tablename__='signup'

    id=Column(Integer,index=True,autoincrement=True, primary_key=True,nullable=False)
    Username=Column(String(255),index=True,nullable=False)
    Email=Column(String(255),index=True,nullable=False)
    Password=Column(String(255),index=True,nullable=False)
    Status=Column(String(255),index=True,nullable=False)
    Created_by=Column(String(255),index=True,nullable=False)
    Created_at=Column(String(255),index=True,nullable=False)


class Contest(base):
    __tablename__="contest"

    id=Column(Integer,primary_key=True,index=True)
    contestName=Column(String(30))
    startDate=Column(String(30))
    startTime=Column(String(30))
    endDate=Column(String(30))
    endtime=Column(String(30))
    organisationType=Column(String(30))
    organisationName=Column(String(30))
    visibility=Column(String(30))
    username=Column(String(30))

class Leaderboard(base):
    __tablename__='leaderboard'

    id=Column(Integer,index=True,autoincrement=True, primary_key=True,nullable=False)
    Username=Column(String(255),nullable=False)
    c_id = Column(String(100))
    question_id=Column(JSON)
    score = Column(Integer)

class Profile(base):
    __tablename__='profile'

    id=Column(Integer,index=True,autoincrement=True, primary_key=True,nullable=False)
    fname=Column(String(255))
    lname = Column(String(100))
    mobile=Column(String(255))
    email = Column(String(100))
    country=Column(String(255))
    state = Column(String(100))
    



        
base.metadata.create_all(bind=db_engine)
    