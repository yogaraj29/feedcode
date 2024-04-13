from http.client import HTTPException
import io
import os
import subprocess
import sys
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from jose import  jwt,JWTError
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi import FastAPI,Request,Depends,Form,File,UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse,JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy import desc
from sqlalchemy.orm import Session
from fastapi import FastAPI, HTTPException, Request
from datetime import datetime, timedelta
from configs.base_config import BaseConfig
import models
from database import SessionLocal
from fastapi import Query
from utils import create_access_token


app = FastAPI()

# CORS (Cross-Origin Resource Sharing) middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def get_db():
    db = None
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()



app.add_middleware(SessionMiddleware, secret_key="e8Lj5R$Zv@n8!sWm3P#q")
templates = Jinja2Templates(directory='templates')
app.mount("/templates",StaticFiles(directory="templates"), name="templates")

def get_db():
    db = None
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
        
@app.get('/index', response_class=HTMLResponse) 
def get_form(request:Request, question: str = Query(None),db:Session = Depends(get_db)):
    try:
        token = request.session["sessid"]
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM] )
        
        user_nme: str= payload.get("user_name")

        if user_nme is None:

            raise HTTPException(status_code=401,detail="Unauthorized")   
        else:

            results = db.query(models.Question).filter(models.Question.question_id==question).first()
            new_user1=db.query(models.TestCase).filter(models.TestCase.question_id==question).first()
            print(results.question_id)
            idd=results.c_id
            contests = db.query(models.Contest).filter(models.Contest.id==idd).first()
            current_datetime = datetime.now()
            return templates.TemplateResponse("index.html",context={"request":request,"data":results,"data1":new_user1, 'contests': contests, 'current_datetime': current_datetime, 'datetime': datetime,"user_name":user_nme})
    except :
        raise HTTPException(status_code=401,detail="Unauthorized")




class CodeRequest(BaseModel):
    code: str
    language: str  # Add userInput field
    question_id: int
    username: str



class CodeRequest1(BaseModel):
    code: str
    language: str  # Add userInput field
    userInput: str
    username:str

