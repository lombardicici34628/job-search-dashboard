import os
import uuid
import streamlit as st
from jobspy import scrape_jobs
import pandas as pd
from openai import OpenAI

st.set_page_config(page_title="Job Search Dashboard", layout="wide")
st.title("🔍 AI‑Powered Job Scraper")
st.markdown("Built with `JobSpy`, `OpenAI`, and `Streamlit`")

# 🔑 OpenAI Key
openai_api_key = os.getenv("OPENAI_API_KEY") or st.text_input("🔑 OpenAI API Key", type="password")
client = OpenAI(api_key=openai_api_key) if openai_api_key else None

# 🎯 User Inputs
search_term = st.text_input("🔎 Enter job title or keywords", "QA Automation Engineer")
location = st.text_input("📍 Location(s)", "Bangalore, Hyderabad")
results_wanted = st.slider("🎯 Number of Results", 10, 200, 50)
hours_old = st.slider("🕒 Posted within last (hours)", 1, 168, 72)

# 🛠️ Table rendering with Copy buttons
def render_copy_table(df):
    df = df.copy()
    df["Job Link"] = df["job_url"].apply(lambda url: f"""
        <span style="font-size: 14px;">
            <a href="{url}" target="_blank">{url}</a>
            <button onclick="navigator.clipboard.writeText('{url}')" 
                style="margin-left:10px; padding:4px 8px; background:#0099ff; color:white; border:none; border-radius:4px; cursor:pointer;">
                📋 Copy
            </button>
        </span>
    """)
    display_df = df[["title", "company", "location", "date_posted", "Job Link"]]
    table_id = "job_table_" + str(uuid.uuid4()).replace("-", "")

    st.markdown(f"""
    <div style="overflow-x: auto;">
        <style>
            #{table_id} td, #{table_id} th {{
                padding: 8px 12px;
                border: 1px solid #444;
                text-align: left;
                font-size: 14px;
            }}
            #{table_id} tr:nth-child(even) {{
                background-color: #1e1e1e;
            }}
            #{table_id} {{
                border-collapse: collapse;
                width: 100%;
                margin-top: 10px;
            }}
        </style>
        {display_df.to_html(escape=False, index=False, table_id=table_id)}
    </div>
    """, unsafe_allow_html=True)

# 🔍 Search
if st.button("🚀 Run Job Search"):
    with st.spinner("Scraping jobs..."):
        jobs = scrape_jobs(
            site_name=["indeed", "glassdoor", "linkedin"],
            search_term=search_term,
            location=location,
            results_wanted=results_wanted,
            hours_old=hours_old,
            country_indeed="India",
            linkedin_fetch_description=False
        )
    st.success(f"✅ {len(jobs)} jobs scraped!")

    # Select columns
    core_columns = [
        "title", "company", "location", "description", "date_posted", "job_url"
    ]
    valid_columns = [col for col in core_columns if col in jobs.columns]
    df = jobs[valid_columns]

    # Show table with copy link buttons
    st.subheader("📋 Job Listings with Copy Buttons")
    render_copy_table(df)

    # GPT analysis if available
    if client and "description" in df.columns and not df["description"].dropna().empty:
        st.subheader("🤖 AI Match (Top Skills/Keywords)")
        sample_desc = "\n\n".join(df["description"].dropna().astype(str).head(5))
        with st.spinner("Analyzing with GPT…"):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You're a helpful job search assistant."},
                    {"role": "user", "content": f"Extract key skills and tools from these job descriptions:\n{sample_desc}"}
                ]
            )
        st.markdown(response.choices[0].message.content)

    # Export
    st.download_button("⬇️ Download CSV", df.to_csv(index=False), file_name="jobs.csv", mime="text/csv")
