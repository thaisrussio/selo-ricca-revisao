import streamlit as st
import pdfplumber
import pandas as pd
import os, time, base64, io, json
from openai import OpenAI
from PIL import Image

# ------------------------------  CONFIG PÁGINA  ------------------------------
st.set_page_config(page_title="Selo Ricca de Revisão", layout="wide")

# ------------------------------  FONTES AEONIK  -------------------------------
def load_fonts() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.cdnfonts.com/css/aeonik');

        html, body, [class*="css"], .stApp {
            font-family: 'Aeonik', sans-serif !important;
            color: #000 !important;
            background:#FFF !important;
        }

        /* botões magenta */
        div.stButton>button {
            background:#FF00FF !important;
            color:#FFF !important;
            font-weight:700 !important;
            border:none; border-radius:8px;
            padding:.5em 1.2em; font-size:16px;
        }
        div.stButton>button:hover{background:#E600E6 !important;}

        /* selectbox grafite */
        div[data-baseweb="select"]>div{background:#333 !important;border:none;border-radius:6px;}
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] svg,
        div[data-baseweb="select"] div[data-testid="stMarkdown"] p{color:#FFF !important;fill:#FFF !important;}
        ul[role="listbox"] li{background:#333 !important;color:#FFF !important;}

        /* inputs */
        .stTextInput input,.stTextArea textarea{color:#000 !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )

load_fonts()

# ------------------------------  PATHS  ---------------------------------------
logo_path      = "assets/logo"
elementos_path = "assets/Elementos"

# ------------------------------  FUNDO  ---------------------------------------
def set_background(img_name: str, opacity: float = 1.0) -> None:
    path = os.path.join(elementos_path, img_name)
    if not os.path.exists(path):
        st.warning(f"Imagem não encontrada: {path}")
        return
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    st.markdown(
        f"""
        <style>
        .app-background {{
            position:fixed; top:0; left:0; width:100%; height:100%;
            z-index:-1; opacity:{opacity};
            background:url("data:image/png;base64,{b64}") center/cover no-repeat;
        }}
        </style><div class="app-background"></div>""",
        unsafe_allow_html=True,
    )

# ------------------------------  LOGIN  ---------------------------------------
def login_page():
    set_background("Patterns Escuras-03.png")
    st.image(os.path.join(logo_path, "Vertical_Cor.png"), width=300)
    st.title("Selo Ricca de Revisão")
    st.subheader("Login de acesso interno")

    user     = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if user == "riccarevisao" and password == "Ricc@2026!":
            st.session_state.autenticado = True
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha incorretos.")

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if not st.session_state.autenticado:
    login_page()
    st.stop()

# ------------------  PÁGINA – INFORMAÇÕES INICIAIS  ---------------------------
def info_page():
    set_background("Patterns-06.png")
    st.image(os.path.join(logo_path, "Horizontal_Cor.png"), width=200)
    st.header("Informações do Projeto")

    col1, col2 = st.columns(2)
    with col1:
        nome_usuario = st.text_input("Seu nome")
        projeto      = st.text_input("Nome do projeto")
    with col2:
        time_sel = st.selectbox("Time", ["Magenta","Lilás","Ouro","Menta","Patrulha","Outro"])

    st.header("Glossário do cliente")
    st.info("Preencha uma regra por linha – exemplo: diretor = Diretor-Presidente")
    glossario = st.text_area("Glossário")

    if st.button("Próximo"):
        if not nome_usuario or not projeto:
            st.warning("Preencha nome e projeto.")
        else:
            st.session_state.update(
                nome_usuario=nome_usuario,
                projeto=projeto,
                time=time_sel,
                glossario=glossario,
                pagina="revisao",
            )
            st.experimental_rerun()

if st.session_state.get("pagina","info") == "info":
    info_page()
    st.stop()

# ------------------------  PÁGINA – REVISÃO  ----------------------------------
def pagina_revisao():
    set_background("Patterns Escuras_Prancheta 1.png")
    st.image(os.path.join(logo_path, "Horizontal_Cor.png"), width=150)
    st.header("Revisão Ortográfica e Editorial")

    col1,col2,col3 = st.columns(3)
    col1.info(f"Usuário:  {st.session_state.nome_usuario}")
    col2.info(f"Projeto:  {st.session_state.projeto}")
    col3.info(f"Time:     {st.session_state.time}")

    pdf_file = st.file_uploader("Selecione o PDF", type=["pdf"])

    def montar_prompt(gloss):
        return f"""
Você atuará como revisor(a) e analista de consistência editorial. Analise o texto SEM reescrevê-lo.
Forneça APENAS ocorrências de erros ou inconsistências.
Use apenas o glossário do cliente fornecido abaixo:

{gloss}

Formato de saída (JSON):
[
  {{
    "pagina": "número da página",
    "categoria": "Ortografia | Gramática | Numeração | Terminologia | Estilo | ODS | Elementos Visuais",
    "trecho":   "trecho original",
    "sugestao": "sugestão de correção",
    "justificativa": "observação"
  }}
]
Se não houver erros, retorne: "Nenhum erro identificado".
""".strip()

    if pdf_file:
        if st.button("Iniciar Revisão"):
            inicio = time.time()
            texto_paginas = []

            with st.spinner("Extraindo texto do PDF..."):
                with pdfplumber.open(pdf_file) as pdf:
                    for i,page in enumerate(pdf.pages,1):
                        texto_paginas.append((i, page.extract_text() or ""))

            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            prompt = montar_prompt(st.session_state.glossario)
            ocorrencias = []
            progress = st.progress(0.0)
            status   = st.empty()

            for idx,(pag,texto) in enumerate(texto_paginas,1):
                status.text(f"Revisando página {pag}...")
                progress.progress((idx-1)/len(texto_paginas))

                try:
                    resp = client.chat.completions.create(
                        model="gpt-4.1-mini",
                        temperature=0,
                        messages=[{"role":"system","content":prompt},
                                  {"role":"user","content":texto}],
                    )
                    resultado = resp.choices[0].message.content

                    if "Nenhum erro identificado" in resultado:
                        continue
