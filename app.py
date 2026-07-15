from flask import Flask, render_template, request, redirect
import sqlite3
import re
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- Database ----------------

conn = sqlite3.connect("resume.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS resumes(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    phone TEXT,
    skills TEXT,
    education TEXT,
    score INTEGER
)
""")

conn.commit()
conn.close()


# ---------------- Resume Extraction ----------------

def extract_details(file_path):

    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()

    lines = text.split("\n")

    name = lines[0].strip() if lines else "Not Found"

    email = re.search(r'[\w\.-]+@[\w\.-]+', text)
    email = email.group(0) if email else "Not Found"

    phone = re.search(r'\b\d{10}\b', text)
    phone = phone.group(0) if phone else "Not Found"

    skills_list = [
        "Python",
        "Java",
        "C",
        "C++",
        "SQL",
        "HTML",
        "CSS",
        "JavaScript",
        "Flask",
        "Django",
        "React",
        "Bootstrap",
        "Machine Learning",
        "AI"
    ]

    found = []

    for skill in skills_list:
        if skill.lower() in text.lower():
            found.append(skill)

    skills = ", ".join(found) if found else "Not Found"

    education_keywords = [
        "Bachelor",
        "B.E",
        "B.Tech",
        "M.Tech",
        "MBA",
        "Diploma",
        "HSC",
        "SSC"
    ]

    education = "Not Found"

    for edu in education_keywords:
        if edu.lower() in text.lower():
            education = edu
            break

    return name, email, phone, skills, education


# ---------------- Resume Score ----------------

def calculate_score(email, phone, skills, education):

    score = 0

    if email != "Not Found":
        score += 20

    if phone != "Not Found":
        score += 20

    if education != "Not Found":
        score += 20

    if skills != "Not Found":
        score += 40

    return score


# ---------------- Home ----------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- Upload ----------------

@app.route("/upload", methods=["POST"])
def upload():

    file = request.files["resume"]

    if file.filename == "":
        return "Please choose a file."

    if not file.filename.endswith(".txt"):
        return "Upload only TXT resumes."

    path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)

    file.save(path)

    name, email, phone, skills, education = extract_details(path)

    score = calculate_score(email, phone, skills, education)

    conn = sqlite3.connect("resume.db")
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO resumes
    (name,email,phone,skills,education,score)
    VALUES(?,?,?,?,?,?)
    """, (name, email, phone, skills, education, score))

    conn.commit()
    conn.close()

    return render_template(
        "result.html",
        name=name,
        email=email,
        phone=phone,
        skills=skills,
        education=education,
        score=score
    )


# ---------------- History ----------------

@app.route("/history")
def history():

    conn = sqlite3.connect("resume.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM resumes")

    rows = cur.fetchall()

    conn.close()

    return render_template("history.html", rows=rows)


# ---------------- Search ----------------

@app.route("/search", methods=["POST"])
def search():

    keyword = request.form["keyword"]

    conn = sqlite3.connect("resume.db")
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM resumes WHERE name LIKE ?",
        ('%' + keyword + '%',)
    )

    rows = cur.fetchall()

    conn.close()

    return render_template("history.html", rows=rows)


# ---------------- Delete ----------------

@app.route("/delete/<int:id>")
def delete(id):

    conn = sqlite3.connect("resume.db")
    cur = conn.cursor()

    cur.execute("DELETE FROM resumes WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/history")


# ---------------- Run ----------------

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
