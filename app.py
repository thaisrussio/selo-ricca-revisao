# app.py (substituir arquivo existente pelo conteúdo abaixo)
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
# CONFIGURAÇÃO
# ============================================================
st.set_page_config(page_title="Selo Ricca de Revisão", layout="wide")

# PATHS (confirmados por você)
logo_dir = "assets/logo"
fonts_dir = "assets/fonts"
elementos_path = "assets/Elementos"   # CORREÇÃO: nome consistente

# ============================================================
# INJEÇÃO DE CSS / FONTE (Aeonik aplicada globalmente)
# ============================================================
def inject_css():
    regular = os.path.join(fonts_dir, "Aeonik-Regular.otf")
    medium = os.path.join(fonts_dir, "Aeonik-Medium.otf")
    bold = os.path.join(fonts_dir, "Aeonik-Bold.otf")

    css = f"""
    <style>
    @font-face {{font-family: 'Aeonik'; src: url('{regular}') format('opentype'); font-weight: 400;}}
    @font-face {{font-family: 'Aeonik'; src: url('{medium}') format('opentype'); font-weight: 500;}}
    @font-face {{font-family: 'Aeonik'; src: url('{bold}') format('opentype'); font-weight: 700;}}

    /* Aplicar Aeonik globalmente */
    html, body, .stApp, .block-container, .css-1d391kg, .element-container, .stTextArea textarea, input, select, textarea, button {{
        font-family: 'Aeonik', sans-serif !important;
        color: #000000 !important;
    }}

    /* Botões (todos magenta com texto branco, Aeonik Medium 16px) */
    div.stButton > button {{
        background-color: #FF00FF !important;
        color: #FFFFFF !important;
        font-family: 'Aeonik' !important;
        font-weight: 500 !important;
        font-size: 16px !important;
        border-radius: 8px !important;
        padding: 0.5em 1.0em !important;
    }}

    /* Botões cinza (logout/voltar) — aplicamos mesma aparência para simplificar */
    .ricca-btn-gray {{
        background-color: #666666 !important;
        color: #FFFFFF !important;
        font-family: 'Aeonik' !important;
        font-weight: 500 !important;
        font-size: 16px !important;
        border-radius: 8px !important;
        padding: 0.45em 1.0em !important;
    }}

    /* Selectbox visual (tentativa de aplicar cor fundo; pode depender da versão do Streamlit) */
    div[data-baseweb="select"] > div > div > div > div {{
        background-color: #333333 !important;
        border-radius: 6px !important;
    }}
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div[class*="value"] {{
        color: white !important;
        font-family: 'Aeonik' !important;
    }}

    /* Header grande para página 3 */
    .ricca-header-3 {{
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 4px;
    }}

    /* Glossário box */
    .ricca-gloss-box {{
        background-color: #FFE6FF;
        color: #FF00FF;
        padding: 10px;
        border-radius: 8px;
        font-weight: 500;
    }}

    /* background container */
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
# FUNÇÃO DE BACKGROUND (usa elementos_path corretamente)
# ============================================================
def set_background(image_filename: str, opacity: float = 1.0):
    img_path = os.path.join(elementos_path, image_filename)
    if not os.path.exists(img_path):
        # não para o app; só avisa e retorna
        st.markdown(f"<!-- background {image_filename} não encontrado -->", unsafe_allow_html=True)
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
# AUTENTICAÇÃO (fixa, simples e obrigatória)
# ============================================================
HARDCODED_USER = "riccarevisao"
HARDCODED_PASS = "Ricc@2026!"

def page_login():
    set_background("Patterns Escuras-03.png", opacity=1)
    # logo vertical à esquerda, grande
    logo_vertical = os.path.join(logo_dir, "Vertical_Cor.png")
    cols = st.columns([1,3])
    with cols[0]:
        if os.path.exists(logo_vertical):
            st.image(logo_vertical, width=260)
    with cols[1]:
        # Título único e "Login" como subtítulo
        st.markdown("<div style='font-family:Aeonik;font-weight:700;font-size:32px;color:#000000'>Selo Ricca de Revisão</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-family:Aeonik;font-weight:700;font-size:18px;color:#000000;margin-top:6px'>Login</div>", unsafe_allow_html=True)

    # formulário para permitir submit com Enter
    with st.form("login_form"):
        st.markdown("<div style='font-family:Aeonik;font-weight:500;font-size:16px;color:#000000'>Usuário</div>", unsafe_allow_html=True)
        user = st.text_input("", key="login_user", label_visibility="collapsed")
        st.markdown("<div style='font-family:Aeonik;font-weight:500;font-size:16px;color:#000000;margin-top:6px'>Senha</div>", unsafe_allow_html=True)
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
# Inicializações de session_state
# ============================================================
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "login"
if "revisao_em_andamento" not in st.session_state:
    st.session_state["revisao_em_andamento"] = False
if "nome_usuario" not in st.session_state:
    st.session_state["nome_usuario"] = ""
if "projeto" not in st.session_state:
    st.session_state["projeto"] = ""
if "time" not in st.session_state:
    st.session_state["time"] = ""
if "glossario" not in st.session_state:
    st.session_state["glossario"] = ""

# Se não autenticado, mostra login
if not st.session_state["autenticado"]:
    page_login()
    st.stop()

# ============================================================
# PÁGINA 2 (Informações) — sem texto explicativo grande
# ============================================================
def page_info():
    set_background("Patterns-06.png", opacity=1)
    logo_horizontal = os.path.join(logo_dir, "Horizontal_Cor.png")
    cols = st.columns([1,3])
    with cols[0]:
        if os.path.exists(logo_horizontal):
            st.image(logo_horizontal, width=160)

    # labels com estilo (Seu nome / Projeto / Time)
    with st.form("info_form"):
        st.markdown("<div style='font-family:Aeonik;font-weight:500;font-size:20px;color:#000000'>Seu nome</div>", unsafe_allow_html=True)
        nome = st.text_input("", value=st.session_state.get("nome_usuario", ""), key="nome_input", label_visibility="collapsed")
        st.markdown("<div style='font-family:Aeonik;font-weight:500;font-size:20px;color:#000000;margin-top:8px'>Projeto</div>", unsafe_allow_html=True)
        projeto = st.text_input("", value=st.session_state.get("projeto", ""), key="projeto_input", label_visibility="collapsed")
        st.markdown("<div style='font-family:Aeonik;font-weight:500;font-size:20px;color:#000000;margin-top:8px'>Time</div>", unsafe_allow_html=True)
        times = ["Magenta", "Lilás", "Ouro", "Menta", "Patrulha", "Outro"]
        default_index = 0
        if st.session_state.get("time") in times:
            default_index = times.index(st.session_state.get("time"))
        time_sel = st.selectbox("", options=times, index=default_index, label_visibility="collapsed")

        # layout com Logout (esquerda, cinza) e Próximo (direita, magenta)
        cols_btn = st.columns([1,1])
        with cols_btn[0]:
            if st.form_submit_button("Logout"):
                # limpar sessão de forma simples
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.session_state["autenticado"] = False
                st.experimental_rerun()
        with cols_btn[1]:
            if st.form_submit_button("Próximo"):
                st.session_state["nome_usuario"] = nome
                st.session_state["projeto"] = projeto
                st.session_state["time"] = time_sel
                st.session_state["pagina"] = "revisao"
                st.experimental_rerun()

# Se não estiver na página revisão, mostra info
if st.session_state.get("pagina") != "revisao":
    page_info()
    st.stop()

# ============================================================
# PÁGINA 3: REVISÃO (Glossário, Voltar, Iniciar Revisão)
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

def page_revisao():
    set_background("Patterns Escuras_Prancheta 1.png", opacity=1)
    logo_horizontal = os.path.join(logo_dir, "Horizontal_Cor.png")
    cols = st.columns([1,3])
    with cols[0]:
        if os.path.exists(logo_horizontal):
            st.image(logo_horizontal, width=160)

    # Header maior e bold
    st.markdown("<div class='ricca-header-3'>Revisão Ortográfica e Editorial</div>", unsafe_allow_html=True)

    # Glossário note reduzido e box
    st.markdown("<div class='ricca-gloss-box'>Ricca, aqui você deve inserir os padrões do cliente, com uma regra por linha.<br>Ex.:<br>diretor = Diretor-Presidente<br>empresa = Companhia<br>funcionários = colaboradores</div>", unsafe_allow_html=True)
    gloss = st.text_area("", value=st.session_state.get("glossario", ""), key="gloss_input", height=130, label_visibility="collapsed")
    st.session_state["glossario"] = gloss

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Selecione o PDF", type=["pdf"])

    # Botões Voltar (esquerda, cinza) e Iniciar (direita, magenta)
    cols_btn = st.columns([1,1])
    with cols_btn[0]:
        if st.button("Voltar"):
            st.session_state["pagina"] = "info"
            st.experimental_rerun()
    with cols_btn[1]:
        if st.session_state.get("revisao_em_andamento", False):
            st.warning("Revisão em andamento. Aguarde.")
        else:
            if uploaded_file and st.button("Iniciar revisão"):
                st.session_state["revisao_em_andamento"] = True
                start = time.time()
                texto_paginas = []
                with st.spinner("Extraindo texto..."):
                    try:
                        with pdfplumber.open(uploaded_file) as pdf:
                            for i, page in enumerate(pdf.pages, start=1):
                                texto = page.extract_text() or ""
                                texto_paginas.append((i, texto))
                    except Exception:
                        st.error("Erro ao extrair texto do PDF. Verifique o arquivo.")
                        st.session_state["revisao_em_andamento"] = False
                        return

                ocorrencias = []
                api_key = st.secrets.get("OPENAI_API_KEY", None)
                if not api_key:
                    st.error("OPENAI_API_KEY não configurada em st.secrets.")
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

                total = time.time() - start
                st.success(f"Revisão concluída em {total:.1f} segundos.")
                st.session_state["revisao_em_andamento"] = False

                if ocorrencias:
                    df = pd.DataFrame(ocorrencias)
                    df["usuário"] = st.session_state.get("nome_usuario", st.session_state.get("usuario", ""))
                    df["time"] = st.session_state.get("time", "")
                    df["projeto"] = st.session_state.get("projeto", "")
                    df["tempo_s"] = total
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

# executa pagina de revisao
page_revisao()
