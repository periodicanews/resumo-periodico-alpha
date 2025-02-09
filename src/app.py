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
    page_title="Resumo Periódico",
    page_icon="assets/favicon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sessions
if "messages" not in st.session_state:
    st.session_state.messages = []

if "article_content" not in st.session_state:
    st.session_state.article_content = None

if "input_chat_placeholder" not in st.session_state:
    st.session_state.input_chat_placeholder = "Faça upload do artigo"

# Summary prompt
question = """Respond to the topics: Title ('Título'), Publication Date ('Data de publicação'), Authors ('Autores'), Summary in a Tweet ('Resumo em um tweet'), Overview ('Panorama'), and Key Findings ('Principais achados'). The response should be in PT-BR and based on the article."""


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
    st.image("assets/periodica.png", width=50)
    st.title("Resumo Periódico", anchor=False)
    st.write(
        """
Faça upload do artigo científico, gere o resumo e faça perguntas para o chatbot.

A ferramenta usa a biblioteca de aprendizado de máquina GROBID para extrair, analisar e reestruturar a publicação técnica, e o modelo de linguagem Claude 3.5 Haiku para gerar as respostas.
"""
    )
    st.markdown(
        'É experiental, de <a href="" target="_blank">código aberto</a> e um protótipo para automatizar o processo de curadoria da newsletter Periódica.',
        unsafe_allow_html=True,
    )

    st.divider()

    uploaded_file = st.file_uploader("Anexar artigo", type=("pdf"))
    button = st.button("Resumir", type="primary", use_container_width=True)

if button and not uploaded_file:
    st.warning("Sem arquivo")

if uploaded_file and button:
    # Make dirs
    pdf_name = uploaded_file.name
    date_now = datetime.datetime.now()
    input_path = f"resources/input_{date_now}/"
    pdf_path = f"{input_path}{pdf_name}"
    os.makedirs(input_path, exist_ok=True)

    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.toast("GROBID: iniciando análise", icon="⏳")

    # GROBID process
    grobid_client = GrobidClient(config_path="config.json")
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
    prompt = (
        f"""Here is an article:\n\n{st.session_state.article_content}\n\n{question}"""
    )

    st.session_state.messages.append({"role": "user", "content": prompt})

    response = llm_client()
    response_text = response.content[0].text

    st.session_state.messages.append({"role": "assistant", "content": response_text})

    st.session_state.input_chat_placeholder = "Faça mais perguntas sobre o artigo"

# Chat
for message in st.session_state.messages:
    # Hide summary and pre-prompt input messages
    if (
        message["content"] in question
        or "Here is an article:" in message["content"]
        or "Baseando-se neste artigo" in message["content"]
    ):
        continue

    with st.chat_message(message["role"]):
        st.markdown(hide_tei_content(message["content"]))

# Input user
user_input = st.chat_input(st.session_state.input_chat_placeholder)
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    followup_prompt = f"Baseando-se neste artigo:\n\n{st.session_state.article_content}\n\n{user_input}"

    st.session_state.messages.append({"role": "user", "content": followup_prompt})

    response = llm_client()

    if not response:
        st.stop()

    response_text = response.content[0].text

    with st.chat_message("assistant"):
        chat_response = st.write_stream(stream_data(hide_tei_content(response_text)))

    st.session_state.messages.append({"role": "assistant", "content": response_text})
