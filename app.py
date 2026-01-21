import streamlit as st
import pdfplumber
import pandas as pd
import os
import time
from PIL import Image
from openai import OpenAI
import base64
import io
import json

# ============================================================
# CONFIGURAÇÕES DE PÁGINA E FONTE
# ============================================================
st.set_page_config(page_title="Selo Ricca de Revisão", layout="wide")

# ============================================================
# CARREGANDO FONTES AEONIK
# ============================================================
def load_fonts():
    st.markdown(
        """
        <style>
        @import url('https://fonts.cdnfonts.com/css/aeonik');

        /* Aplicação global da fonte */
        html, body, [class*="css"], [class*="st-"], .stApp, .main, p, div, h1, h2, h3, h4, h5, h6, span, label, button, input, textarea, .stSelectbox, .stDataFrame {
            font-family: 'Aeonik', sans-serif !important;
        }

        /* Cor do texto padrão: preto */
        body, p, div, h1, h2, h3, h4, h5, h6, span, label, .stTextInput input, .stTextArea textarea, .stMarkdown {
            color: #000000 !important;
        }

        /* Configuração de fundo */
        .stApp {
            background-color: #FFFFFF !important;
        }

        /* Botões magenta com texto branco */
        div.stButton > button {
            background-color: #FF00FF !important;
            color: white !important;
            font-family: 'Aeonik', sans-serif !important;
            font-weight: 700 !important;
            border-radius: 8px !important;
            padding: 0.5em 1.2em !important;
            font-size: 16px !important;
            border: none !important;
        }
        div.stButton > button:hover {
            background-color: #E600E6 !important;
            color: white !important;
        }

        /* Selectboxes grafite com texto branco */
        div[data-baseweb="select"] > div {
            background-color: #333333 !important;
            border-radius: 6px !important;
            border: none !important;
        }

        div[data-baseweb="select"] span,
        div[data-baseweb="select"] div[data-testid="stMarkdown"] p,
        div[data-baseweb="select"] svg {
            color: white !important;
            fill: white !important;
        }

        /* Dropdown menu items */
        ul[role="listbox"] li, div[role="listbox"] div {
            background-color: #333333 !important;
            color: white !important;
            font-family: 'Aeonik', sans-serif !important;
        }

        /* Dropdown menu hover */
        ul[role="listbox"] li:hover, div[role="listbox"] div:hover {
            background-color: #444444 !important;
        }

        /* Ajuste para dataframes */
        .stDataFrame table {
            font-family: 'Aeonik', sans-serif !important;
        }

        /* Ajuste para textos de spinner e mensagens */
        .stSpinner, .stAlert, .stInfo, .stSuccess, .stWarning, .stError {
            font-family: 'Aeonik', sans-serif !important;
        }

        /* Ajuste para file uploader */
        .stFileUploader div {
            font-family: 'Aeonik', sans-serif !important;
        }

        /* Remover borda do selectbox */
        div[data-baseweb="select"] > div {
            border: none !important;
        }

        /* Ajustar cor do texto no selectbox */
        div[data-baseweb="select"] {
            color: white !important;
        }

        /* Garantir que o texto dentro do selectbox seja branco */
        [data-baseweb="select"] [data-testid="stMarkdown"] p {
            color: white !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

load_fonts()

# ============================================================
# PATHS DE ASSETS
# ============================================================
logo_path = "assets/logo"
elementos_path = "assets/Elementos"

# ============================================================
# FUNÇÃO PARA DEFINIR FUNDO COM IMAGEM
# ============================================================
def set_background(image_filename, opacity=1.0):
    img_path = os.path.join(elementos_path, image_filename)

    # Verificar se o arquivo existe
    if not os.path.exists(img_path):
        st.warning(f"Imagem de fundo não encontrada: {img_path}")
        return

    with open(img_path, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()

    st.markdown(
        f"""
        <style>
        .app-background {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            opacity: {opacity};
            background-image: url("data:image/png;base64,{encoded}");
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center;
        }}
        </style>
        <div class="app-background"></div>
        """,
        unsafe_allow_html=True
    )

# ============================================================
# LOGIN
# ============================================================
def login_page():
    try:
        set_background("Patterns Escuras-03.png", opacity=1)
    except Exception as e:
        st.error(f"Erro ao carregar imagem de fundo: {e}")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image(os.path.join(logo_path, "Vertical_Cor.png"), width=300)
        except Exception as e:
            st.error(f"Erro ao carregar logo: {e}")

        st.title("Selo Ricca de Revisão")
        st.subheader("Login de acesso interno")

        user = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            if user == "riccarevisao" and password == "Ricc@2026!":
                st.session_state["autenticado"] = True
                st.experimental_rerun()
            else:
                st.error("Usuário ou senha incorretos.")

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    login_page()
    st.stop()

# ============================================================
# PÁGINA DE INFORMAÇÕES INICIAIS
# ============================================================
def info_page():
    try:
        set_background("Patterns-06.png", opacity=1)
    except Exception as e:
        st.error(f"Erro ao carregar imagem de fundo: {e}")

    try:
        st.image(os.path.join(logo_path, "Horizontal_Cor.png"), width=200)
    except Exception as e:
        st.error(f"Erro ao carregar logo: {e}")

    st.header("Informações do Projeto")

    col1, col2 = st.columns(2)
    with col1:
        nome_usuario = st.text_input("Seu nome")
        projeto = st.text_input("Nome do projeto")

    with col2:
        time_selecionado = st.selectbox("Time", ["Magenta", "Lilás", "Ouro", "Menta", "Patrulha", "Outro"])

    st.header("Glossário do cliente")
    st.info("Preencha o glossário conforme padrões do cliente (uma linha por regra): Ex.: diretor = Diretor-Presidente")
    glossario = st.text_area("Glossário", placeholder="empresa = Companhia\ncolaborador(a) = funcionário(a)\nEstado - ES = Estado (ES)")

    if st.button("Próximo"):
        if not nome_usuario or not projeto:
            st.warning("Por favor, preencha seu nome e o nome do projeto.")
        else:
            st.session_state["nome_usuario"] = nome_usuario
            st.session_state["projeto"] = projeto
            st.session_state["time"] = time_selecionado
            st.session_state["glossario"] = glossario
            st.session_state["pagina"] = "revisao"
            st.experimental_rerun()

if "pagina" not in st.session_state:
    st.session_state["pagina"] = "info"

if st.session_state.get("pagina") == "info":
    info_page()
    st.stop()

# ============================================================
# PÁGINA DE REVISÃO
# ============================================================
def pagina_revisao():
    try:
        set_background("Patterns Escuras_Prancheta 1.png", opacity=1)
    except Exception as e:
        st.error(f"Erro ao carregar imagem de fundo: {e}")

    try:
        st.image(os.path.join(logo_path, "Horizontal_Cor.png"), width=150)
    except Exception as e:
        st.error(f"Erro ao carregar logo: {e}")

    st.header("Revisão Ortográfica e Editorial")

    # Mostrar informações do projeto
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"Usuário: {st.session_state.get('nome_usuario', '')}")
    with col2:
        st.info(f"Projeto: {st.session_state.get('projeto', '')}")
    with col3:
        st.info(f"Time: {st.session_state.get('time', '')}")

    uploaded_file = st.file_uploader("Selecione o PDF", type=["pdf"])

    # Prompt base
    def montar_prompt(glossario_cliente):
        return f"""
