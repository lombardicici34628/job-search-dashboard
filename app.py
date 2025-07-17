import os
import streamlit as st
from jobspy import scrape_jobs
import pandas as pd
import openai

st.set_page_config(page_title="Job Search Dashboard", layout="wide")
st.title("🔍 AI‑Powered Job Scraper")
st.markdown("Built with `JobSpy`, `OpenAI`, and `Streamlit`")

# Load OpenAI key (via Streamlit Secrets or user input)
openai_api_key = os.getenv("OPENAI_API_KEY") or st.text_input("🔑 OpenAI API Key", type="password")

# Search inputs
search_term = st.text_input("🔎 Job Title", "JOB-ROLE")
location = st.text_input("📍 Location(s)", "Bangalore, Hyderabad, Pune")
results_wanted = st.slider("🎯 Number of Results", 10, 200, 50)
hours_old = st.slider("🕒 Posted within last (hours)", 24, 168, 72)

if st.button("🚀 Run Job Search"):
    with st.spinner("Scraping jobs..."):
        jobs = scrape_jobs(
            site_name=["linkedin", "indeed"],
            search_term=search_term,
            location=location,
            results_wanted=results_wanted,
            hours_old=hours_old,
            country_indeed="India",
            linkedin_fetch_description=True
        )
    st.success(f"✅ {len(jobs)} jobs scraped!")

# ✅ Define core columns
    core_columns = [
    "title", "company", "location", "experience_range", "date_posted", "job_url"
    ]

# 🔍 Display available columns (for debugging)
    st.write("🔎 Available columns:", list(jobs.columns))

# ✅ Select only valid (existing) columns
    valid_columns = [col for col in core_columns if col in jobs.columns]
    df = jobs[valid_columns]

# 📊 Show in Streamlit
    st.dataframe(df, use_container_width=True)

    if openai_api_key and not df.empty:
        st.subheader("🤖 AI Match (Top Skills/Keywords)")
        openai.api_key = openai_api_key
        
        sample_desc = "\n\n".join(df["description"].head(5).astype(str))
        with st.spinner("Analyzing with GPT…"):
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You're a helpful job search assistant."},
                    {"role": "user", "content": f"Extract key skills, tools, and earning patterns from these job descriptions:\n{sample_desc}"}
                ]
            )
        st.markdown(response["choices"][0]["message"]["content"])

    st.download_button("⬇️ Download CSV", df.to_csv(index=False), file_name="jobs.csv", mime="text/csv")
