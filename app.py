from flask import Flask, render_template, request, session, send_file, redirect
import sqlite3, random, datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
app.secret_key = "secret123"

courses = ["python","java","c","cpp","javascript","sql","php","csharp","kotlin","html","css"]

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS theory(id INTEGER PRIMARY KEY AUTOINCREMENT, course TEXT, content TEXT)")
    conn.commit()
    conn.close()

init_db()

# ================= MCQ =================
def generate_questions(course):
    return [
        {"q":f"What is {course.upper()} used for?","options":["Development","Cooking","Driving","None"],"ans":"Development"},
        {"q":f"{course.upper()} type?","options":["Programming","Hardware","Network","None"],"ans":"Programming"},
        {"q":f"Used in industry?","options":["Yes","No","Rarely","None"],"ans":"Yes"},
        {"q":f"Helps in?","options":["Apps","Food","Sleep","None"],"ans":"Apps"},
        {"q":f"Syntax is?","options":["Structured","Random","None","All"],"ans":"Structured"},
        {"q":f"Who learns?","options":["Students","Animals","None","All"],"ans":"Students"},
        {"q":f"Is useful?","options":["Yes","No","None","All"],"ans":"Yes"},
        {"q":f"Used worldwide?","options":["Yes","No","None","All"],"ans":"Yes"},
        {"q":f"Improves?","options":["Skills","Nothing","None","All"],"ans":"Skills"},
        {"q":f"Important?","options":["Yes","No","None","All"],"ans":"Yes"}
    ]

all_questions = {c: generate_questions(c) for c in courses}

# ================= ROUTES =================
@app.route('/')
def home():
    return render_template("index.html", courses=courses)

@app.route('/admin', methods=['GET','POST'])
def admin():
    if request.method == "POST":
        if request.form['password'] == "admin123":
            session['admin'] = True
            return redirect('/')
    return render_template("admin.html")

@app.route('/course/<course_id>')
def course(course_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM theory WHERE course=?", (course_id,))
    data = c.fetchall()
    conn.close()
    return render_template("course.html", data=data, course=course_id)

@app.route('/add_theory/<course_id>', methods=['POST'])
def add_theory(course_id):
    if not session.get('admin'):
        return "Unauthorized"

    content = request.form.get('content')

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO theory(course, content) VALUES (?,?)",(course_id,content))
    conn.commit()
    conn.close()

    return redirect(f"/course/{course_id}")

@app.route('/delete/<int:id>/<course>')
def delete(id, course):
    if not session.get('admin'):
        return "Unauthorized"

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM theory WHERE id=?",(id,))
    conn.commit()
    conn.close()

    return redirect(f"/course/{course}")

@app.route('/download_theory/<course_id>')
def download_theory(course_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT content FROM theory WHERE course=?", (course_id,))
    data = c.fetchall()
    conn.close()

    file_path = f"static/{course_id}_notes.pdf"
    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    content = []

    for d in data:
        content.append(Paragraph(d[0], styles['Normal']))
        content.append(Spacer(1, 12))

    doc.build(content)
    return send_file(file_path, as_attachment=True)

@app.route('/quiz/<course_id>')
def quiz(course_id):
    questions = all_questions[course_id]
    random.shuffle(questions)
    session['questions'] = questions
    return render_template("quiz.html", questions=questions, course=course_id)

@app.route('/submit', methods=['POST'])
def submit():
    questions = session.get('questions', [])
    score = 0
    results = []

    for i, q in enumerate(questions):
        user = request.form.get(f"q{i}")
        correct = q['ans']
        if user == correct:
            score += 1

        results.append({"q":q['q'], "user":user, "correct":correct})

    percent = int((score/len(questions))*100)
    session['score'] = score
    session['percent'] = percent

    return render_template("result.html", results=results, score=score, total=len(questions), percent=percent)

@app.route('/get_certificate')
def get_certificate():
    return render_template("get_certificate.html")

@app.route('/certificate', methods=['POST'])
def certificate():
    name = request.form['name']
    score = session.get('score',0)
    percent = session.get('percent',0)
    date = datetime.datetime.now().strftime("%d-%m-%Y")

    file_path = "static/certificate.pdf"
    c = canvas.Canvas(file_path, pagesize=A4)
    w,h = A4

    c.setFillColorRGB(0.95,0.97,1)
    c.rect(0,0,w,h,fill=1)

    c.setStrokeColor(colors.darkblue)
    c.setLineWidth(4)
    c.rect(30,30,w-60,h-60)

    try:
        c.drawImage("static/logo.png", w/2-40, h-110, width=80, height=80)
    except:
        pass

    c.setFont("Helvetica-Bold",30)
    c.drawCentredString(w/2,h-150,"CERTIFICATE")

    c.setFont("Helvetica",16)
    c.drawCentredString(w/2,h-190,"OF COMPLETION")

    c.setFont("Helvetica",14)
    c.drawCentredString(w/2,h-250,"This is to certify that")

    c.setFont("Helvetica-Bold",26)
    c.setFillColor(colors.green)
    c.drawCentredString(w/2,h-290,name)

    c.setFillColor(colors.black)
    c.drawCentredString(w/2,h-340,"has successfully completed the quiz")

    c.drawCentredString(w/2,h-390,f"Score: {score}")
    c.drawCentredString(w/2,h-420,f"Percentage: {percent}%")
    c.drawCentredString(w/2,h-450,f"Date: {date}")

    c.save()

    return render_template("certificate.html", name=name, score=score, percent=percent, date=date)

@app.route('/download')
def download():
    return send_file("static/certificate.pdf", as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)