@app.post("/runcode")
async def run_code(code_request: CodeRequest,db: Session = Depends(get_db)):
    flag=0
    if code_request.language == "python":
        try:
            # Fetch test cases for the given question_id from the database
            test_cases = db.query(models.TestCase).filter(models.TestCase.question_id == code_request.question_id).all()

            # Loop through test cases and execute the code with each test input
            results = []
            for test_case in test_cases:
                test_input = test_case.test_input
                expected_output = test_case.expected_output

                # Capture the output of the executed code with test input
                sys.stdin = io.StringIO(test_input)  # Redirect stdin to the test input
                sys.stdout = io.StringIO()  # Redirect stdout to capture output
                exec(code_request.code, globals(), locals())  # Pass globals() and locals()
                output = sys.stdout.getvalue()

                # Reset stdout and stdin
                sys.stdout = sys.__stdout__
                sys.stdin = sys.__stdin__

                # Check if output matches expected output
                if output.strip() == expected_output.strip():
                    results.append(True)
                else:
                    results.append(False)

            # Check if all test cases passed
            if all(results):
                flag=1
                # return {"success": "Your code executed successfully"}
            else:
                failed_count = len(test_cases) - sum(results)
                return {"success": False, "message": f"{failed_count} test cases failed"}

        except Exception as e:
            return {"success": False, "message": f"Execution Error: {str(e)}"}

    elif code_request.language == "c":
        try:
            failed_count = 0
            # Fetch test cases for the given question_id from the database
            test_cases = db.query(models.TestCase).filter(models.TestCase.question_id == code_request.question_id).all()

            for test_case in test_cases:
                test_input = test_case.test_input
                expected_output = test_case.expected_output

                # Write the C code to a temporary file
                with open("temp.c", "w") as f:
                    f.write(code_request.code)

                # Get the absolute path to the temporary file
                c_file_path = os.path.abspath("temp.c")

                # Compile the C code with gcc
                compile_command = ["gcc", "-o", "temp", c_file_path]
                compile_process = subprocess.run(compile_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Check for compilation errors
                if compile_process.returncode != 0:
                    return {"success": False, "message": f"Compilation Error: {compile_process.stderr.decode().strip()}"}

                # Execute the compiled program and get output
                execution_command = ["./temp"]
                execution_process = subprocess.run(execution_command, input=test_input.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Check if there was an error during execution
                if execution_process.returncode != 0:
                    return {"success": False, "message": f"Execution Error: {execution_process.stderr.decode().strip()}"}

                # Compare the output with the expected output
                output_str = execution_process.stdout.decode().strip()
                if output_str != expected_output:
                    failed_count += 1

                # Clean up temporary files
                os.remove("temp.c")
                if os.path.exists("temp"):
                    os.remove("temp")

            if failed_count == 0:
                flag=1
                # return {"success": "Your code executed successfully"}
            else:
                return {"success": False, "message": f"{failed_count} test cases failed"}

        except Exception as e:
            return {"success": False, "message": f"Execution Error: {str(e)}"}


    elif code_request.language == "cpp":
        try:
            failed_count = 0
            # Fetch test cases for the given question_id from the database
            test_cases = db.query(models.TestCase).filter(models.TestCase.question_id == code_request.question_id).all()

            for test_case in test_cases:
                test_input = test_case.test_input
                expected_output = test_case.expected_output

                # Write the C++ code to a temporary file
                with open("temp.cpp", "w") as f:
                    f.write(code_request.code)

                # Compile the C++ code
                compile_command = ["g++", "-o", "temp", "temp.cpp"]
                compile_process = subprocess.run(compile_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Check for compilation errors
                if compile_process.returncode != 0:
                    return {"success": False, "message": f"Compilation Error: {compile_process.stderr.decode().strip()}"}

                # Execute the compiled program and get output
                execution_command = ["./temp"]
                execution_process = subprocess.run(execution_command, input=test_input.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Check if there was an error during execution
                if execution_process.returncode != 0:
                    return {"success": False, "message": f"Execution Error: {execution_process.stderr.decode().strip()}"}

                # Compare the output with the expected output
                output_str = execution_process.stdout.decode().strip()
                if output_str != expected_output:
                    failed_count += 1

                # Clean up temporary files
                os.remove("temp.cpp")
                if os.path.exists("temp"):
                    os.remove("temp")

            if failed_count == 0:
                flag=1
                # return {"success": "Your code executed successfully"}
            else:
                return {"success": False, "message": f"{failed_count} test cases failed"}

        except Exception as e:
            return {"success": False, "message": f"Execution Error: {str(e)}"}

    elif code_request.language == "java":
        try:
            failed_count = 0
            # Fetch test cases for the given question_id from the database
            test_cases = db.query(models.TestCase).filter(models.TestCase.question_id == code_request.question_id).all()

            for test_case in test_cases:
                test_input = test_case.test_input
                expected_output = test_case.expected_output

                # Write the Java code to a temporary file
                with open("Main.java", "w") as f:
                    f.write(code_request.code)

                # Compile the Java code
                compile_command = ["javac", "Main.java"]
                compile_process = subprocess.run(compile_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Check for compilation errors
                if compile_process.returncode != 0:
                    return {"success": False, "message": f"Compilation Error: {compile_process.stderr.decode().strip()}"}

                # Execute the compiled program and get output
                execution_command = ["java", "Main"]
                execution_process = subprocess.run(execution_command, input=test_input.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Check if there was an error during execution
                if execution_process.returncode != 0:
                    return {"success": False, "message": f"Execution Error: {execution_process.stderr.decode().strip()}"}

                # Compare the output with the expected output
                output_str = execution_process.stdout.decode().strip()
                if output_str != expected_output:
                    failed_count += 1

            # Clean up temporary files
            os.remove("Main.java")
            if os.path.exists("Main.class"):
                os.remove("Main.class")

            if failed_count == 0:
                flag=1
                # return {"success":"Your code executed successfully"}
            else:
                return {"success": False, "message": f"{failed_count} test cases failed"}

        except Exception as e:
            return {"success": False, "message": f"Execution Error: {str(e)}"}
        
    
    else:
        return {"success": False, "message": "Unsupported language"}
    
    if flag == 1:
        results = db.query(models.Question).filter(models.Question.question_id == code_request.question_id).first()
        if results:
            cc_id = results.c_id
            check = db.query(models.Leaderboard).filter(models.Leaderboard.Username==code_request.username,models.Leaderboard.c_id == cc_id).first()
            if check:
                if not check.question_id or code_request.question_id not in json.loads(check.question_id):
                    print("Before appending:")
                    print("check.question_id:", check.question_id)
                    
                    # Update the score
                    check.score += 10
                    
                    # Deserialize JSON data from the column
                    if check.question_id:
                        question_ids = json.loads(check.question_id)
                    else:
                        question_ids = []
                    
                    # Append the new question_id if it doesn't already exist
                    if code_request.question_id not in question_ids:
                        question_ids.append(code_request.question_id)
                        
                        # Serialize the updated JSON data
                        check.question_id = json.dumps(question_ids)
                        
                        print("After appending:")
                        print("check.question_id:", check.question_id)
                        
                        db.commit()
                        
                    return {"success": "Your code executed successfully"}
            return {"success": "Your code executed successfully"}
            
        else:
            return {"error": "Question not found"}




@app.post("/custom")
async def run_code(code_request: CodeRequest1,request: Request):

    if code_request.language == "python":
        try:
            # Capture the output of the executed code with user input
            sys.stdin = io.StringIO(code_request.userInput)  # Redirect stdin to the user input
            sys.stdout = io.StringIO()  # Redirect stdout to capture output
            exec(code_request.code, globals(), locals())
            # Get the output and reset stdout and stdin
            output = sys.stdout.getvalue()
            sys.stdout = sys.__stdout__
            sys.stdin = sys.__stdin__
            return {"success": True, "message": "Code executed successfully", "output": output}
        except Exception as e:
            return {"success": False, "message": f"Execution Error: {str(e)}"}
    elif code_request.language == "c":
        try:
            # Write the C code to a temporary file
            with open("temp.c", "w") as f:
                f.write(code_request.code)

            # Compile the C code
            compile_command = ["gcc", "-o", "temp", "temp.c"]
            compile_process = subprocess.run(compile_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Check for compilation errors
            if compile_process.returncode != 0:
                return {"success": False, "message": f"Compilation Error: {compile_process.stderr.decode().strip()}"}

            # Execute the compiled program with custom input
            execution_command = ["./temp"]
            execution_process = subprocess.run(execution_command, input=code_request.userInput.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            return {"success": True, "output": execution_process.stdout.decode().strip()}

        except Exception as e:
            return {"success": False, "message": f"Execution Error: {str(e)}"}
        finally:
            # Clean up temporary files
            os.remove("temp.c")
            if os.path.exists("temp"):
                os.remove("temp")
    elif code_request.language == "cpp":
        try:
            # Write the C++ code to a temporary file
            with open("temp.cpp", "w") as f:
                f.write(code_request.code)

            # Compile the C++ code
            compile_command = ["g++", "-o", "temp", "temp.cpp"]
            compile_process = subprocess.run(compile_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Check for compilation errors
            if compile_process.returncode != 0:
                return {"success": False, "message": f"Compilation Error: {compile_process.stderr.decode().strip()}"}

            # Execute the compiled program with custom input
            execution_command = ["./temp"]
            execution_process = subprocess.run(execution_command, input=code_request.userInput.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            return {"success": True, "output": execution_process.stdout.decode().strip()}

        except Exception as e:
            return {"success": False, "message": f"Execution Error: {str(e)}"}
        finally:
            # Clean up temporary files
            os.remove("temp.cpp")
            if os.path.exists("temp"):
                os.remove("temp")

    elif code_request.language == "java":
        try:
            # Write the Java code to a temporary file
            with open("Main.java", "w") as f:
                f.write(code_request.code)

            # Compile the Java code
            compile_command = ["javac", "Main.java"]
            compile_process = subprocess.run(compile_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Check for compilation errors
            if compile_process.returncode != 0:
                return {"success": False, "message": f"Compilation Error: {compile_process.stderr.decode().strip()}"}

            # Execute the compiled program with custom input
            execution_command = ["java", "Main"]
            execution_process = subprocess.run(execution_command, input=code_request.userInput.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            return {"success": True, "output": execution_process.stdout.decode().strip()}

        except Exception as e:
            return {"success": False, "message": f"Execution Error: {str(e)}"}
        finally:
            # Clean up temporary files
            os.remove("Main.java")
            if os.path.exists("Main.class"):
                os.remove("Main.class")
    else:
        return {"success": False, "message": "Unsupported language"}

    

@app.get("/login")
def login_page(request: Request):   
    return templates.TemplateResponse('login.html', context={'request': request}) 

@app.get("/signup_get")
def login_page(request: Request):   
    return templates.TemplateResponse('signup.html', context={'request': request}) 


@app.post("/logcheck")
def logcheck(request:Request,db:Session=Depends(get_db),login_user:str=Form(...),login_password:str=Form(...)):
    #print(login_email,login_password)
    find=db.query(models.signup).filter(models.signup.Username==login_user,models.signup.Password==login_password).first()
    if find is None:
        error= "Invalid Creditional"   
        json_compatible_item_data = jsonable_encoder(error)
        return JSONResponse(content=json_compatible_item_data)
    else:
        access_token_expires = timedelta(minutes=BaseConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"user_name": find.Username},expires_delta=access_token_expires)
        sessid = access_token
        request.session["sessid"] = sessid
        error = "checked"
        error= "Done"   
        json_compatible_item_data = jsonable_encoder(error)
        return JSONResponse(content=json_compatible_item_data)



@app.post("/signup")
def signup(request:Request,db:Session=Depends(get_db),signup_username:str=Form(...),signup_email:str=Form(...),signup_password:str=Form(...)):
    find=db.query(models.signup).filter(models.signup.Username ==signup_username,models.signup.Email==signup_email).first()
    if find is not None:
        error= "This user name and email is already exist"   
        json_compatible_item_data = jsonable_encoder(error)
        return JSONResponse(content=json_compatible_item_data)
    else:
        data=models.signup(Username=signup_username,Email=signup_email,Password=signup_password,Status="ACTIVE",Created_by="admin",Created_at="08/02/2024")
        db.add(data)
        db.commit()
        data1=models.Profile(email=signup_username)
        db.add(data1)
        db.commit()
        access_token_expires = timedelta(minutes=BaseConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"user_name": signup_username},expires_delta=access_token_expires)
        sessid = access_token
        request.session["sessid"] = sessid
        error= "Done"
        json_compatible_item_data = jsonable_encoder(error)
        return JSONResponse(content=json_compatible_item_data)
    


@app.get("/list", response_class=HTMLResponse)
def get_contests(request: Request, db: Session = Depends(get_db)):
    try:
        token = request.session["sessid"]
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM] )
        user_nme: str= payload.get("user_name")

        if user_nme is None:

            raise HTTPException(status_code=401,detail="Unauthorized")   
        else:
            contests = db.query(models.Contest).all()
            current_datetime = datetime.now()
            return templates.TemplateResponse('listcontest.html', context={'request': request, 'contests': contests, 'current_datetime': current_datetime, 'datetime': datetime})
    except :
        raise HTTPException(status_code=401,detail="Unauthorized")


@app.get("/q_list", response_class=HTMLResponse)
def get_content(request: Request, contest_name: int = Query(None), db: Session = Depends(get_db)):
    try:
        token = request.session["sessid"]
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM] )
        user_nme: str= payload.get("user_name")

        if user_nme is None:

            raise HTTPException(status_code=401,detail="Unauthorized")   
        else:
            check = db.query(models.Leaderboard).filter(models.Leaderboard.Username == user_nme, models.Leaderboard.c_id == contest_name).first()
            print(check)
            print(user_nme)
            if not check:
                data=models.Leaderboard(Username=user_nme,score=0,c_id=contest_name)
                db.add(data)
                db.commit()
            contests = db.query(models.Contest).filter(models.Contest.id==contest_name).first()
            current_datetime = datetime.now()
            new_user=db.query(models.Question).filter(models.Question.c_id==contest_name).all()
            return templates.TemplateResponse('qlist.html', context={'request': request,"cont":new_user, 'contests': contests, 'current_datetime': current_datetime, 'datetime': datetime}) 
    
    except :
        raise HTTPException(status_code=401,detail="Unauthorized")



@app.get("/home")
def login_page(request: Request,db:Session=Depends(get_db)):
    try:
        token = request.session["sessid"]
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM] )
        user_nme: str= payload.get("user_name")

        if user_nme is None:

            raise HTTPException(status_code=401,detail="Unauthorized")   
        else:
            return templates.TemplateResponse('home.html', context={'request': request}) 
    except :
        raise HTTPException(status_code=401,detail="Unauthorized")



    


@app.get("/contest")
def login_page(request: Request):
    try:
        token = request.session["sessid"]
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM] )
        user_nme: str= payload.get("user_name")

        if user_nme is None:

            raise HTTPException(status_code=401,detail="Unauthorized")   
        else:   
            return templates.TemplateResponse('contest.html', context={'request': request})
    except :
        raise HTTPException(status_code=401,detail="Unauthorized")

 


@app.post("/create")
def create_data(request:Request,db:Session=Depends(get_db),contestName:str=Form(...),startDate:str=Form(...),startTime:str=Form(...),endDate:str=Form(...),endtime:str=Form(...),organisationType:str=Form(...),organisationName:str=Form(...),visibility:str=Form(...)):

    try:
        token = request.session["sessid"]
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM] )
        user_nme: str= payload.get("user_name")

        if user_nme is None:

            raise HTTPException(status_code=401,detail="Unauthorized")   
        else:
            body=models.Contest(contestName=contestName,startDate=startDate,startTime=startTime,endDate=endDate,endtime=endtime,organisationType=organisationType,organisationName=organisationName,visibility=visibility,username=user_nme)
            db.add(body)
            db.commit()
            last_id = db.query(models.Contest).order_by(desc(models.Contest.id)).first().id

            return RedirectResponse(f"/question?last_id={last_id}", status_code=303)
    except :
        raise HTTPException(status_code=401,detail="Unauthorized")



