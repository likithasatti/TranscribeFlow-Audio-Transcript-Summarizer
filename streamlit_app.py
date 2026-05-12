import streamlit as st

st.title("TranscribeFlow AI")

audio = st.file_uploader("Upload Audio File")

if audio:
    st.audio(audio)

    st.success("Audio uploaded successfully!")