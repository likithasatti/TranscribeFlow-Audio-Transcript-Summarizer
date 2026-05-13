# from transformers import pipeline

# summarizer = pipeline("summarization", model="t5-small")

# def summarize_text(text):
#     summary = summarizer(text, max_length=60, min_length=25, do_sample=False)
#     return summary[0]['summary_text'] 

# from transformers import pipeline
# summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# def summarize_text(text):
#     summary = summarizer(
#         text,
#         max_length=100,
#         min_length=40,
#         do_sample=False
#     )
#     return summary[0]['summary_text']

# summarizer = pipeline("summarization", model="t5-small")

# def summarize_text(text):

#     # Add prefix (important for T5)
#     text = "summarize: " + text

#     summary = summarizer(
#         text,
#         max_length=120,
#         min_length=40,
#         do_sample=False
#     )

#     return summary[0]['summary_text']

def summarize_text(text):
    return text[:500]