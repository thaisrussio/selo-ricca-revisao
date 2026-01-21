import streamlit as st
import pdfplumber
import pandas as pd
import os
import time
from openai import OpenAI
import base64
import io
import json

# ============================================================
# CONFIGURAÇÕES DE PÁGINA E FONTE
# ============================================================
st.set_page_config(page_title="Selo Ricca de Revisão", layout="wide")

# ============================================================
# PATHS DE ASSETS (conforme fornecido)
# ============================================================
logo_dir = "assets/logo"
fonts_dir = "assets/fonts"
elementos_path = "assets/Elementos"

# ============================================================
# CARREGANDO FONTES AEONIK E CSS
# ============================================================
def load_fonts():
    # Paths para as fontes (conforme informado)
    regular = os.path.join(fonts_dir, "Aeonik-Regular.otf")
    medium = os.path.join(fonts_dir, "Aeonik-Medium.otf")
    bold = os.path.join(fonts_dir, "Aeonik-Bold.otf")

    font_css = """
    <style>
    @font-face {
        font-family: 'Aeonik';
        src: url('""" + regular + """') format('opentype');
        font-weight: 400;
    }
    @font-face {
        font-family: 'Aeonik';
        src: url('""" + medium + """') format('opentype');
        font-weight: 500;
    }
    @font-face {
        font-family: 'Aeonik';
        src: url('""" + bold + """') format('opentype');
        font-weight: 700;
    }
    html, body, .stApp, .main {
        font-family: 'Aeonik', sans-serif;
        background-color: #FFFFFF !important;
        color: #000000;
    }
    /* Botões magenta */
    div.stButton > button {
        background-color: #FF00FF;
        color: white;
        font-family: 'Aeonik', sans-serif !important;
        font-weight: 700;
        border-radius: 8px;
        padding: 0.5em 1.2em;
        font-size: 16px;
    }
    div.stButton > button:hover {
        background-color: #E600E6;
    }
    /* Selectboxes (filtro frágil: pode mudar com versões do Streamlit) */
    div[data-baseweb="select"] > div > div > div > div {
        background-color: #333333 !important;
        border-radius: 6px;
    }
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div[class*="value"] {
        color: white !important;
        font-family: 'Aeonik', sans-serif !important;
    }
    </style>
    """
    st.markdown(font_css, unsafe_allow_html=True)

load_fonts()

# ============================================================
# FUNÇÃO PARA DEFINIR FUNDO COM IMAGEM (base64)
# ============================================================
def set_background(image_filename: str, opacity: float = 1.0):
    img_path = os.path.join(elementos_path, image_filename)
    if not os.path.exists(img_path):
        # fallback: não interrompe, apenas avisa
        st.warning(f"Imagem de fundo {image_filename} não encontrada em assets/Elementos.")
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
        unsafe_allow_html=True,
    )

# ============================================================
# AUTENTICAÇÃO SIMPLES (fixa e obrigatória)
# ============================================================
HARDCODED_USER = "riccarevisao"
HARDCODED_PASS = "Ricc@2026!"

def login_page():
    set_background("Patterns Escuras-03.png", opacity=1)
    logo_vertical = os.path.join(logo_dir, "Vertical_Cor.png")
    if os.path.exists(logo_vertical):
        st.image(logo_vertical, width=300)
    st.title("Selo Ricca de Revisão")
    st.subheader("Login de acesso interno")

    user = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if user == HARDCODED_USER and password == HARDCODED_PASS:
            st.session_state["autenticado"] = True
            st.session_state["usuario"] = user
        else:
            st.error("Usuário ou senha incorretos.")

# inicializa session_state
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "login"
if "revisao_em_andamento" not in st.session_state:
    st.session_state["revisao_em_andamento"] = False

# Bloqueia acesso se não autenticado
if not st.session_state["autenticado"]:
    login_page()
    st.stop()

