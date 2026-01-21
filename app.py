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
# CONFIGURAÇÕES INICIAIS
# ============================================================
st.set_page_config(page_title="Selo Ricca de Revisão", layout="wide", initial_sidebar_state="collapsed")

# ============================================================
# PATHS DE ASSETS (conforme informado)
# ============================================================
logo_dir = "assets/logo"
fonts_dir = "assets/fonts"
elementos_path = "assets/Elementos"

# ============================================================
# INJEÇÃO DE CSS GLOBAL (Aeonik aplicada amplamente)
# ============================================================
def inject_css():
    regular = os.path.join(fonts_dir, "Aeonik-Regular.otf")
    medium = os.path.join(fonts_dir, "Aeonik-Medium.otf")
    bold = os.path.join(fonts_dir, "Aeonik-Bold.otf")

    css = f"""
    <style>
    @font-face {{ font-family: 'Aeonik'; src: url('{regular}') format('opentype'); font-weight: 400; }}
    @font-face {{ font-family: 'Aeonik'; src: url('{medium}') format('opentype'); font-weight: 500; }}
    @font-face {{ font-family: 'Aeonik'; src: url('{bold}') format('opentype'); font-weight: 700; }}

    /* Aplicar Aeonik globalmente */
    html, body, .stApp, .main, .block-container, .element-container, .stTextInput, .stSelectbox, .stButton {{
        font-family: 'Aeonik', sans-serif !important;
        color: #000000 !important;
        background-color: #FFFFFF !important;
    }}

    /* Títulos e labels pretos e Aeonik Medium */
    .ricca-label {{
        font-family: 'Aeonik', sans-serif;
        font-weight: 500;
        color: #000000;
    }}

    /* Header página 1 e 3 */
    .ricca-h1 {{ font-family: 'Aeonik'; font-weight:700; font-size:32px; color:#000000; margin:0; }}
    .ricca-h3 {{ font-family: 'Aeonik'; font-weight:700; font-size:18px; color:#000000; margin:0; }}

    /* Botões principais (magenta) */
    div.stButton > button {{
        background-color: #FF00FF !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        padding: 0.5em 1.1em !important;
        font-size: 16px !important;
    }}
    div.stButton > button:hover {{ background-color: #E600E6 !important; }}

    /* Botões cinza (Logout/Voltar) - implementados como links estilizados */
    .ricca-btn-gray {{
        display: inline-block;
        background-color: #666666;
        color: #FFFFFF !important;
        padding: 0.45em 1em;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 500;
        font-family: 'Aeonik', sans-serif;
        font-size: 16px;
    }}
    .ricca-btn-gray:hover {{ background-color: #555555; }}

    /* Caixa de glossário magenta clarinho com texto magenta vivo */
    .glossary-box {{
        background-color: #FFE6FF; /* magenta clarinho */
        color: #FF00FF; /* magenta vivo */
        padding: 0.6rem;
        border-radius: 6px;
        font-family: 'Aeonik', sans-serif;
        font-weight: 500;
        font-size: 14px;
        margin-bottom: 8px;
    }}

    /* Background layer (aplicada por set_background) */
    .app-background {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: -1;
        background-size: cover;
        background-repeat: no-repeat;
        background-position: center;
    }}

    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

inject_css()

# ============================================================
# FUNÇÃO PARA DEFINIR BACKGROUND (BASE64)
# ============================================================
def set_background(image_filename: str, opacity: float = 1.0):
    img_path = os.path.join(elementos_path, image_filename)
    if not os.path.exists(img_path):
        # fallback leve: não interrompe, apenas registra
        st.markdown(f"<!-- Background {image_filename} não encontrado -->", unsafe_allow_html=True)
        return
    with open(img_path, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()
    st.markdown(
        f"""
        <style>
        .app-background {{
            background-image: url("data:image/png;base64,{encoded}");
            opacity: {opacity};
        }}
        </style>
        <div class="app-background"></div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# AÇÕES por query param (back/logout) — mantido como opção
