from faster_whisper import WhisperModel

model = None

def transcribe_audio(audio_path):
    global model

    if model is None:
        model = WhisperModel("tiny")

    segments, info = model.transcribe(audio_path)

    text = ""

    for segment in segments:
        text += segment.text + " "

    return text