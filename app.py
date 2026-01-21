import streamlit as st
from PIL import Image
import pdfplumber
import pandas as pd
from openai import OpenAI
import time
import os

# ========================================
# CONFIGURAÇÕES INICIAIS
# ========================================
st.set_page_config(page_title="Selo Ricca de Revisão", layout="wide")

# Caminhos
logo_path = "assets/logo.png"
elementos_path = "assets/Elementos"
fonts_path = "assets/fonts"

# Fonte Aeonik
st.markdown(
    f"""
    <style>
    @font-face {{
        font-family: 'Aeonik';
        src: url('{fonts_path}/Aeonik-Regular.otf');
        font-weight: normal;
    }}
    @font-face {{
        font-family: 'Aeonik';
        src: url('{fonts_path}/Aeonik-Bold.otf');
        font-weight: bold;
    }}
    @font-face {{
        font-family: 'Aeonik';
        src: url('{fonts_path}/Aeonik-Medium.otf');
        font-weight: 500;
    }}
    html, body, [class*="css"] {{
        font-family: 'Aeonik', sans-serif;
    }}
    .stButton>button {{
        background-color: #FF00FF;
        color: white;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ========================================
# FUNÇÃO PARA FUNDO DE TELA (CAMADA ATRÁS)
# ========================================
def set_background(image_filename, opacity=0.5):
    img_path = os.path.join(elementos_path, image_filename)
    st.markdown(
        f"""
        <style>
        .bg-layer {{
            position: fixed;
            top: 0;
            left: 0;
            width: auto;
            height: auto;
            z-index: -1;
            pointer-events: none;
            opacity: 0,5;
        }}
        </style>
        <img src="{img_path}" class="bg-layer">
        """,
        unsafe_allow_html=True
    )

# ========================================
# PÁGINA DE LOGIN
# ========================================
def login_page():
    set_background("Patterns Escuras-03.png", opacity=0.6)
    st.image(f"{logo_path}/Vertical_Cor.png", width=300)

    st.subheader("Login Selo Ricca de Revisão")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if username == "riccarevisao" and password == "Ricc@2026!":
            st.session_state["logged_in"] = True
        else:
            st.error("Usuário ou senha incorretos")

# ========================================
# PÁGINA DE INFORMAÇÕES INICIAIS
# ========================================
def info_page():
    set_background("Patterns-06.png", opacity=0.5)
    st.image(f"{logo_path}/Horizontal_Cor.png", width=200)

    st.header("Informações do Projeto")
    st.text_input("Seu nome", key="nome")
    st.text_input("Projeto", key="projeto")
    st.selectbox(
        "Time", 
        ["Magenta", "Lilás", "Ouro", "Menta", "Patrulha", "Outro"],
        key="time"
    )
    st.text_area(
        "Glossário do cliente (Ex.: diretor = Diretor-Presidente)",
        key="glossario",
        height=100
    )

    if st.button("Próximo"):
        st.session_state["page"] = "revisao"

# ========================================
# PÁGINA DE REVISÃO
# ========================================
def revisao_page():
    set_background("Patterns Escuras_Prancheta 1.png", opacity=0.4)
    st.image(f"{logo_path}/Horizontal_Cor.png", width=200)

    st.header("Revisão Ortográfica")
    uploaded_file = st.file_uploader("Selecione o PDF", type=["pdf"])

    if uploaded_file:
        if st.button("Iniciar Revisão"):
            start_time = time.time()
            with st.spinner("Extraindo texto do PDF..."):
                pages_text = []
                with pdfplumber.open(uploaded_file) as pdf:
                    for i, page in enumerate(pdf.pages, start=1):
                        text = page.extract_text()
                        pages_text.append((i, text))
                time.sleep(1)

            with st.spinner("Revisão em andamento, aguarde mais um pouquinho..."):
                client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                ocorrencias = []
                for i, text in pages_text:
                    # Prompt simplificado: usar o glossário do cliente
                    glossario = st.session_state.get("glossario", "")
                    prompt = f"""
Você é revisor profissional. Não reescreva o texto. Use apenas o glossário abaixo.
Glossário:
{glossario}
Texto:
{text}
Saída em JSON com campos: página, trecho, sugestão, tipo, observação
"""
                    response = client.chat.completions.create(
                        model="gpt-4.1-mini",
                        temperature=0,
                        messages=[
                            {"role": "system", "content": prompt},
                        ]
                    )
                    try:
                        resultado = eval(response.choices[0].message.content)
                        for item in resultado:
                            item["pagina"] = i
                            ocorrencias.append(item)
                    except Exception:
                        ocorrencias.append({
                            "pagina": i,
                            "trecho": "—",
                            "sugestao": "—",
                            "tipo": "Erro de processamento",
                            "observacao": "Resposta da IA fora do formato esperado"
                        })
                time.sleep(1)

            with st.spinner("Gerando relatório de erros..."):
                df = pd.DataFrame(ocorrencias)
                end_time = time.time()
                df["tempo_segundos"] = round(end_time - start_time, 2)
                df["nome"] = st.session_state.get("nome", "")
                df["projeto"] = st.session_state.get("projeto", "")
                df["time"] = st.session_state.get("time", "")
                st.success("Revisão concluída. Relatório gerado.")
                st.dataframe(df)

                # Baixar Excel
                output_file = "relatorio_revisao.xlsx"
                df.to_excel(output_file, index=False, engine='openpyxl')
                st.download_button(
                    "Baixar relatório em Excel",
                    data=open(output_file, "rb"),
                    file_name=output_file
                )

# ========================================
# CONTROLE DE PÁGINAS
# ========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "page" not in st.session_state:
    st.session_state["page"] = "login"

if not st.session_state["logged_in"]:
    login_page()
else:
    if st.session_state["page"] == "info":
        info_page()
    elif st.session_state["page"] == "revisao":
        revisao_page()