# ============================================================
params = st.experimental_get_query_params()
if "action" in params:
    action = params.get("action")[0]
    if action == "back":
        st.session_state["pagina"] = "info"
        st.experimental_set_query_params()
        st.experimental_rerun()
    if action == "logout":
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.session_state["autenticado"] = False
        st.experimental_set_query_params()
        st.experimental_rerun()

# ============================================================
# AUTENTICAÇÃO FIXA (obrigatória)
# ============================================================
HARDCODED_USER = "riccarevisao"
HARDCODED_PASS = "Ricc@2026!"

def login_page():
    set_background("Patterns Escuras-03.png", opacity=1)
    logo_vertical = os.path.join(logo_dir, "Vertical_Cor.png")
    col_logo, col_empty = st.columns([1,3])
    with col_logo:
        if os.path.exists(logo_vertical):
            st.image(logo_vertical, width=260)
    with col_empty:
        pass

    # Título e subtítulo (substituído para "Login")
    st.markdown('<div class="ricca-h1">Selo Ricca de Revisão</div>', unsafe_allow_html=True)
    st.markdown('<div class="ricca-h3">Login</div>', unsafe_allow_html=True)

    # Form para permitir Enter
    with st.form("login_form"):
        st.markdown('<div class="ricca-label">Usuário</div>', unsafe_allow_html=True)
        user = st.text_input("", key="login_user", label_visibility="collapsed")
        st.markdown('<div class="ricca-label">Senha</div>', unsafe_allow_html=True)
        password = st.text_input("", type="password", key="login_pass", label_visibility="collapsed")
        submitted = st.form_submit_button("Entrar")
        if submitted:
            if user == HARDCODED_USER and password == HARDCODED_PASS:
                st.session_state["autenticado"] = True
                st.session_state["usuario"] = user
                st.session_state["pagina"] = "info"
                st.experimental_rerun()
            else:
                st.error("Usuário ou senha incorretos.")

# ============================================================
# Inicializa session_state
# ============================================================
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "login"
if "revisao_em_andamento" not in st.session_state:
    st.session_state["revisao_em_andamento"] = False
# campos persistentes
for key in ["nome_usuario","projeto","time","glossario"]:
    if key not in st.session_state:
        st.session_state[key] = ""

# Bloqueia acesso se não autenticado
if not st.session_state["autenticado"]:
    login_page()
    st.stop()

# ============================================================
# PÁGINA 2: INFORMAÇÕES (sem texto instrucional extra)
# ============================================================
def info_page():
    set_background("Patterns-06.png", opacity=1)
    logo_horizontal = os.path.join(logo_dir, "Horizontal_Cor.png")
    col_logo, col_form = st.columns([1,3])
    with col_logo:
        if os.path.exists(logo_horizontal):
            st.image(logo_horizontal, width=160)

    # Form (permite Enter para avançar)
    with st.form("info_form"):
        st.markdown('<div class="ricca-label">Seu nome</div>', unsafe_allow_html=True)
        nome_usuario = st.text_input("", value=st.session_state.get("nome_usuario", ""), key="nome_input", label_visibility="collapsed")
        st.markdown('<div class="ricca-label">Projeto</div>', unsafe_allow_html=True)
        projeto = st.text_input("", value=st.session_state.get("projeto", ""), key="projeto_input", label_visibility="collapsed")
        st.markdown('<div class="ricca-label">Time</div>', unsafe_allow_html=True)
        times = ["Magenta", "Lilás", "Ouro", "Menta", "Patrulha", "Outro"]
        default_index = times.index(st.session_state.get("time")) if st.session_state.get("time") in times else 0
        time_selecionado = st.selectbox("", options=times, index=default_index, key="time_select", label_visibility="collapsed")

        # Botões: Logout (esquerda, cinza) e Próximo (direita, magenta)
        colL, colR = st.columns([1,1])
        with colL:
            logout_link = '<a class="ricca-btn-gray" href="?action=logout">Logout</a>'
            st.markdown(logout_link, unsafe_allow_html=True)
        with colR:
            if st.form_submit_button("Próximo"):
                st.session_state["nome_usuario"] = nome_usuario
                st.session_state["projeto"] = projeto
                st.session_state["time"] = time_selecionado
                st.session_state["pagina"] = "revisao"
                st.experimental_rerun()

