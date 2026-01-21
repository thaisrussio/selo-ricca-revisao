import streamlit as st
import pdfplumber
import pandas as pd
from openai import OpenAI
import io

# ============================================================
# CONFIGURAÇÕES INICIAIS
# ============================================================
st.set_page_config(page_title="Selo Ricca de Revisão", layout="wide")

# Estilo CSS
st.markdown(
    """
    <style>
    @font-face {
        font-family: "Aeonik";
        src: url("assets/fonts/Aeonik-Regular.ttf") format("truetype");
        font-weight: 400;
    }
    @font-face {
        font-family: "Aeonik";
        src: url("assets/fonts/Aeonik-Medium.ttf") format("truetype");
        font-weight: 500;
    }
    @font-face {
        font-family: "Aeonik";
        src: url("assets/fonts/Aeonik-Bold.ttf") format("truetype");
        font-weight: 700;
    }
    html, body, [class*="css"]  {
        font-family: "Aeonik", sans-serif;
        background-color: #FFFFFF;
        color: #1B1B1B;
    }
    .stButton>button {
        background-color: #E6007E;
        color: white;
        font-weight: 700;
        border-radius: 10px;
        padding: 10px 20px;
        border: none;
    }
    .stTextInput>div>input, .stSelectbox>div>div>div>input, .stTextArea>div>textarea {
        border-radius: 5px;
        border: 1px solid #ccc;
        padding: 8px;
    }
    </style>
    """, unsafe_allow_html=True
)

# ============================================================
# SESSÃO STATE
# ============================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "project" not in st.session_state:
    st.session_state.project = ""
if "team" not in st.session_state:
    st.session_state.team = ""
if "ready_to_review" not in st.session_state:
    st.session_state.ready_to_review = False
if "ready_to_process" not in st.session_state:
    st.session_state.ready_to_process = False

# ============================================================
# FUNÇÃO DE LOGIN
# ============================================================
def login():
    st.image("assets/logo.png/Vertical_Cor.png", width=150)
    st.title("Selo Ricca de Revisão - Login")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if username == "riccarevisao" and password == "Ricc@2026!":
            st.session_state.authenticated = True
            st.success("Login realizado com sucesso!")
        else:
            st.error("Usuário ou senha incorretos")

# ============================================================
# PÁGINA INICIAL (APÓS LOGIN)
# ============================================================
def pagina_inicial():
    st.image("assets/logo.png/Vertical_Cor.png", width=150)
    st.title("Selo Ricca de Revisão")
    st.subheader("Informações do usuário e projeto")

    st.session_state.user_name = st.text_input("Seu nome", value=st.session_state.user_name)
    st.session_state.project = st.text_input("Projeto", value=st.session_state.project)
    st.session_state.team = st.selectbox(
        "Time",
        ["Magenta", "Lilás", "Ouro", "Menta", "Patrulha", "Outro"],
        index=0
    )

    if st.button("Continuar"):
        if st.session_state.user_name.strip() == "" or st.session_state.project.strip() == "":
            st.warning("Preencha nome e projeto antes de continuar")
        else:
            st.session_state.ready_to_review = True

# ============================================================
# PÁGINA DE REVISÃO
# ============================================================
def pagina_revisao():
    st.image("assets/logo.png/Vertical_Cor.png", width=150)
    st.subheader(f"Usuário: {st.session_state.user_name} | Projeto: {st.session_state.project} | Time: {st.session_state.team}")

    st.info(
        "Faça upload de PDFs curtos para revisão. O relatório será gerado em Excel com ocorrências encontradas."
    )

    # Campos de padrões do cliente
    st.header("Padrões do Cliente")
    termo_instituicao = st.text_input("Termo para a instituição", placeholder="ex.: organização")
    termo_equipe = st.text_input("Termo para a equipe", placeholder="ex.: colaboradores")
    tom_texto = st.selectbox("Tom do texto", ["Sóbrio e institucional", "Técnico", "Leve e otimista", "Resiliente e de superação"])
    diretrizes = st.text_area("Outras diretrizes de linguagem", placeholder="Ex.: evitar voz passiva")
    glossario = st.text_area("Glossário do cliente (uma regra por linha: termo incorreto = termo correto)")

    uploaded_file = st.file_uploader("Selecione o arquivo PDF", type=["pdf"])

    # Botão único para iniciar revisão
    if uploaded_file and st.button("Iniciar revisão"):
        st.session_state.ready_to_process = True

    # Processamento da revisão
    if uploaded_file and st.session_state.ready_to_process:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

        padroes = {
            "instituicao": termo_instituicao or "não definido",
            "equipe": termo_equipe or "não definido",
            "tom": tom_texto,
            "diretrizes": diretrizes or "nenhuma",
            "glossario": glossario or "não informado"
        }

        prompt_sistema = f"""
Você é um revisor editorial profissional especializado em relatórios institucionais
em português do Brasil.

TAREFA:
Analise o texto fornecido SEM reescrevê-lo.

REGRAS OBRIGATÓRIAS:
1. Não reescreva o texto.
2. Não devolva o texto corrigido.
3. Apenas identifique e liste ocorrências de erro ou inconsistência.
4. Caso não haja erros, informe explicitamente: "Texto em conformidade".

PADRÕES DO CLIENTE:
- Termo para instituição: {padroes['instituicao']}
- Termo para equipe: {padroes['equipe']}
- Tom do texto: {padroes['tom']}
- Diretrizes adicionais: {padroes['diretrizes']}
- Glossário: {padroes['glossario']}

FORMATO DE SAÍDA (OBRIGATÓRIO – JSON):
[
  {{
    "pagina": "número da página",
    "categoria": "Ortografia | Gramática | Numeração | Terminologia | Estilo | ODS | Elementos Visuais",
    "trecho": "trecho original",
    "sugestao": "sugestão de correção",
    "justificativa": "fundamentação técnica"
  }}
]
"""

        ocorrencias = []

        with st.spinner("Revisão em andamento, por favor aguarde..."):
            with pdfplumber.open(uploaded_file) as pdf:
                for i, page in enumerate(pdf.pages, start=1):
                    texto = page.extract_text()
                    if not texto:
                        continue

                    resposta = client.chat.completions.create(
                        model="gpt-4.1-mini",
                        temperature=0,
                        messages=[
                            {"role": "system", "content": prompt_sistema},
                            {"role": "user", "content": texto}
                        ]
                    )

                    try:
                        resultado = resposta.choices[0].message.content
                        dados = eval(resultado)
                        for item in dados:
                            item["pagina"] = i
                            ocorrencias.append(item)
                    except Exception:
                        ocorrencias.append({
                            "pagina": i,
                            "categoria": "Erro de processamento",
                            "trecho": "—",
                            "sugestao": "—",
                            "justificativa": "Resposta da IA fora do formato esperado"
                        })

        # Resultado
        if ocorrencias:
            df = pd.DataFrame(ocorrencias)
            st.success("Revisão concluída. Relatório gerado.")
            st.dataframe(df, use_container_width=True)

            # Download Excel
            output = io.BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            st.download_button(
                "Baixar relatório em Excel",
                data=output,
                file_name=f"{st.session_state.project}_relatorio_revisao.xlsx"
            )
        else:
            st.info("Nenhuma ocorrência identificada. Texto em conformidade.")

# ============================================================
# FLUXO PRINCIPAL
# ============================================================
if not st.session_state.authenticated:
    login()
elif st.session_state.authenticated and not st.session_state.ready_to_review:
    pagina_inicial()
else:
    pagina_revisao()
