import streamlit as st
from PIL import Image
import pdfplumber
import pandas as pd
from openai import OpenAI
import os
import time

# ======================
# CONFIGURAÇÃO DO STREAMLIT
# ======================
st.set_page_config(page_title="Selo Ricca de Revisão", layout="wide")

# Caminhos de assets
assets_path = os.path.join(os.getcwd(), "assets")
logo_path = os.path.join(assets_path, "logo.png")
fonts_path = os.path.join(assets_path, "fonts")
Elementos_path = os.path.join(assets_path, "Elementos")

# Função para carregar imagens
def load_image(subfolder, filename):
    return Image.open(os.path.join(Elementos_path if subfolder=="Elementos" else logo_path, filename))

# ======================
# FONTE AEONIK
# ======================
st.markdown(
    f"""
    <style>
    @font-face {{
        font-family: 'Aeonik';
        src: url('{os.path.join(fonts_path,'Aeonik-Regular.otf')}') format('opentype');
        font-weight: normal;
    }}
    @font-face {{
        font-family: 'Aeonik';
        src: url('{os.path.join(fonts_path,'Aeonik-Bold.otf')}') format('opentype');
        font-weight: bold;
    }}
    @font-face {{
        font-family: 'Aeonik';
        src: url('{os.path.join(fonts_path,'Aeonik-Medium.otf')}') format('opentype');
        font-weight: 500;
    }}
    html, body, [class*="css"] {{
        font-family: 'Aeonik', sans-serif;
    }}
    .stApp {{
        background-color: #FFF;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ======================
# LOGIN
# ======================
def login_page():
    pattern_bg = load_image("Elementos", "Patterns Escuras-03.png")
    logo = load_image("", "Vertical_Cor.png")
    st.image(logo, width=300)
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("file://{os.path.join(Elementos_path,'Patterns Escuras-03.png')}");
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center;
            background-color: #FFF;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    st.subheader("Login Selo Ricca de Revisão")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if username == "riccarevisao" and password == "Ricc@2026!":
            st.session_state["authenticated"] = True
            st.session_state["user"] = username
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha incorretos.")

# ======================
# PREENCHIMENTO DE INFORMAÇÕES
# ======================
def info_page():
    pattern_bg = load_image("Elementos", "Patterns-06.png")
    st.image(pattern_bg, use_column_width=True)

    st.header("Informações do Projeto")
    st.text_input("Seu nome", key="nome_usuario")
    st.text_input("Projeto", key="nome_projeto")
    st.selectbox("Time", ["Magenta", "Lilás", "Ouro", "Menta", "Patrulha", "Outro"], key="time_projeto")

    st.header("Glossário do Cliente (exemplo)")
    st.text_area("Preencha o glossário", value="diretor = Diretor-Presidente\nempresa = Companhia", key="glossario")

    if st.button("Próximo"):
        st.session_state["info_filled"] = True
        st.experimental_rerun()

# ======================
# PÁGINA DE REVISÃO
# ======================
def review_page():
    pattern_bg = load_image("Elementos", "Patterns Escuras_Prancheta 1.png")
    logo = load_image("", "Horizontal_Cor.png")
    st.image(logo, width=200)

    st.header("Selo Ricca de Revisão - Revisão de PDF")
    uploaded_file = st.file_uploader("Selecione o arquivo PDF", type=["pdf"])

    if uploaded_file:
        start_time = time.time()
        with st.spinner("Extraindo texto do PDF..."):
            time.sleep(1)

        # =====================================
        # Inicializar cliente OpenAI
        # =====================================
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

        padroes = {
            "glossario": st.session_state.get("glossario", "")
        }

        ocorrencias = []

        with pdfplumber.open(uploaded_file) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                texto = page.extract_text() or ""
                with st.spinner(f"Revisão em andamento (Página {i}/{len(pdf.pages)})..."):
                    time.sleep(1)

                prompt = f"""
                Você é um revisor editorial. NÃO REESCREVA o texto.
                Analise e liste apenas erros seguindo o glossário do cliente:
                {padroes['glossario']}
                Forneça saída em JSON com: pagina, trecho, sugestao, tipo de erro, observacao
                Texto: {texto}
                """

                resposta = client.chat.completions.create(
                    model="gpt-4.1-mini",
                    temperature=0,
                    messages=[{"role":"system","content":prompt}]
                )

                try:
                    dados = eval(resposta.choices[0].message.content)
                    for item in dados:
                        item["pagina"] = i
                        ocorrencias.append(item)
                except:
                    ocorrencias.append({
                        "pagina": i,
                        "tipo de erro": "Erro de processamento",
                        "trecho": "—",
                        "sugestao": "—",
                        "observacao": "Resposta da IA fora do formato esperado"
                    })

        duration = round(time.time() - start_time, 2)

        if ocorrencias:
            df = pd.DataFrame(ocorrencias)
            df["Usuário"] = st.session_state.get("user", "")
            df["Projeto"] = st.session_state.get("nome_projeto", "")
            df["Time"] = st.session_state.get("time_projeto", "")
            df["Tempo (s)"] = duration
            df["Custo Estimado (USD)"] = round(duration * 0.0005, 4)  # exemplo custo

            st.success(f"Revisão concluída em {duration}s. Relatório gerado.")
            st.dataframe(df, use_container_width=True)

            output_path = "selo_ricca_relatorio.xlsx"
            df.to_excel(output_path, index=False, engine='openpyxl')

            st.download_button(
                "Baixar relatório em Excel",
                data=open(output_path, "rb").read(),
                file_name="selo_ricca_relatorio.xlsx"
            )
        else:
            st.info("Nenhuma ocorrência identificada. Texto em conformidade.")

# ======================
# CONTROLE DE PÁGINAS
# ======================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login_page()
elif not st.session_state.get("info_filled", False):
    info_page()
else:
    review_page()
