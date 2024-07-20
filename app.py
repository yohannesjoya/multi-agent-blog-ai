from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
import os
from datetime import datetime

os.environ["OPENAI_API_BASE"] = "https://api.groq.com/openai/v1"
os.environ["OPENAI_MODEL_NAME"] = "llama3-8b-8192"
os.environ["OPENAI_API_KEY"] = "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" # paste your api key here


from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from planner import planner,plan
from writer import writer,write
from editor import editor,edit

crew = Crew(
    agents=[planner,writer,editor],
    tasks=[plan,write,edit],
    verbose=2
)

app = FastAPI()
# Setup cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Post route
@app.post("/api/v1/generate")
def summarizePdf(request_body:dict):
    # scraped_data  = request_body["raw_data"]
    inputs = request_body["inputs"]
    result = crew.kickoff(inputs=inputs)
    now = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
    response = {
        "content" : str(result),
        "date" : now
    }
    return JSONResponse(content=response, status_code=201)

# Get route
@app.get("/")
def home():
    return {"hello":"world"}


    # inputs = {"topic":"detail study of React19, the new features of latest react 19.",
    #       "links" : ["https://react.dev/blog/2024/04/25/react-19"]
    #       }
    # filename : str = f"{now}.md"
    # with open(filename, 'w') as file:
    #     file.write(str(result))