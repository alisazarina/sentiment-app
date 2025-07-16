import os
import re # Extract sentiment value
import streamlit as st
from openai import AzureOpenAI
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
import PyPDF2 # import for PDF
import docx # import for DOCX

# Load environment variables
load_dotenv()

# Azure OpenAI client setup
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_API_BASE"),
)
deployment_name = os.getenv("AZURE_DEPLOYMENT_NAME")

# Streamlit UI
st.set_page_config(page_title="AI Sentiment Analysis", layout="centered")
st.title("🧠 Multilingual AI-Powered Sentiment Moderator")
st.caption("Powered by GPT-4 (Azure). " \
"Supports text, social media URLs, images, and files in real-time.")

# Input option
option = st.selectbox("Choose input type:",
                      ["Text", "URL", "Image", "File"]
                      )

content = ""

if option == "Text":
    content = st.text_area("Enter your text here:")

elif option == "URL":
    url = st.text_input("Enter a social media URL here:")
    if url:
        content = f"[Simulated content from {url}]" # placeholder for now

elif option == "Image":
    uploaded_image = st.file_uploader("Upload an image", type=["jpg", "png", "jpeg"])
    if uploaded_image:
        image = Image.open(uploaded_image)
        st.image(image, caption="Uploaded image")
        content = "" # placeholder

elif option == "File":
    uploaded_file = st.file_uploader("Upload a file (txt, pdf, docx)", type=["txt", "pdf", "docx"])
    if uploaded_file:
        file_type = uploaded_file.type
        content = ""
        if uploaded_file.name.endswith(".txt"):
            content = uploaded_file.read().decode("utf-8")
        elif uploaded_file.name.endswith(".pdf"):
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                content += page.extract_text() or ""
        elif uploaded_file.name.endswith(".docx"):
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs:
                content += para.text + "\n"
        else:
            st.warning("Unsupported file type.")
        if content:
            st.text_area("Extracted content:", value=content, height=200)
        if not content.strip():
            st.warning("No content extracted from the file. Please check the file format or content.")

# Analyse
analyse_clicked = st.button("Analyse Sentiment")
if analyse_clicked:
    if not content or not content.strip():
        st.warning("Please input some content to analyse.")
    else:
        with st.spinner("Analysing with Azure OpenAI..."):
            prompt = f"""
            You are a multilingual sentiment analysis expert.
            Analyse the tone of this content and classify it as Positive, Neutral, or Negative.
            Then explain your reasoning in moderate detail, but in a conversational tone and in bullet points.

            Content:
            \"{content}\"

            Respond like this:
            Sentiment: [Positive/Neutral/Negative]
            Explanation: [...]
            """

            response = client.chat.completions.create(
                model=deployment_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )

            result = response.choices[0].message.content

            # Add emoji based on sentiment
            sentiment_emoji = ""
            if "Sentiment:" in result:
                match = re.search(r"Sentiment:\s*\[?(Positive|Neutral|Negative)\]?", result, re.IGNORECASE)
                if match:
                    sentiment = match.group(1).lower()
                    if sentiment == "positive":
                        sentiment_emoji = "😊"
                    elif sentiment == "neutral":
                        sentiment_emoji = "😐"
                    elif sentiment == "negative":
                        sentiment_emoji = "😞"
                    # Replace or append emoji to sentiment line
                    result = re.sub(
                        r"(Sentiment:\s*\[?(Positive|Neutral|Negative)\]?)",
                        r"\1 " + sentiment_emoji,
                        result,
                        flags=re.IGNORECASE
                    )

            st.markdown("### 💬 Result")
            st.markdown(result)