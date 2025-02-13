import os
import json
import requests
import sqlite3
import glob
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv
from datetime import datetime
import re

load_dotenv()

app = FastAPI()
AIPROXY_API_KEY = os.getenv("AIPROXY_TOKEN")
LLM_API_URL = "https://api.aiproxy.com/v1/llm"

# Helper function to call the LLM API
def call_llm_api(prompt: str) -> str:
    if not AIPROXY_API_KEY:
        raise HTTPException(status_code=500, detail="AIPROXY_API_KEY not set.")
    
    headers = {
        "Authorization": f"Bearer {AIPROXY_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {"prompt": prompt, "max_tokens": 100}
    try:
        response = requests.post(LLM_API_URL, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        return response.json().get("text", "")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"LLM API request failed: {e}")

# Task A1
def generate_data(user_email: str):
    os.system(f"python3 https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py {user_email}")

# Task A2
def format_file():
    os.system("npx prettier@3.4.2 --write /data/format.md")

# Task A3 - Fix date parsing issue
def count_wednesdays():
    with open('/data/dates.txt', 'r') as f:
        dates = f.readlines()
    wednesday_count = 0
    for date in dates:
        date = date.strip()
        for fmt in ("%Y-%m-%d", "%Y/%m/%d %H:%M:%S"):
            try:
                if datetime.strptime(date, fmt).weekday() == 2:
                    wednesday_count += 1
                break
            except ValueError:
                continue
    with open('/data/dates-wednesdays.txt', 'w') as f:
        f.write(str(wednesday_count))

# Task A4
def sort_contacts():
    with open('/data/contacts.json', 'r') as f:
        contacts = json.load(f)
    sorted_contacts = sorted(contacts, key=lambda x: (x['last_name'], x['first_name']))
    with open('/data/contacts-sorted.json', 'w') as f:
        json.dump(sorted_contacts, f)

# Task A5
def write_recent_log_lines():
    log_files = sorted(glob.glob('/data/logs/*.log'), key=os.path.getmtime, reverse=True)[:10]
    with open('/data/logs-recent.txt', 'w') as f:
        for log_file in log_files:
            with open(log_file, 'r') as lf:
                first_line = lf.readline().strip()
                f.write(first_line + '\n')

# Task A6 - Improve task matching
def create_index_file():
    index = {}
    for md_file in glob.glob('/data/docs/*.md'):
        with open(md_file, 'r',encoding='utf-8') as f:
            for line in f:
                if line.startswith('#'):
                    index[os.path.basename(md_file)] = line[1:].strip()[2:]
                    break
    with open('/data/docs/index.json', 'w',encoding='utf-8') as f:
        json.dump(index, f, indent=4)

# Task A7 - Fallback for extracting sender email
def extract_sender_email():
    with open('/data/email.txt', 'r',encoding='utf-8') as f:
        email_content = f.read()
    
    # Fallback using regex
    match = re.search(r"From:.*?([\w\.-]+@[\w\.-]+)", email_content)
    sender_email = match.group(1) if match else ""
    
    if not sender_email:
        prompt = f"Extract the sender's email address from the following email content:\n{email_content}"
        sender_email = call_llm_api(prompt).strip()
    
    with open('/data/email-sender.txt', 'w') as f:
        f.write(sender_email)

# Task A8 - Handle API failure in extracting credit card number
def extract_credit_card_number():
    prompt = "Extract the credit card number from the provided image."
    try:
        credit_card_number = call_llm_api(prompt).replace(" ", "").strip()
    except HTTPException:
        credit_card_number = "FAILED_TO_EXTRACT"
    
    with open('/data/credit-card.txt', 'w') as f:
        f.write(credit_card_number)

# Task A9
def find_most_similar_comments():
    try:
        with open('/data/comments.txt', 'r', encoding='utf-8') as f:
            comments = [line.strip() for line in f.readlines() if line.strip()]

        if len(comments) < 2:
            raise ValueError("Not enough comments to compare.")

        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode(comments, convert_to_tensor=True)
        similarity_matrix = util.pytorch_cos_sim(embeddings, embeddings)

        max_sim = -1
        best_pair = (None, None)

        for i in range(len(comments)):
            for j in range(i + 1, len(comments)):
                if similarity_matrix[i][j] > max_sim:
                    max_sim = similarity_matrix[i][j]
                    best_pair = (comments[i], comments[j])

        with open('/data/comments-similar.txt', 'w', encoding='utf-8') as f:
            f.write("\n".join(best_pair))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in A9: {str(e)}")
# Task A10 - Improve task matching
def total_sales_gold_tickets():
    conn = sqlite3.connect('/data/ticket-sales.db')
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(units * price) FROM tickets WHERE type = 'Gold'")
    total_sales = cursor.fetchone()[0] or 0
    conn.close()
    with open('/data/ticket-sales-gold.txt', 'w') as f:
        f.write(str(total_sales))

@app.post("/run")
async def run_task(task: str):
    try:
        task = task.lower()
        if "generate data" in task:
            user_email = task.split()[-1]
            generate_data(user_email)
        elif "format the contents" in task:
            format_file()
        elif "count the number of wednesdays" in task:
            count_wednesdays()
        elif "sort the array of contacts" in task:
            sort_contacts()
        elif "write the first line of the 10 most recent" in task:
            write_recent_log_lines()
        elif "find all markdown files" in task or "create index file" in task or re.search(r"find.*markdown.*h1", task):
            create_index_file()
        elif "extract the sender's email address" in task or re.search(r"extract.*sender.*email", task):
            extract_sender_email()
        elif "extract the card number" in task:
            extract_credit_card_number()
        elif "find the most similar pair of comments" in task or re.search(r"most similar.*comments", task):
            find_most_similar_comments()
        elif "total sales of all the items in the gold ticket type" in task or "total sales of gold tickets" in task:
            total_sales_gold_tickets()
        else:
            raise HTTPException(status_code=400, detail="Task not recognized.")
        return {"message": "Task executed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/read")
async def read_file(path: str):
    try:
        with open(path, 'r') as f:
            content = f.read()
        return PlainTextResponse(content, status_code=200)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)