# Se a página atual não for revisão, mostra info_page
if st.session_state.get("pagina") != "revisao":
    info_page()
    st.stop()

# ============================================================
# PÁGINA 3: REVISÃO (Glossário, uploader, botões com posições corretas)
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
    col_logo, col_main = st.columns([1,3])
    with col_logo:
        if os.path.exists(logo_horizontal):
            st.image(logo_horizontal, width=160)

    # Header maior e bold
    st.markdown('<div class="ricca-h1">Revisão Ortográfica e Editorial</div>', unsafe_allow_html=True)

    # Espaço
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Caixa de glossário estilizada (magenta clarinho com texto magenta vivo)
    st.markdown('<div class="glossary-box">Ricca, aqui você deve inserir os padrões do cliente, com uma regra por linha.<br>Ex.:<br>diretor = Diretor-Presidente<br>empresa = Companhia<br>funcionários = colaboradores</div>', unsafe_allow_html=True)
    gloss = st.text_area("", value=st.session_state.get("glossario", ""), key="gloss_input", height=140, label_visibility="collapsed")
    st.session_state["glossario"] = gloss

    # Espaçamento entre glossário e uploader
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Selecione o PDF", type=["pdf"])

    # Botões: Voltar (esquerda, embaixo) e Iniciar Revisão (direita, embaixo)
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    col_left, col_right = st.columns([1,1])
    with col_left:
        back_link = '<a class="ricca-btn-gray" href="?action=back">Voltar</a>'
        st.markdown(back_link, unsafe_allow_html=True)
    with col_right:
        if st.session_state.get("revisao_em_andamento", False):
            st.warning("Revisão em andamento. Aguarde conclusão.")
        else:
            if uploaded_file and st.button("Iniciar revisão"):
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
                api_key = st.secrets.get("OPENAI_API_KEY", None)
                if not api_key:
                    st.error("OPENAI_API_KEY não configurada em st.secrets. Impossível continuar.")
                    st.session_state["revisao_em_andamento"] = False
                    return

                client = OpenAI(api_key=api_key)
                prompt = montar_prompt(st.session_state.get("glossario", ""))

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
                                )
                                try:
                                    resultado = resposta.choices[0].message.content
                                except Exception:
                                    resultado = getattr(resposta, "text", "") or ""

                                if not resultado:
                                    raise ValueError("Resposta vazia")

                                try:
                                    dados = json.loads(resultado)
                                except json.JSONDecodeError:
                                    cleaned = resultado.strip().strip('"').strip("'")
                                    if cleaned == "Nenhum erro identificado":
                                        dados = []
                                    else:
                                        ocorrencias.append({
                                            "pagina": pagina_num,
                                            "categoria": "Erro de processamento",
                                            "trecho": "—",
                                            "sugestao": "—",
                                            "justificativa": "Resposta da IA fora do formato JSON esperado"
                                        })
                                        sucesso = True
                                        break

                                if isinstance(dados, str) and dados == "Nenhum erro identificado":
                                    sucesso = True
                                    break

                                if isinstance(dados, list):
                                    for item in dados:
                                        if isinstance(item, dict):
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
                                time.sleep(1 * tentativa)

                total_time = time.time() - start_time
                st.success(f"Revisão concluída em {total_time:.1f} segundos.")
                st.session_state["revisao_em_andamento"] = False

                if ocorrencias:
                    df = pd.DataFrame(ocorrencias)
                    df["usuário"] = st.session_state.get("nome_usuario", st.session_state.get("usuario", ""))
                    df["time"] = st.session_state.get("time", "")
                    df["projeto"] = st.session_state.get("projeto", "")
                    df["tempo_s"] = total_time
                    df["custo_estimado_USD"] = len(texto_paginas) * 0.01
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

# Executa página de revisão
pagina_revisao()