@app.get("/question")
def addquestion(request: Request, last_id: int = Query(...), db: Session = Depends(get_db)):
    try:
        token = request.session["sessid"]
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM] )
        user_nme: str= payload.get("user_name")

        if user_nme is None:

            raise HTTPException(status_code=401,detail="Unauthorized")   
        else:
            new_question = db.query(models.Question).filter(models.Question.c_id == last_id).all()
            return templates.TemplateResponse('question.html', context={'request': request, "question": new_question,"lastid":last_id})
    except :
        raise HTTPException(status_code=401,detail="Unauthorized")



@app.post("/add_question")
def add_question(request:Request,db:Session=Depends(get_db),description:str=Form(...),sip:str=Form(...),sop:str=Form(...),topic:str=Form(...),constraints:str=Form(...),contestid:str=Form(...)):
    try:
        token = request.session["sessid"]
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM] )
        user_nme: str= payload.get("user_name")

        if user_nme is None:

            raise HTTPException(status_code=401,detail="Unauthorized")   
        else:
            sip=list(sip.split(','))
            sop=list(sop.split(','))
            data=models.Question(question_text=description,topic=topic,constraint=constraints,c_id=contestid)
            db.add(data)
            db.commit()
            qid=db.query(models.Question).all()
            qqid=len(qid)
            for i,j in zip(sip,sop):
                dat1=models.TestCase(question_id=qqid,test_input=i,expected_output=j)
                db.add(dat1)
                db.commit()
            error= "Done"   
            json_compatible_item_data = jsonable_encoder(error)
            return JSONResponse(content=json_compatible_item_data)
    except :
        raise HTTPException(status_code=401,detail="Unauthorized")


            


