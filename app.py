import os
import logging
import pickle
import base64
import io
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import EmailStr
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from langchain.prompts import PromptTemplate
from langchain.agents import AgentType, initialize_agent
from langchain.tools import Tool
from langchain_huggingface import HuggingFaceEndpoint
from langchain.tools import DuckDuckGoSearchRun
import PyPDF2

load_dotenv()

app = FastAPI()

# Configuration
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
APP_API_KEY = os.getenv("APP_API_KEY")
REDIRECT_URI = "http://127.0.0.1:8000/google/callback"
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BloodTestCrew:
    def __init__(self, huggingface_api_key):
        self.huggingface_api_key = huggingface_api_key
        self.search_tool = DuckDuckGoSearchRun()
        self.llm = self.initialize_llm()

    def initialize_llm(self):
        try:
            llm = HuggingFaceEndpoint(
                repo_id="gpt2",  # Changed to a text generation model
                task="text-generation",
                huggingfacehub_api_token=self.huggingface_api_key
            )
            return llm
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise

    def analyze_blood_test(self, pdf_content, email):
        try:
            pdf_text = self.extract_text_from_pdf(pdf_content)
            logger.info(f"Extracted PDF Text: {pdf_text[:100]}")  # Log the first 100 chars

            tools = [
                Tool(
                    name="DuckDuckGo Search",
                    func=self.search_articles,
                    description="Use DuckDuckGo to search for health articles"
                )
            ]

            agent = initialize_agent(
                tools,
                self.llm,
                agent=AgentType.REACT_DOCSTORE,
                verbose=True
            )

            prompt = f"Analyze this blood test report: {pdf_text}"
            logger.info(f"Prompt for Agent: {prompt}")

            result = agent.run(prompt)
            logger.info(f"Agent Result: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to analyze blood test: {e}")
            return f"Failed to analyze blood test: {str(e)}"

    def extract_text_from_pdf(self, pdf_content):
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            text = ""
            for page in pdf_reader.pages:
                extracted_text = page.extract_text()
                text += extracted_text if extracted_text else ""
            return text
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise

    def search_articles(self, query):
        return self.search_tool.run(query)

crew = BloodTestCrew(HUGGINGFACE_API_KEY)

# API key header for authentication
api_key_header = APIKeyHeader(name="X-API-Key")

# Dependency to validate API key
def get_api_key(api_key: str = Depends(api_key_header)):
    if api_key == APP_API_KEY:
        return api_key
    raise HTTPException(status_code=401, detail="Invalid API Key")

# Serve the index.html file from the root directory
@app.get("/", include_in_schema=False)
async def serve_html():
    return FileResponse("index.html")

# Endpoint to analyze blood test reports
@app.post("/analyze_blood_test/")
async def analyze_blood_test(
        file: UploadFile = File(...),
        email: EmailStr = Form(...),
        api_key: str = Depends(get_api_key)
):
    try:
        content = await file.read()
        result = crew.analyze_blood_test(content, email)
        await send_email(email, "Your Blood Test Analysis", result)
        return {"message": "Analysis complete. Results sent to your email."}
    except Exception as e:
        logger.error(f"Failed to analyze blood test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze blood test: {str(e)}")

# Function to send email with the analysis result using Gmail API and OAuth 2.0
async def send_email(recipient, subject, body):
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = Flow.from_client_secrets_file(
                'credentials.json',
                scopes=SCOPES,
                redirect_uri=REDIRECT_URI
            )
            auth_url, _ = flow.authorization_url(prompt='consent')
            logger.info(f"Please visit this URL to authorize the application: {auth_url}")
            code = input("Enter the authorization code: ")
            flow.fetch_token(code=code)
            creds = flow.credentials

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    message = {
        'raw': base64.urlsafe_b64encode(f'To: {recipient}\nSubject: {subject}\n\n{body}'.encode()).decode()
    }

    try:
        service.users().messages().send(userId='me', body=message).execute()
        logger.info(f"Email sent successfully to {recipient}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

# OAuth 2.0 Authorization Endpoint
@app.get("/authorize/")
async def authorize():
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    authorization_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    return RedirectResponse(url=authorization_url)

# Google Callback Endpoint
@app.get("/google/callback")
async def google_callback(code: str):
    logger.info(f"Received callback with code: {code}")
    try:
        flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials

        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)

        return JSONResponse(content={"message": "Authorization successful. You can close this window."})
    except Exception as e:
        logger.error(f"Error in google_callback: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
