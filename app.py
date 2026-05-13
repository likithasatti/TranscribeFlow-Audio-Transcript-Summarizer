from flask import Flask, render_template, request, redirect, url_for, session, send_file
import uuid
import mysql.connector
import os
import json

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "transcribe_project_2026")

# ---------------- ENV CONFIG ----------------
USE_DB = os.environ.get("USE_DB", "false").lower() == "true"

db = None
cursor = None

# ---------------- MYSQL (OPTIONAL) ----------------
if USE_DB:
    try:
        db = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
            database=os.environ.get("DB_NAME")
        )
        cursor = db.cursor()
    except Exception as e:
        print("DB connection failed:", e)
        db = None
        cursor = None

# ---------------- UPLOAD FOLDER ----------------
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ---------------- LAZY AI FUNCTIONS ----------------
def transcribe(audio_path):
    from audiototext import transcribe_audio
    return transcribe_audio(audio_path)

def summarize(text):
    from summarizer import summarize_text
    return summarize_text(text)


# ---------------- LOGIN ----------------
@app.route('/', methods=['GET', 'POST'])
def login():
    error = ""

    if request.method == 'POST':

        # Cloud mode (no DB)
        if cursor is None:
            session['username'] = request.form['username']
            return redirect(url_for('upload_page'))

        username = request.form['username']
        password = request.form['password']

        try:
            query = "SELECT * FROM users WHERE username=%s AND password=%s"
            cursor.execute(query, (username, password))
            user = cursor.fetchone()

            if user:
                session['username'] = username
                return redirect(url_for('upload_page'))
            else:
                error = "Invalid username or password"

        except Exception as e:
            return f"Database error: {str(e)}"

    return render_template('login.html', error=error)


# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():

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

        except Exception as e:
            message = f"Error: {str(e)}"

    return render_template('register.html', message=message)


# ---------------- UPLOAD PAGE ----------------
@app.route('/upload-page')
def upload_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('upload.html')


# ---------------- UPLOAD AUDIO ----------------
@app.route('/upload', methods=['POST'])
def upload():

    if 'username' not in session:
        return redirect(url_for('login'))

    if 'audio' not in request.files:
        return "No audio file uploaded"

    file = request.files['audio']

    if file.filename == '':
        return "No selected file"

    if file and file.filename.endswith(('.mp3', '.wav')):

        try:
            audio_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(audio_path)

            # -------- AI PROCESSING (SAFE) --------
            transcript_text = transcribe(audio_path)
            summary_text = summarize(transcript_text)

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

        except Exception as e:
            return f"AI Processing Error: {str(e)}"

    return "Invalid file format (Only MP3/WAV allowed)"


# ---------------- RECORD AUDIO ----------------
@app.route('/record', methods=['POST'])
def record_audio():

    if 'username' not in session:
        return redirect(url_for('login'))

    try:
        audio_file = request.files['audio']

        filename = f"recorded_{uuid.uuid4().hex}.wav"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        audio_file.save(filepath)

        # -------- AI PROCESSING --------
        transcript_text = transcribe(filepath)
        summary_text = summarize(transcript_text)

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

    except Exception as e:
        return f"Recording Error: {str(e)}"


# ---------------- DOWNLOAD TXT ----------------
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


# ---------------- DOWNLOAD JSON ----------------
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


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ---------------- RUN (RENDER SAFE) ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)