import os
from dotenv import load_dotenv
load_dotenv()

os.environ["OPENAI_API_BASE"] = os.getenv("API_BASE")
os.environ["OPENAI_MODEL_NAME"] = os.getenv("MODEL")
os.environ["OPENAI_API_KEY"] = os.getenv("GROQ_API_KEY") # paste your api key here

from crewai import Crew
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from planner import planner,plan
from writer import writer,write
from editor import editor,edit
from researcher import researcher, research
from scrapper import scrape_data, save_data

crew = Crew(
    agents=[researcher,planner,writer,editor],
    tasks=[research,plan,write,edit],
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

    inputs = request_body["inputs"]
    links = inputs['links']

    raw_data_collection = []
    for link in links:
        raw_data = scrape_data(link)
        raw_data_collection.append(raw_data)

    inputs['content'] = raw_data_collection

    del inputs['links']
    
    result = crew.kickoff(inputs=inputs)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    save_data(str(result),timestamp,"blog",output_folder="generated")
    
    response = {
        "content" : str(result),
        "publicationDate" : timestamp
    }
    return JSONResponse(content=response, status_code=201)

# Get route
@app.get("/")
def home():
    return {"hello":"world"}