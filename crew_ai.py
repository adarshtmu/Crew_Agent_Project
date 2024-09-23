import logging
import io
import PyPDF2
from langchain_huggingface import HuggingFaceEndpoint
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import Tool
from langchain.prompts import PromptTemplate
from langchain.agents import AgentType, initialize_agent
class BloodTestCrew:
    def __init__(self, huggingface_api_key):
        self.huggingface_api_key = huggingface_api_key
        self.search_tool = DuckDuckGoSearchRun()
        self.llm = self.initialize_llm()

    def initialize_llm(self):
        try:
            llm = HuggingFaceEndpoint(
                repo_id="microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext",
                task="text-generation",
                huggingfacehub_api_token=self.huggingface_api_key
            )
            return llm
        except Exception as e:
            logging.error(f"Failed to initialize LLM: {e}")
            raise


    def analyze_blood_test(self, pdf_content, email):
        try:
            pdf_text = self.extract_text_from_pdf(pdf_content)
            logging.info(f"Extracted PDF Text: {pdf_text[:100]}")  # Log the first 100 chars

            # Define tools for the agent
            tools = [
                Tool(
                    name="DuckDuckGo Search",
                    func=self.search_articles,
                    description="Use DuckDuckGo to search for health articles"
                )
            ]

            # Initialize the agent
            agent = initialize_agent(
                tools,
                self.llm,
                agent=AgentType.REACT_DOCSTORE,
                verbose=True
            )

            # Prepare the prompt for analysis
            prompt = f"Analyze this blood test report: {pdf_text}"
            logging.info(f"Prompt for Agent: {prompt}")

            # Invoke the agent
            result = agent.run(prompt)
            logging.info(f"Agent Result: {result}")
            return result
        except Exception as e:
            logging.error(f"Failed to analyze blood test: {e}")
            return f"Failed to analyze blood test: {str(e)}"

    def extract_text_from_pdf(self, pdf_content):
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            text = ""
            for page in pdf_reader.pages:
                extracted_text = page.extract_text()
                text += extracted_text if extracted_text else ""  # Handle None values
            return text
        except Exception as e:
            logging.error(f"Failed to extract text from PDF: {e}")
            raise

    def search_articles(self, query):
        return self.search_tool.run(query)

# Make sure to configure logging before running your application
logging.basicConfig(level=logging.INFO)