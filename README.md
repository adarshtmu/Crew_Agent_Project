# Blood Test Analysis Project

## Overview

The Blood Test Analysis project is a web application that allows users to upload blood test reports in PDF format. The application analyzes the content of the reports using a language model and sends the analysis results to the user's email. It integrates with Google APIs for email functionality and uses DuckDuckGo for searching relevant health articles.

## Features

- Upload PDF files of blood test reports.
- Analyze the content of the reports using advanced language models.
- Send analysis results via email.
- Search for related health articles using DuckDuckGo.

## Installation

To set up the project locally, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   

2. Create a virtual environment (optional but recommended):

python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

3. Install required packages:

pip install -r requirements.txt


4. Set up environment variables:
Create a .env file in the root directory and add the following variables:

HUGGINGFACE_API_KEY=<your_huggingface_api_key>
APP_API_KEY=<your_app_api_key>

5. Download Google credentials:
Obtain your credentials.json file from the Google Developer Console and place it in the root directory of your project.





Usage

Run the application:

uvicorn main:app --host 0.0.0.0 --port 8000

Access the application:
Open your web browser and navigate to http://127.0.0.1:8000.
Upload a blood test report:
Use the provided interface to upload a PDF file containing your blood test report and enter your email address.
Receive analysis results:
After processing, you will receive an email with the analysis results.
