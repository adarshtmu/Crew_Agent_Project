import streamlit as st
import PyPDF2
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from crewai import Agent, Task, Crew
from dotenv import load_dotenv
import os
from openai import OpenAI
import re

# Load environment variables
load_dotenv()

# Get API keys from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

# Debug logging
st.sidebar.write(f"OPENAI_API_KEY set: {'Yes' if OPENAI_API_KEY else 'No'}")
st.sidebar.write(f"SENDER_EMAIL set: {'Yes' if SENDER_EMAIL else 'No'}")
st.sidebar.write(f"SENDER_PASSWORD set: {'Yes' if SENDER_PASSWORD else 'No'}")

# Initialize OpenAI client
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
    st.sidebar.success("OpenAI client initialized successfully")
else:
    st.sidebar.warning("OpenAI API key is not set. Fallback analysis will be used.")


# PDF Analysis function
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text


# Email function
def send_email(recipient, subject, body):
    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["To"] = recipient
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient, message.as_string())
        return True
    except smtplib.SMTPAuthenticationError:
        st.error(
            "Email authentication failed. Please check your email and password in the .env file. For Gmail, use an App Password.")
        return False
    except Exception as e:
        st.error(f"Error sending email: {str(e)}")
        return False


# Updated GPT-3.5 function
def call_openai(prompt):
    if not OPENAI_API_KEY:
        return "Error: OpenAI API key is not set"

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes blood test reports."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        if "insufficient_quota" in str(e):
            st.warning("OpenAI API quota exceeded. Using fallback analysis method.")
        else:
            st.error(f"Error calling OpenAI API: {str(e)}")
        return "Error: API unavailable"


# Fallback analysis function
def fallback_analysis(text):
    # Define some common blood test parameters and their normal ranges
    parameters = {
        "Hemoglobin": (13.5, 17.5),  # g/dL
        "White Blood Cell Count": (4.5, 11.0),  # 10^3/µL
        "Platelet Count": (150, 450),  # 10^3/µL
        "Glucose": (70, 100),  # mg/dL
        "Cholesterol": (0, 200),  # mg/dL
    }

    analysis = []
    for param, (low, high) in parameters.items():
        pattern = rf"{param}\D+(\d+\.?\d*)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            if value < low:
                analysis.append(f"{param} is low at {value}. Normal range is {low}-{high}.")
            elif value > high:
                analysis.append(f"{param} is high at {value}. Normal range is {low}-{high}.")
            else:
                analysis.append(f"{param} is normal at {value}. Normal range is {low}-{high}.")

    if not analysis:
        return "No common blood test parameters found in the report."
    return "\n".join(analysis)


# Main application
def main():
    st.title("Blood Test Report Analyzer")

    # File uploader
    uploaded_file = st.file_uploader("Upload your blood test report (PDF)", type="pdf")
    email = st.text_input("Enter your email address")

    if st.button("Analyze Report"):
        if uploaded_file and email:
            # Process the PDF
            pdf_content = extract_text_from_pdf(uploaded_file)

            # Try OpenAI first, fall back to simple analysis if it fails
            st.info("Analyzing report...")
            analysis_result = call_openai(f"Analyze this blood test report: {pdf_content}")
            if analysis_result.startswith("Error:"):
                analysis_result = fallback_analysis(pdf_content)
                recommendation_result = "Based on the analysis, please consult with your healthcare provider for personalized recommendations."
            else:
                recommendation_result = call_openai("Provide health recommendations based on the analysis")
                if recommendation_result.startswith("Error:"):
                    recommendation_result = "Based on the analysis, please consult with your healthcare provider for personalized recommendations."

            # Display results
            st.subheader("Analysis Results and Recommendations")
            st.write(f"Analysis: {analysis_result}")
            st.write(f"Recommendations: {recommendation_result}")

            # Send email
            if SENDER_EMAIL and SENDER_PASSWORD:
                if send_email(email, "Your Blood Test Report Analysis",
                              f"Analysis: {analysis_result}\n\nRecommendations: {recommendation_result}"):
                    st.success(f"Results have been sent to {email}")
            else:
                st.error("Email credentials are not set. Cannot send email.")
        else:
            st.error("Please upload a PDF and enter your email address.")


if __name__ == "__main__":
    main()