Você atuará como revisor(a) e analista de consistência editorial. Analise o texto SEM reescrevê-lo.
Forneça APENAS ocorrências de erros ou inconsistências.
Use apenas o glossário do cliente fornecido abaixo:

{glossario_cliente}

Formato de saída (JSON):
[
    {{
    "pagina": "número da página",
    "categoria": "Ortografia | Gramática | Numeração | Terminologia | Estilo | ODS | Elementos Visuais",
    "trecho": "trecho original",
    "sugestao": "sugestão de correção",
    "justificativa": "observação"
    }}
]
Se não houver erros, retorne: "Nenhum erro identificado".
"""

    if uploaded_file:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            start_button = st.button("Iniciar Revisão", use_container_width=True)

        if start_button:
            start_time = time.time()
            texto_paginas = []

            with st.spinner("Extraindo texto do PDF..."):
                try:
                    with pdfplumber.open(uploaded_file) as pdf:
                        for i, page in enumerate(pdf.pages, start=1):
                            texto = page.extract_text() or ""
                            texto_paginas.append((i, texto))
                except Exception as e:
                    st.error(f"Erro ao processar o PDF: {e}")
                    st.stop()

            ocorrencias = []

            try:
                client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                prompt = montar_prompt(st.session_state["glossario"])
            except Exception as e:
                st.error(f"Erro ao configurar OpenAI: {e}")
                st.stop()

            # Processamento por página
            progress_bar = st.progress(0)
            status_text = st.empty()

            for idx, (pagina_num, texto) in enumerate(texto_paginas):
                status_text.text(f"Revisão da página {pagina_num} em andamento...")
                progress_value = (idx / len(texto_paginas))
                progress_bar.progress(progress_value)

                try:
                    resposta = client.chat.completions.create(
                        model="gpt-4.1-mini",
                        temperature=0,
                        messages=[
                            {"role": "system", "content": prompt},
                            {"role": "user", "content": texto}
                        ]
                    )

                    resultado = resposta.choices[0].message.content

                    # Tratamento da resposta
                    if "Nenhum erro identificado" in resultado:
                        continue

                    try:
                        clean_resultado = resultado.replace("
