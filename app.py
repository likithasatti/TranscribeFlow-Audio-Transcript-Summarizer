from flask import Flask, render_template, request, redirect, url_for, session, send_file
import uuid
import mysql.connector
import os
import json

# AI imports temporarily disabled
# from audiototext import transcribe_audio
# from summarizer import summarize_text

app = Flask(__name__)
app.secret_key = "transcribe_project_2026"

# -------- MySQL Connection --------
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="YOUR_PASSWORD",
        database="login_db"
    )
    cursor = db.cursor()
except:
    db = None
    cursor = None

# -------- Upload Folder --------
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# -------- Login Page --------
@app.route('/', methods=['GET', 'POST'])
def login():
    error = ""

    if request.method == 'POST':

        # Temporary cloud mode without database
        if cursor is None:
            session['username'] = request.form['username']
            return redirect(url_for('upload_page'))

        username = request.form['username']
        password = request.form['password']

        query = "SELECT * FROM users WHERE username=%s AND password=%s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()

        if user:
            session['username'] = username
            return redirect(url_for('upload_page'))
        else:
            error = "Invalid username or password"

    return render_template('login.html', error=error)


# -------- Register Page --------
@app.route('/register', methods=['GET', 'POST'])
def register():

    # Temporary cloud mode
    if cursor is None:
        return redirect(url_for('login'))

    message = ""

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            query = "INSERT INTO users (username, password) VALUES (%s, %s)"
            cursor.execute(query, (username, password))
            db.commit()
            return redirect(url_for('login'))
        except:
            message = "Username already exists"

    return render_template('register.html', message=message)


# -------- Upload Page --------
@app.route('/upload-page')
def upload_page():
    if 'username' not in session:
        return redirect(url_for('login'))

    return render_template('upload.html')


# -------- Upload File --------
@app.route('/upload', methods=['POST'])
def upload():

    if 'username' not in session:
        return redirect(url_for('login'))

    file = request.files['audio']

    if file and file.filename.endswith(('.mp3', '.wav')):

        audio_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(audio_path)

        # Temporary AI replacement
        transcript_text = "Test transcript"
        summary_text = "Test summary"

        transcript_filename = os.path.splitext(file.filename)[0] + ".txt"
        summary_filename = "summary_" + os.path.splitext(file.filename)[0] + ".txt"

        with open(os.path.join(UPLOAD_FOLDER, transcript_filename), "w", encoding="utf-8") as f:
            f.write(transcript_text)

        with open(os.path.join(UPLOAD_FOLDER, summary_filename), "w", encoding="utf-8") as f:
            f.write(summary_text)

        return render_template(
            "result.html",
            transcript=transcript_text,
            summary=summary_text,
            transcript_file=transcript_filename,
            summary_file=summary_filename,
            source="upload"
        )

    return "Invalid file format (Only MP3/WAV allowed)"


# -------- Record Audio --------
@app.route('/record', methods=['POST'])
def record_audio():

    if 'username' not in session:
        return redirect(url_for('login'))

    audio_file = request.files['audio']

    filename = f"recorded_{uuid.uuid4().hex}.wav"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    audio_file.save(filepath)

    # Temporary AI replacement
    transcript_text = "Test transcript"
    summary_text = "Test summary"

    transcript_filename = filename.replace(".wav", ".txt")
    summary_filename = "summary_" + transcript_filename

    with open(os.path.join(UPLOAD_FOLDER, transcript_filename), "w", encoding="utf-8") as f:
        f.write(transcript_text)

    with open(os.path.join(UPLOAD_FOLDER, summary_filename), "w", encoding="utf-8") as f:
        f.write(summary_text)

    return render_template(
        "result.html",
        transcript=transcript_text,
        summary=summary_text,
        transcript_file=transcript_filename,
        summary_file=summary_filename,
        source="record"
    )


# -------- Download TXT --------
@app.route('/download-combined/<transcript_filename>/<summary_filename>')
def download_combined(transcript_filename, summary_filename):

    if 'username' not in session:
        return redirect(url_for('login'))

    transcript_path = os.path.join(UPLOAD_FOLDER, transcript_filename)
    summary_path = os.path.join(UPLOAD_FOLDER, summary_filename)

    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript_text = f.read()

    with open(summary_path, "r", encoding="utf-8") as f:
        summary_text = f.read()

    combined_filename = os.path.splitext(transcript_filename)[0] + "_Final.txt"
    combined_path = os.path.join(UPLOAD_FOLDER, combined_filename)

    with open(combined_path, "w", encoding="utf-8") as f:
        f.write("===== TRANSCRIPTION =====\n\n")
        f.write(transcript_text)
        f.write("\n\n------------------------------------\n\n")
        f.write("===== SUMMARY =====\n\n")
        f.write(summary_text)

    return send_file(combined_path, as_attachment=True)


# -------- Download JSON --------
@app.route('/download-json/<transcript_filename>/<summary_filename>')
def download_json(transcript_filename, summary_filename):

    if 'username' not in session:
        return redirect(url_for('login'))

    transcript_path = os.path.join(UPLOAD_FOLDER, transcript_filename)
    summary_path = os.path.join(UPLOAD_FOLDER, summary_filename)

    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript_text = f.read()

    with open(summary_path, "r", encoding="utf-8") as f:
        summary_text = f.read()

    data = {
        "transcript": transcript_text,
        "summary": summary_text
    }

    json_filename = os.path.splitext(transcript_filename)[0] + "_result.json"
    json_path = os.path.join(UPLOAD_FOLDER, json_filename)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    return send_file(json_path, as_attachment=True)


# -------- Logout --------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)