@app.get("/profile")
def login_page(request: Request,db:Session=Depends(get_db)):
    try:
        token = request.session["sessid"]
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM] )
        user_nme: str= payload.get("user_name")

        if user_nme is None:

            raise HTTPException(status_code=401,detail="Unauthorized")   
        else:
            results=db.query(models.Profile).first()
            return templates.TemplateResponse('profile.html', context={'request': request,'results':results,"mail":user_nme}) 
    except :
        raise HTTPException(status_code=401,detail="Unauthorized")




@app.post("/updateprofile")
def create_data(request:Request,db:Session=Depends(get_db),fname:str=Form(...),lname:str=Form(...),mobile:str=Form(...),country:str=Form(...),state:str=Form(...)):
    try:
        token = request.session["sessid"]
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM] )
        user_nme: str= payload.get("user_name")

        if user_nme is None:

            raise HTTPException(status_code=401,detail="Unauthorized")   
        else:
            db.query(models.Profile).filter(models.Profile.id==1).update({"fname":fname,"lname":lname,"mobile":mobile,"country":country,"state":state})
            db.commit()
            return RedirectResponse("/home", status_code=303)  
    except :
        raise HTTPException(status_code=401,detail="Unauthorized")


            


@app.get("/leaderboard", response_class=HTMLResponse)
def get_content(request: Request, contest_id: int = Query(None), db: Session = Depends(get_db)):
    try:
        token = request.session["sessid"]
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM] )
        user_nme: str= payload.get("user_name")

        if user_nme is None:
            raise HTTPException(status_code=401,detail="Unauthorized")   
        else:
            user=db.query(models.Leaderboard).filter(models.Leaderboard.Username==user_nme,models.Leaderboard.c_id==contest_id).first()
            status=0
            if user is None:
                status=1
            else:
                status=0  
            print(status)
            results = db.query(models.Leaderboard).filter(models.Leaderboard.Username!=user_nme,models.Leaderboard.c_id==contest_id).order_by(desc(models.Leaderboard.score)).all()
            return templates.TemplateResponse('leaderboard.html', context={'request': request,"user":user,"results":results,"status":status}) 
    except:
        raise HTTPException(status_code=401,detail="Unauthorized")


