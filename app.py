import streamlit as st
import pdfplumber
import pandas as pd
import os
import time
from openai import OpenAI
import base64
import io
import json

# ----------------------
# Config
# ----------------------
st.set_page_config(page_title="Selo Ricca de Revisão", layout="wide")
BASE = os.path.dirname(__file__) if "__file__" in globals() else "."

logo_dir = os.path.join(BASE, "assets", "logo.png")
fonts_dir = os.path.join(BASE, "assets", "fonts")
elementos_path = os.path.join(BASE, "assets", "Elementos")

# ----------------------
# Helper: carregar arquivo como base64
# ----------------------
def file_b64(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# ----------------------
# CSS global: aplica Aeonik em praticamente tudo e estiliza botões/selectboxes
# ----------------------
def inject_css():
    regular = os.path.join(fonts_dir, "Aeonik-Regular.otf")
    medium = os.path.join(fonts_dir, "Aeonik-Medium.otf")
    bold = os.path.join(fonts_dir, "Aeonik-Bold.otf")

    # se fontes não existirem, avisar (mas continuar)
    missing = []
    for p in [regular, medium, bold]:
        if not os.path.exists(p):
            missing.append(p)
    if missing:
        st.warning("Arquivos de fonte Aeonik não encontrados em assets/fonts/. Verifique os paths.")

    css = f"""
    <style>
    @font-face {{ font-family: 'Aeonik'; src: url('{regular}') format('opentype'); font-weight: 400; }}
    @font-face {{ font-family: 'Aeonik'; src: url('{medium}') format('opentype'); font-weight: 500; }}
    @font-face {{ font-family: 'Aeonik'; src: url('{bold}') format('opentype'); font-weight: 700; }}

    /* Forçar Aeonik globalmente */
    html, body, .stApp, .block-container, .stMarkdown, .element-container, .css-1d391kg {{
        font-family: 'Aeonik', sans-serif !important;
        color: #000000 !important;
        background-color: #FFFFFF !important;
    }}

    /* Botões: magenta, texto branco, Aeonik Medium 16px */
    div.stButton > button, button {{

        background-color: #FF00FF !important;
        color: #FFFFFF !important;
        font-family: 'Aeonik', sans-serif !important;
        font-weight: 500 !important;
        font-size: 16px !important;
        border-radius: 8px !important;
        padding: 0.45em 1.1em !important;
    }}
    div.stButton > button:hover, button:hover {{
        background-color: #E600E6 !important;
    }}

    /* Selectbox: força fonte Aeonik e cor branca no valor */
    div[data-baseweb="select"] * {{
        font-family: 'Aeonik', sans-serif !important;
        color: #FFFFFF !important;
    }}
    div[data-baseweb="select"] > div > div > div > div {{
        background-color: #333333 !important;
        border-radius: 6px !important;
    }}

    /* Títulos específicos */
    .ricca-title-big {{ font-size: 28px; font-weight: 700; margin: 0 0 8px 0; }}
    .ricca-subnote {{ font-size: 14px; color: #FF00FF; font-weight: 500; padding: 8px; background:#FFF0FF; border-radius:6px; }}

    /* Background layer - preenchimento total */
    .app-background {{
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        z-index: -1;
        background-size: cover;
        background-repeat: no-repeat;
        background-position: center;
        opacity: 1;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

inject_css()

# ----------------------
# Background helper (usa arquivos em assets/Elementos)
# ----------------------
def set_background(filename):
    path = os.path.join(Elementos_path, filename)
    b64 = file_b64(path)
    if not b64:
        st.info(f"Background {filename} não encontrado em assets/Elementos.")
        return
    st.markdown(f"""
    <div class="app-background" style="background-image:url('data:image/png;base64,{b64}');"></div>
    """, unsafe_allow_html=True)

# ----------------------
# Logos (usando os paths exatos informados)
# ----------------------
logo_vertical_path = os.path.join(logo_dir, "Vertical_Cor.png")
logo_horizontal_path = os.path.join(logo_dir, "Horizontal_Cor.png")
if not os.path.exists(logo_vertical_path):
    st.warning("Vertical_Cor.png não encontrado em assets/logo/")
if not os.path.exists(logo_horizontal_path):
    st.warning("Horizontal_Cor.png não encontrado em assets/logo/")

# ----------------------
# Autenticação fixa
# ----------------------
HARDCODED_USER = "riccarevisao"
HARDCODED_PASS = "Ricc@2026!"

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "login"
if "revisao_em_andamento" not in st.session_state:
    st.session_state["revisao_em_andamento"] = False
# session fields
for k in ("nome_usuario","projeto","time","glossario"):
    if k not in st.session_state:
        st.session_state[k] = ""

# ----------------------
# PÁGINA 1 - LOGIN
# ----------------------
def page_login():
    set_background("Patterns Escuras-03.png")
    cols = st.columns([1,4])
    with cols[0]:
        if os.path.exists(Logo_Vertical_path):
            st.image(Logo_Vertical_path, width=260)
    with cols[1]:
        st.markdown("<div class='ricca-title-big'>Selo Ricca de Revisão</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:18px; font-weight:700;'>Login</div>", unsafe_allow_html=True)

    # form para permitir submit com Enter
    with st.form("form_login"):
        st.markdown("<div style='font-weight:500; font-size:16px;color:#000'>Usuário</div>", unsafe_allow_html=True)
        user = st.text_input("", key="input_user", label_visibility="collapsed")
        st.markdown("<div style='font-weight:500; font-size:16px;color:#000'>Senha</div>", unsafe_allow_html=True)
        pwd = st.text_input("", type="password", key="input_pass", label_visibility="collapsed")
        submitted = st.form_submit_button("Entrar")
        if submitted:
            if user == HARDCODED_USER and pwd == HARDCODED_PASS:
                st.session_state["autenticado"] = True
                st.session_state["usuario"] = user
                st.session_state["pagina"] = "info"
                st.experimental_rerun()
            else:
                st.error("Usuário ou senha incorretos.")

if not st.session_state["autenticado"]:
    page_login()
    st.stop()

# ----------------------
# PÁGINA 2 - INFORMAÇÕES
# ----------------------
def page_info():
    set_background("Patterns-06.png")
    cols = st.columns([1,4])
    with cols[0]:
        if os.path.exists(Logo_Horizontal_path):
            st.image(Logo_Horizontal_path, width=160)
    # sem cabeçalho extra, apenas labels
    with st.form("form_info"):
        st.markdown("<div style='font-weight:500; font-size:20px;color:#000'>Seu nome</div>", unsafe_allow_html=True)
        nome = st.text_input("", value=st.session_state.get("nome_usuario",""), key="nome")
        st.markdown("<div style='font-weight:500; font-size:20px;color:#000'>Projeto</div>", unsafe_allow_html=True)
        projeto = st.text_input("", value=st.session_state.get("projeto",""), key="projeto")
        st.markdown("<div style='font-weight:500; font-size:20px;color:#000'>Time</div>", unsafe_allow_html=True)
        times = ["Magenta","Lilás","Ouro","Menta","Patrulha","Outro"]
        idx = times.index(st.session_state["time"]) if st.session_state["time"] in times else 0
        time_sel = st.selectbox("", options=times, index=idx, key="time")

        # botões: esquerda logout cinza, direita próximo magenta
        cols_btn = st.columns([1,1])
        with cols_btn[0]:
            if st.form_submit_button("Logout"):
                # limpa sessão
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

if st.session_state.get("pagina") == "info":
    page_info()
    st.stop()

# ----------------------
# Prompt builder
# ----------------------
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

# ----------------------
# PÁGINA 3 - REVISÃO
# ----------------------
def page_revisao():
    set_background("Patterns Escuras_Prancheta 1.png")
    cols = st.columns([1,4])
    with cols[0]:
        if os.path.exists(Logo_Horizontal_path):
            st.image(Logo_Horizontal_path, width=160)

    st.markdown("<div class='ricca-title-big'>Revisão ortográfica e editorial</div>", unsafe_allow_html=True)

    # Voltar (botão real): à esquerda, cinza
    cols_nav = st.columns([1,4])
    with cols_nav[0]:
        if st.button("Voltar"):
            st.session_state["pagina"] = "info"
            st.experimental_rerun()

    # Nota do glossário (menor) e text_area magenta claro com texto magenta vivo
    st.markdown("<div style='font-size:14px;color:#000;margin-top:8px'>Glossário do cliente</div>", unsafe_allow_html=True)
    st.markdown("<div class='ricca-subnote'>Ricca, aqui você deve inserir os padrões do cliente, com uma regra por linha.<br>Ex.:<br>diretor = Diretor-Presidente<br>empresa = Companhia<br>funcionários = colaboradores</div>", unsafe_allow_html=True)
    gloss = st.text_area("", value=st.session_state.get("glossario",""), key="gloss_area", height=130, label_visibility="collapsed")
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)  # espaço entre glossário e uploader

    uploaded_file = st.file_uploader("Selecione o PDF", type=["pdf"])

    # Iniciar revisão (botão magenta, à direita)
    cols_act = st.columns([3,1])
    with cols_act[1]:
        if st.button("Iniciar revisão") and uploaded_file and not st.session_state.get("revisao_em_andamento", False):
            # salva glossário
            st.session_state["glossario"] = gloss
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
                    st.error("Erro ao extrair texto do PDF. Verifique o arquivo (pode estar escaneado).")
                    st.session_state["revisao_em_andamento"] = False
                    return

            ocorrencias = []
            api_key = st.secrets.get("OPENAI_API_KEY", None)
            if not api_key:
                st.error("OPENAI_API_KEY não configurada em st.secrets.")
                st.session_state["revisao_em_andamento"] = False
                return

            client = OpenAI(api_key=api_key)
            prompt = montar_prompt(st.session_state.get("glossario",""))

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
                            elif isinstance(dados, str) and dados == "Nenhum erro identificado":
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
                df["usuário"] = st.session_state.get("nome_usuario", st.session_state.get("usuario",""))
                df["time"] = st.session_state.get("time","")
                df["projeto"] = st.session_state.get("projeto","")
                df["tempo_s"] = total_time
                df["custo_estimado_USD"] = len(texto_paginas) * 0.01
                st.dataframe(df, use_container_width=True)
                output = io.BytesIO()
                df.to_excel(output, index=False, engine="openpyxl")
                output.seek(0)
                st.download_button("Baixar relatório em Excel", data=output.getvalue(), file_name="selo_ricca_relatorio.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.info("Nenhuma ocorrência identificada.")

# Exibir página de revisão
page_revisao()