# ============================================================
# PÁGINA 2: INFORMAÇÕES INICIAIS
# ============================================================
def info_page():
    set_background("Patterns-06.png", opacity=1)
    logo_horizontal = os.path.join(logo_dir, "Horizontal_Cor.png")
    if os.path.exists(logo_horizontal):
        st.image(logo_horizontal, width=200)
    st.header("Informações do Projeto")

    # Preenche com valores existentes na sessão, se houver
    nome_usuario = st.text_input("Seu nome", value=st.session_state.get("nome_usuario", st.session_state.get("usuario", "")))
    projeto = st.text_input("Nome do projeto", value=st.session_state.get("projeto", ""))
    time_selecionado = st.selectbox("Time", ["Magenta", "Lilás", "Ouro", "Menta", "Patrulha", "Outro"], index=0 if st.session_state.get("time") is None else ["Magenta","Lilás","Ouro","Menta","Patrulha","Outro"].index(st.session_state.get("time")) if st.session_state.get("time") in ["Magenta","Lilás","Ouro","Menta","Patrulha","Outro"] else 5)

    st.info("Preencha os campos do projeto. O glossário será fornecido na página de revisão.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Próximo"):
            st.session_state["nome_usuario"] = nome_usuario
            st.session_state["projeto"] = projeto
            st.session_state["time"] = time_selecionado
            st.session_state["pagina"] = "revisao"
            st.experimental_rerun()

    with col2:
        # botão opcional para logout/limpar sessão mantendo login (útil em testes)
        if st.button("Logout"):
            for k in ["autenticado","usuario","nome_usuario","projeto","time","glossario","pagina","revisao_em_andamento"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.session_state["autenticado"] = False
            st.experimental_rerun()

# Se não estiver na página revisão, exibir info_page
if st.session_state.get("pagina") != "revisao":
    info_page()
    st.stop()

# ============================================================
# PÁGINA 3: REVISÃO (agora com glossário)
# ============================================================
def montar_prompt(glossario_cliente: str) -> str:
    return f"""
Você atuará como revisor(a) e analista de consistência editorial. Analise o texto SEM reescrevê-lo.
Forneça APENAS ocorrências de erros ou inconsistências.
Use apenas o glossário do cliente fornecido abaixo:

{glossario_cliente}

RETORNE SOMENTE JSON VÁLIDO, sem texto adicional nem explicações.

Formato de saída (JSON): lista de objetos; cada objeto com campos:
- pagina: número da página (inteiro)
- categoria: "Ortografia" | "Gramática" | "Numeração" | "Terminologia" | "Estilo" | "ODS" | "Elementos Visuais"
- trecho: trecho original
- sugestao: sugestão de correção
- justificativa: observação

Se não houver erros, retorne: "Nenhum erro identificado"
"""

def pagina_revisao():
    set_background("Patterns Escuras_Prancheta 1.png", opacity=1)
    logo_horizontal = os.path.join(logo_dir, "Horizontal_Cor.png")
    if os.path.exists(logo_horizontal):
        st.image(logo_horizontal, width=150)
    st.header("Revisão Ortográfica e Editorial")

    # Campo glossário na página 3 conforme solicitado
    st.header("Glossário do cliente (usar uma linha por regra)")
    st.info("Ex.: diretor = Diretor-Presidente")
    glossario = st.text_area("Glossário", value=st.session_state.get("glossario", ""), placeholder="empresa = Companhia\ncolaborador(a) = funcionário(a)\nEstado - ES = Estado (ES)")

    uploaded_file = st.file_uploader("Selecione o PDF", type=["pdf"])

    col_back, col_run = st.columns([1,1])
    with col_back:
        if st.button("Voltar"):
            # volta para página de informações
            st.session_state["pagina"] = "info"
            st.experimental_rerun()

    with col_run:
        iniciar = st.button("Iniciar Revisão")
        # Prevenção de múltiplos cliques: se já em andamento, bloqueia
        if iniciar and not st.session_state.get("revisao_em_andamento", False):
            # salva glossário em sessão
            st.session_state["glossario"] = glossario
            st.session_state["revisao_em_andamento"] = True

            start_time = time.time()
            texto_paginas = []

            with st.spinner("Extraindo texto..."):
                try:
                    with pdfplumber.open(uploaded_file) as pdf:
                        for i, page in enumerate(pdf.pages, start=1):
                            texto = page.extract_text() or ""
                            texto_paginas.append((i, texto))
                except Exception:
                    st.error("Erro ao extrair texto do PDF. Verifique o arquivo (talvez seja um PDF escaneado).")
                    st.session_state["revisao_em_andamento"] = False
                    return

            ocorrencias = []
            # Validação da chave de API (ainda usa OPENAI_API_KEY em st.secrets se disponível)
            api_key = st.secrets.get("OPENAI_API_KEY", None)
            if not api_key:
                st.error("OPENAI_API_KEY não configurada em st.secrets. Impossível continuar.")
                st.session_state["revisao_em_andamento"] = False
                return

            client = OpenAI(api_key=api_key)
            prompt = montar_prompt(st.session_state.get("glossario", ""))

            # Processamento por página com retries simples
            for pagina_num, texto in texto_paginas:
                with st.spinner(f"Revisão da página {pagina_num} em andamento..."):
                    tentativa = 0
                    sucesso = False
                    while tentativa < 3 and not sucesso:
                        tentativa += 1
                        try:
                            resposta = client.chat.completions.create(
                                model="gpt-4.1-mini",
                                temperature=0,
                                messages=[
                                    {"role": "system", "content": prompt},
                                    {"role": "user", "content": texto}
                                ],
                                # opcional: max_tokens, timeout
                            )
                            # Extrai conteúdo da resposta (compatibilidade)
                            try:
                                resultado = resposta.choices[0].message.content
                            except Exception:
                                resultado = getattr(resposta, "text", "") or ""

                            if not resultado:
                                raise ValueError("Resposta vazia")

                            # Tenta parse seguro
                            try:
                                dados = json.loads(resultado)
                            except json.JSONDecodeError:
                                # aceita string "Nenhum erro identificado"
                                cleaned = resultado.strip().strip('"').strip("'")
                                if cleaned == "Nenhum erro identificado":
                                    dados = []
                                else:
                                    # falha de parse: registra ocorrência e sai do loop
                                    ocorrencias.append({
                                        "pagina": pagina_num,
                                        "categoria": "Erro de processamento",
                                        "trecho": "—",
                                        "sugestao": "—",
                                        "justificativa": "Resposta da IA fora do formato JSON esperado"
                                    })
                                    sucesso = True
                                    break

                            # Se é string exata
                            if isinstance(dados, str) and dados == "Nenhum erro identificado":
                                sucesso = True
                                break

                            # Se lista, valida items
                            if isinstance(dados, list):
                                for item in dados:
                                    if isinstance(item, dict):
                                        # garante campos esperados
                                        item.setdefault("categoria", "Outro")
                                        item.setdefault("trecho", "—")
                                        item.setdefault("sugestao", "—")
                                        item.setdefault("justificativa", "—")
                                        item["pagina"] = pagina_num
                                        ocorrencias.append(item)
                                sucesso = True
                                break
                            else:
                                ocorrencias.append({
                                    "pagina": pagina_num,
                                    "categoria": "Erro de processamento",
                                    "trecho": "—",
                                    "sugestao": "—",
                                    "justificativa": "Formato de resposta inesperado (não lista)"
                                })
                                sucesso = True
                                break

                        except Exception:
                            # retry simples; se última tentativa, registra erro
                            if tentativa >= 3:
                                ocorrencias.append({
                                    "pagina": pagina_num,
                                    "categoria": "Erro de processamento",
                                    "trecho": "—",
                                    "sugestao": "—",
                                    "justificativa": "Erro na chamada à API"
                                })
                                sucesso = True
                                break
                            time.sleep(1 * tentativa)  # backoff simples

            total_time = time.time() - start_time
            st.success(f"Revisão concluída em {total_time:.1f} segundos.")
            st.session_state["revisao_em_andamento"] = False

            # Relatório em Excel
            if ocorrencias:
                df = pd.DataFrame(ocorrencias)
                df["usuário"] = st.session_state.get("nome_usuario", st.session_state.get("usuario", ""))
                df["time"] = st.session_state.get("time", "")
                df["projeto"] = st.session_state.get("projeto", "")
                df["tempo_s"] = total_time
                df["custo_estimado_USD"] = len(texto_paginas) * 0.01  # exemplo

                st.dataframe(df, use_container_width=True)

                output = io.BytesIO()
                df.to_excel(output, index=False, engine="openpyxl")
                output.seek(0)
                st.download_button(
                    "Baixar relatório em Excel",
                    data=output.getvalue(),
                    file_name="selo_ricca_relatorio.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.info("Nenhuma ocorrência identificada.")

# Executa a página de revisão
pagina_revisao()
