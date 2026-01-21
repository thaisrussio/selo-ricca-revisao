import streamlit as st
import pdfplumber
import pandas as pd
import os
import time
from PIL import Image
from openai import OpenAI
import base64

# ============================================================
# CONFIGURAÇÕES DE PÁGINA E FONTE
# ============================================================
st.markdown(
    """
    <style>
    /* Botões principais */
    div.stButton > button {
        background-color: #FF00FF;  /* Magenta */
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.5em 1.2em;
        font-family: 'Aeonik', sans-serif;
        font-size: 16px;
    }
    div.stButton > button:hover {
        background-color: #E600E6; /* Tom mais escuro ao passar o mouse */
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.set_page_config(page_title="Selo Ricca de Revisão", layout="wide")

# Fontes Aeonik
def load_fonts():
    st.markdown(
        """
        <style>
        @font-face {
            font-family: 'Aeonik';
            src: url('assets/fonts/Aeonik-Regular.otf') format('opentype');
            font-weight: 400;
        }
        @font-face {
            font-family: 'Aeonik';
            src: url('assets/fonts/Aeonik-Medium.otf') format('opentype');
            font-weight: 500;
        }
        @font-face {
            font-family: 'Aeonik';
            src: url('assets/fonts/Aeonik-Bold.otf') format('opentype');
            font-weight: 700;
        }
        html, body, .stApp, .main {
            font-family: 'Aeonik', sans-serif;
            background-color: white !important;
        }
        </style>
        """, unsafe_allow_html=True
    )
load_fonts()

# ============================================================
# PATHS DE ASSETS
# ============================================================
logo_path = "assets/logo.png"
fonts_path = "assets/fonts"
elementos_path = "assets/Elementos"

def set_background(image_filename, opacity=1.0):
    img_path = os.path.join(elementos_path, image_filename)
    with open(img_path, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded}");
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center;
            opacity: 1;
            z-index: -1;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# ============================================================
# LOGIN
# ============================================================
def login_page():
    set_background("Patterns Escuras-03.png", opacity=1)
    st.image(os.path.join(logo_path, "Vertical_Cor.png"), width=300)
    st.title("Selo Ricca de Revisão")
    st.subheader("Login de acesso interno")
    
    user = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        if user == "riccarevisao" and password == "Ricc@2026!":
            st.session_state["autenticado"] = True
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
    set_background("Patterns-06.png", opacity=1)
    st.image(os.path.join(logo_path, "Horizontal_Cor.png"), width=200)
    st.header("Informações do Projeto")
    nome_usuario = st.text_input("Seu nome")
    projeto = st.text_input("Nome do projeto")
    time_selecionado = st.selectbox("Time", ["Magenta", "Lilás", "Ouro", "Menta", "Patrulha", "Outro"])
    
    st.header("Glossário do cliente")
    st.info("Preencha o glossário conforme padrões do cliente (uma linha por regra): Ex.: diretor = Diretor-Presidente")
    glossario = st.text_area("Glossário", placeholder="empresa = Companhia\ncolaborador(a) = funcionário(a)\nEstado - ES = Estado (ES)")

    if st.button("Próximo"):
        st.session_state["nome_usuario"] = nome_usuario
        st.session_state["projeto"] = projeto
        st.session_state["time"] = time_selecionado
        st.session_state["glossario"] = glossario
        st.session_state["pagina"] = "revisao"

if "pagina" not in st.session_state or st.session_state.get("pagina") != "revisao":
    info_page()
    st.stop()

# ============================================================
# PÁGINA DE REVISÃO
# ============================================================
def pagina_revisao():
    set_background("Patterns Escuras_Prancheta 1.png", opacity=1)
    st.image(os.path.join(logo_path, "Horizontal_Cor.png"), width=150)
    st.header("Revisão Ortográfica e Editorial")
    
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
        if st.button("Iniciar Revisão"):
            start_time = time.time()
            with st.spinner("Extraindo texto..."):
                texto_paginas = []
                with pdfplumber.open(uploaded_file) as pdf:
                    for i, page in enumerate(pdf.pages, start=1):
                        texto = page.extract_text() or ""
                        texto_paginas.append((i, texto))
            
            ocorrencias = []
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            prompt = montar_prompt(st.session_state["glossario"])

            # Processamento por página
            for pagina_num, texto in texto_paginas:
                with st.spinner(f"Revisão da página {pagina_num} em andamento..."):
                    resposta = client.chat.completions.create(
                        model="gpt-4.1-mini",
                        temperature=0,
                        messages=[
                            {"role": "system", "content": prompt},
                            {"role": "user", "content": texto}
                        ]
                    )
                    try:
                        resultado = resposta.choices[0].message.content
                        dados = eval(resultado)
                        for item in dados:
                            item["pagina"] = pagina_num
                            ocorrencias.append(item)
                    except Exception:
                        ocorrencias.append({
                            "pagina": pagina_num,
                            "categoria": "Erro de processamento",
                            "trecho": "—",
                            "sugestao": "—",
                            "justificativa": "Resposta da IA fora do formato esperado"
                        })

            total_time = time.time() - start_time
            st.success(f"Revisão concluída em {total_time:.1f} segundos.")

            # Relatório em Excel
            if ocorrencias:
                df = pd.DataFrame(ocorrencias)
                df["usuário"] = st.session_state["nome_usuario"]
                df["time"] = st.session_state["time"]
                df["projeto"] = st.session_state["projeto"]
                df["tempo_s"] = total_time
                df["custo_estimado_USD"] = len(texto_paginas) * 0.01  # exemplo
                st.dataframe(df, use_container_width=True)
                
                import io
                output = io.BytesIO()
                df.to_excel(output, index=False, engine="openpyxl")
                st.download_button(
                    "Baixar relatório em Excel",
                    data=output,
                    file_name="selo_ricca_relatorio.xlsx"
                )
            else:
                st.info("Nenhuma ocorrência identificada.")

pagina_revisao()
