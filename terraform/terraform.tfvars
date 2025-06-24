# Project Configuration
project_name = "causal-analysis"
environment = "dev"

# AWS Region - Update to match your configured region
aws_region = "eu-central-1"

# OpenAI Configuration
openai_api_key = "sk-your-actual-openai-api-key-here"
openai_model = "gpt-3.5-turbo"

# Cognito OAuth URLs - Updated for local development and Vercel deployment
callback_urls = [
  "http://localhost:3000",
   
  "https://causal-prototype.vercel.app",
 
]

logout_urls = [
  "http://localhost:3000",
 
  "https://causal-prototype.vercel.app", 
  
]