# Deployment Guide

## Local
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py

## Streamlit (shareable)
streamlit run app_streamlit.py
# deploy to Streamlit Community Cloud by pointing it at this repo + app_streamlit.py

## Optional LLM agent
cp config/.env.example .env
# set AGENT_BACKEND=llm and OPENAI_API_KEY=... then install langchain/openai
# The pipeline still runs fully without this (rule mode is the default).

## Scheduling
Wrap `python main.py` in cron / Task Scheduler for monthly refresh; commit powerbi/
outputs or publish to Power BI Service.
