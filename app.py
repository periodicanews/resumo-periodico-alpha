import streamlit as st
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

st.title("Resumo Científico", anchor=False)

uploaded_file = st.file_uploader("Anexar artigo", type=("txt", "md"))

question = st.text_input(
    "Pergunte algo sobre o artigo",
    disabled=not uploaded_file,
)

if uploaded_file and question:
    article = uploaded_file.read().decode()
    prompt = f"""{anthropic.HUMAN_PROMPT} Here's an article:\n\n
    {article}\n\n\n\n{question}{anthropic.AI_PROMPT}"""

    client = anthropic.Client(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    st.write("### Resumo")
    st.write(response.content[0].text)
