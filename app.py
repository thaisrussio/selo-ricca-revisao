import streamlit as st
from PIL import Image
import os
import pdfplumber
import pandas as pd
from openai import OpenAI
import time
from io import BytesIO

# ============================================================
# Configuração de página
# ============================================================
st.set_page_config(page_title="Selo Ricca de Revisão", layout="wide")

# ============================================================
# Caminhos
# ============================================================
assets_path = "assets"

logo_path = os.path.join(assets_path, "logo.png")
fonts_path = os.path.join(assets_path, "fonts")
elementos_path = os.path.join(assets_path, "Elementos")

# ============================================================
# CSS
# ============================================================
st.markdown(
    f"""
    <style>
    @font-face {{
        font-family: 'Aeonik';
        src: url('{fonts_path}/Aeonik-Regular.otf') format('opentype');
        font-weight: normal;
    }}
    @font-face {{
        font-family: 'Aeonik';
        src: url('{fonts_path}/Aeonik-Bold.otf') format('opentype');
        font-weight: bold;
    }}
    @font-face {{
        font-family: 'Aeonik';
        src: url('{fonts_path}/Aeonik-Medium.otf') format('opentype');
        font-weight: 500;
    }}

    html, body, [class*="css"] {{
        font-family: 'Aeonik', sans-serif;
    }}

    /* Botão magenta */
    div.stButton > button {{
        background-color: #FFF;
        color: white;
        font-weight: bold;
        font-family: 'Aeonik', sans-serif;
        padding: 10px 24px;
        border-radius: 8px;
    }}
    
    div.stButton > button:active {{
        background-color: #CC00CC;
        transform: scale(0.98);
    }}

    .background-image {{
        position: fixed;
        top: 0;
        left: 0;
        width: auto;
        height: auto;
        pointer-events: none;
        z-index: -1;
    
        opacity: 0.5;
    }}
    </style>
    <img src="{bg_image}" class="bg-layer">
    """,
    unsafe_allow_html=True
)

# ============================================================
# Função para carregar imagens
# ============================================================
def load_image(subfolder, filename):
    if subfolder == "Elementos":
        path = os.path.join(elementos_path, filename)
    elif subfolder == "logo":
        path = os.path.join(logo_path, filename)
    else:
        path = os.path.join(assets_path, filename)
    return Image.open(path)

# ============================================================
# Páginas
# ============================================================

def login_page():
    st.title("Selo Ricca de Revisão")
    # Logo centralizado
    logo = load_image("logo", "Vertical_Cor.png")
    st.image(logo, use_column_width=False, width=300)

    # Background
    bg = load_image("Elementos", "Patterns Escuras-03.png")
    st.image(bg, use_column_width=True, output_format="PNG", clamp=True)

    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    
    if st.button("Próximo"):
        if username == "riccarevisao" and password == "Ricc@2026!":
            st.session_state.authenticated = True
            st.session_state.page = 2
        else:
            st.error("Usuário ou senha incorretos")

def info_page():
    st.header("Preencha as informações do projeto")
    
    # Background
    bg = load_image("Elementos", "Patterns-06.png")
    st.image(bg, use_column_width=True, output_format="PNG", clamp=True)
    
    st.session_state.nome = st.text_input("Seu nome")
    st.session_state.projeto = st.text_input("Projeto")
    st.session_state.time = st.selectbox("Time", ["Magenta", "Lilás", "Ouro", "Menta", "Patrulha", "Outro"])
    
    st.session_state.glosario = st.text_area("Glossário do cliente (ex.: diretor = Diretor-Presidente)")

    if st.button("Próximo"):
        st.session_state.page = 3

def revisao_page():
    st.header("Selo Ricca de Revisão")
    
    # Background
    bg = load_image("Elementos", "Patterns Escuras_Prancheta 1.png")
    st.image(bg, use_column_width=True, output_format="PNG", clamp=True)
    
    # Logo horizontal
    logo = load_image("logo", "Horizontal_Cor.png")
    st.image(logo, width=200)
    
    uploaded_file = st.file_uploader("Selecione o arquivo PDF", type=["pdf"])
    
    if uploaded_file and st.button("Iniciar Revisão"):
        start_time = time.time()
        with st.spinner("Extraindo texto..."):
            time.sleep(1)  # simulação
            # Extração de texto
            texto_paginas = []
            with pdfplumber.open(uploaded_file) as pdf:
                for i, page in enumerate(pdf.pages, start=1):
                    texto_paginas.append((i, page.extract_text() or ""))
        
        with st.spinner("Revisão em andamento, aguarde mais um pouquinho..."):
            time.sleep(1)  # simulação
            # Aqui entraria a chamada da OpenAI API
            ocorrencias = []
            for i, texto in texto_paginas:
                ocorrencias.append({
                    "pagina": i,
                    "categoria": "Ortografia",
                    "trecho": "Exemplo de trecho",
                    "sugestao": "Exemplo de correção",
                    "justificativa": "Teste"
                })
        
        with st.spinner("Gerando relatório de erros..."):
            time.sleep(1)
            end_time = time.time()
            duracao = round(end_time - start_time, 2)
            
            df = pd.DataFrame(ocorrencias)
            # Adiciona info do usuário e projeto
            df["Usuário"] = st.session_state.nome
            df["Projeto"] = st.session_state.projeto
            df["Time"] = st.session_state.time
            df["Tempo de revisão (s)"] = duracao
            df["Custo estimado (USD)"] = round(duracao * 0.01, 2)  # exemplo custo
            
            st.success("Revisão concluída. Relatório gerado.")
            st.dataframe(df)
            
            # Download Excel
            output = BytesIO()
            df.to_excel(output, index=False, engine="openpyxl")
            st.download_button("Baixar relatório em Excel", data=output, file_name="selo_ricca_relatorio.xlsx")

# ============================================================
# Inicialização
# ============================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.page = 1
    st.session_state.nome = ""
    st.session_state.projeto = ""
    st.session_state.time = ""
    st.session_state.glosario = ""

# Controle de páginas
if not st.session_state.authenticated:
    login_page()
else:
    if st.session_state.page == 2:
        info_page()
    elif st.session_state.page == 3:
        revisao_page()
