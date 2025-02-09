import streamlit as st
import anthropic
import os
from dotenv import load_dotenv
from grobid_client.grobid_client import GrobidClient
import time
import datetime
import re

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

st.set_page_config(
    page_title="Resumo Científico",
    page_icon="📃",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sessions

if "messages" not in st.session_state:
    st.session_state.messages = []

if "article_content" not in st.session_state:
    st.session_state.article_content = None


# Send prompt to LLM
def llm_client():
    try:
        st.toast("Claude 3.5 Haiku: gerando resposta", icon="⏳")

        client = anthropic.Client(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            max_tokens=1000,
            model="claude-3-5-haiku-20241022",
            messages=st.session_state.messages,
        )
        return response
    except Exception as e:
        st.error(f"Erro ao gerar resposta: {e}")


# Typing style
def stream_data(response):
    for word in response.split(" "):
        yield word + " "
        time.sleep(0.05)


# Hide XML content from chat
def hide_tei_content(response):
    return re.sub(r"<\?xml.*?</TEI>", "", response, flags=re.DOTALL)


# Sidebar
with st.sidebar:
    st.title("Resumo Científico", anchor=False)
    uploaded_file = st.file_uploader("Anexar artigo", type=("pdf"))
    button = st.button("Gerar Resumo", icon="🖋️", use_container_width=True)

if uploaded_file and button:
    # Make dirs
    pdf_name = uploaded_file.name
    date_now = datetime.datetime.now()
    input_path = f"./resources/input_{date_now}/"
    pdf_path = f"{input_path}{pdf_name}"
    os.makedirs(input_path, exist_ok=True)

    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.toast("GROBID: iniciando análise", icon="⏳")

    # GROBID process
    grobid_client = GrobidClient(config_path="./config.json")
    grobid_client.process(
        "processFulltextDocument",
        input_path,
        consolidate_citations=True,
        tei_coordinates=True,
        force=True,
        verbose=True,
    )

    xml_name = pdf_name.replace(".pdf", ".grobid.tei.xml")
    tei_file_path = f"{input_path}{xml_name}"

    if not os.path.exists(tei_file_path):
        st.warning(
            "Não foi possível encontrar o arquivo XML. Verifique o servidor do GROBID."
        )
        st.stop()

    with open(tei_file_path, "r") as tei_file:
        st.session_state.article_content = tei_file.read()

    # Summary
    question = """Responda aos tópicos: Título ('Título'), Data de publicação ('Data de publicação'),
    Autores ('Autores'), Resumo em um tweet ('Resumo em um tweet'), Panorama ('Panorama'),
    e Principais achados ('Principais achados'). A resposta deve estar em PT-BR e ser baseada no artigo."""

    prompt = f"""{anthropic.HUMAN_PROMPT} Aqui está um artigo:\n\n{st.session_state.article_content}\n\n{question}{anthropic.AI_PROMPT}"""

    st.session_state.messages.append({"role": "user", "content": prompt})

    response = llm_client()
    response_text = response.content[0].text

    st.session_state.messages.append({"role": "assistant", "content": response_text})

# Chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["content"] in question:
            pass
        if "Baseando-se neste artigo" in message["content"]:
            pass
        st.markdown(hide_tei_content(message["content"]))

# Input user
user_input = st.chat_input("Faça mais perguntas sobre o artigo")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    followup_prompt = f"{anthropic.HUMAN_PROMPT} Baseando-se neste artigo:\n\n{st.session_state.article_content}\n\n{user_input}{anthropic.AI_PROMPT}"

    st.session_state.messages.append({"role": "user", "content": followup_prompt})

    response = llm_client()
    response_text = response.content[0].text

    if not response:
        st.stop()

    with st.chat_message("assistant"):
        chat_response = st.write_stream(stream_data(hide_tei_content(response_text)))

    st.session_state.messages.append({"role": "assistant", "content": response_text})
