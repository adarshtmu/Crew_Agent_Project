import streamlit as st
import os
import tempfile
from PyPDF2 import PdfReader
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def send_email(recipient, subject, body):
    message = MIMEMultipart()
    message["From"] = SMTP_USERNAME
    message["To"] = recipient
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(message)



def create_agents():
    blood_test_analyzer = Agent(
        role="Blood Test Analyzer",
        goal="Analyze blood test reports and extract key information",
        backstory="Expert in interpreting medical test results",
        allow_delegation=False
    )

    web_researcher = Agent(
        role="Web Researcher",
        goal="Find relevant health articles based on blood test results",
        backstory="Skilled at finding and summarizing medical information online",
        allow_delegation=False
    )

    health_advisor = Agent(
        role="Health Advisor",
        goal="Provide personalized health recommendations",
        backstory="Experienced in creating tailored health plans based on medical data",
        allow_delegation=False
    )

    return blood_test_analyzer, web_researcher, health_advisor

def create_agents():
    blood_test_analyzer = Agent(
        role="Blood Test Analyzer",
        goal="Analyze blood test reports and extract key information",
        backstory="Expert in interpreting medical test results",
        allow_delegation=False
    )

    web_researcher = Agent(
        role="Web Researcher",
        goal="Find relevant health articles based on blood test results",
        backstory="Skilled at finding and summarizing medical information online",
        allow_delegation=False
    )

    health_advisor = Agent(
        role="Health Advisor",
        goal="Provide personalized health recommendations",
        backstory="Experienced in creating tailored health plans based on medical data",
        allow_delegation=False
    )

    return blood_test_analyzer, web_researcher, health_advisor

def create_tasks(blood_test_report):
    task1 = Task(
        description=f"Analyze the following blood test report and extract key information: {blood_test_report}",
        agent=blood_test_analyzer
    )

    task2 = Task(
        description="Search for relevant health articles based on the blood test analysis",
        agent=web_researcher
    )

    task3 = Task(
        description="Create personalized health recommendations based on the blood test analysis and found articles",
        agent=health_advisor
    )

    return [task1, task2, task3]

def main():
    st.title("Blood Test Report Analyzer")

    uploaded_file = st.file_uploader("Upload your blood test report (PDF)", type="pdf")
    email = st.text_input("Enter your email address")
    api_key = st.text_input("Enter your OpenAI API key", type="password")

    if st.button("Analyze Report") and uploaded_file and email and api_key:
        os.environ["OPENAI_API_KEY"] = api_key

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        blood_test_report = extract_text_from_pdf(tmp_file_path)
        os.unlink(tmp_file_path)

        analysis = analyze_blood_test(blood_test_report)
        articles = search_health_articles(analysis)
        recommendations = create_health_recommendations(analysis, articles)

        result = f"Analysis: {analysis}\n\nArticles: {articles}\n\nRecommendations: {recommendations}"

        send_email(email, "Blood Test Report Analysis", result)
        st.success("Analysis complete! Check your email for the results.")

if __name__ == "__main__":
    main()