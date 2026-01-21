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
# PATHS DE ASSETS (conforme fornecido)
# ============================================================
logo_dir = "assets/logo"
fonts_dir = "assets/fonts"
elementos_path = "assets/Elementos"

# ============================================================
# CSS GLOBAL (fontes Aeonik, botões, selectbox, backgrounds)
# ============================================================
def inject_global_css():
    # paths de fontes (conforme fornecido)
    regular = os.path.join(fonts_dir, "Aeonik-Regular.otf")
    medium = os.path.join(fonts_dir, "Aeonik-Medium.otf")
    bold = os.path.join(fonts_dir, "Aeonik-Bold.otf")

    css = f"""
    <style>
    /* Font-face */
    @font-face {{ font-family: 'Aeonik'; src: url('{regular}') format('opentype'); font-weight: 400; }}
    @font-face {{ font-family: 'Aeonik'; src: url('{medium}') format('opentype'); font-weight: 500; }}
    @font-face {{ font-family: 'Aeonik'; src: url('{bold}') format('opentype'); font-weight: 700; }}

    /* Força família */
    html, body, .stApp, .main {{
        font-family: 'Aeonik', sans-serif;
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }}

    /* Botões - padrão */
    div.stButton > button {{
        background-color: #FF00FF;
        color: #FFFFFF;
        font-family: 'Aeonik', sans-serif !important;
        font-weight: 700;
        border-radius: 8px;
        padding: 0.5em 1.2em;
        font-size: 16px;
    }}
    div.stButton > button:hover {{
        background-color: #E600E6;
    }}

    /* Botão cinza (logout / voltar) - classe custom será aplicada via HTML wrapper */
    .ricca-btn-gray {{
        background-color: #666666 !important;
        color: #FFFFFF !important;
        font-family: 'Aeonik' !important;
        font-weight: 400 !important;
        border-radius: 8px !important;
        padding: 0.45em 1.0em !important;
        font-size: 16px !important;
    }}

    /* Selectbox visual (frágil, depende de estrutura interna do Streamlit) */
    div[data-baseweb="select"] > div > div > div > div {{
        background-color: #333333 !important;
        border-radius: 6px;
    }}
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div[class*="value"] {{
        color: white !important;
        font-family: 'Aeonik', sans-serif !important;
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

    /* Labels / helper customizados (podem ser usados com st.markdown) */
    .ricca-title-bold {{
        font-family: 'Aeonik', sans-serif;
        font-weight: 700;
        color: #000000;
    }}
    .ricca-medium-16 {{
        font-family: 'Aeonik', sans-serif;
        font-weight: 500;
        color: #000000;
        font-size: 16px;
    }}
    .ricca-medium-20 {{
        font-family: 'Aeonik', sans-serif;
        font-weight: 500;
        color: #000000;
        font-size: 20px;
    }}
    .glossario-box {{
        background-color: #FFE6FF; /* magenta clarinho */
        border-radius: 6px;
        padding: 0.6rem;
        color: #FF00FF; /* magenta vivo */
        font-family: 'Aeonik', sans-serif;
        font-weight: 500;
        font-size: 16px;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

inject_global_css()

# ============================================================
# FUNÇÃO PARA DEFINIR BACKGROUND (usa arquivo em assets/Elementos)
# ============================================================
def set_background(image_filename: str, opacity: float = 1.0):
    img_path = os.path.join(elementos_path, image_filename)
    if not os.path.exists(img_path):
        # Aviso leve; não interrompe
        st.markdown(f"<!-- Background {image_filename} não encontrado -->", unsafe_allow_html=True)
        return
    with open(img_path, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()
    style = f"""
    <style>
    .app-background {{
        background-image: url("data:image/png;base64,{encoded}");
        opacity: {opacity};
    }}
    </style>
    <div class="app-background"></div>
    """
    st.markdown(style, unsafe_allow_html=True)

# ============================================================
# AUTENTICAÇÃO (fixa e obrigatória)
# ============================================================
HARDCODED_USER = "riccarevisao"
HARDCODED_PASS = "Ricc@2026!"

def login_page():
    # background e logo
    set_background("Patterns Escuras-03.png", opacity=1)
    logo_vertical = os.path.join(logo_dir, "Vertical_Cor.png")
    # posicionamento: esquerda em cima — usamos um layout com colunas
    c1, c2 = st.columns([1, 3])
    with c1:
        if os.path.exists(logo_vertical):
            st.image(logo_vertical, width=240)  # grande na primeira página, fica à esquerda em cima
        else:
            st.markdown("<h3 class='ricca-title-bold'>Selo Ricca de Revisão</h3>", unsafe_allow_html=True)
    with c2:
        # titulo e subtitulo (estilo Aeonik Bold)
        st.markdown("<h1 class='ricca-title-bold' style='font-size:32px;margin:0'>Selo Ricca de Revisão</h1>", unsafe_allow_html=True)
        st.markdown("<h3 class='ricca-title-bold' style='font-size:18px;margin-top:6px'>Login</h3>", unsafe_allow_html=True)

    # Formulário para permitir submissão via Enter
    with st.form("login_form"):
        st.markdown("<div class='ricca-medium-16'>Usuário</div>", unsafe_allow_html=True)
        user = st.text_input("", key="login_user", label_visibility="collapsed")
        st.markdown("<div class='ricca-medium-16'>Senha</div>", unsafe_allow_html=True)
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
# mantém campos previamente preenchidos
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
    login_page()
    st.stop()

# ============================================================
# PÁGINA 2: INFORMAÇÕES DO PROJETO (sem título grande, só labels)
# ============================================================
def info_page():
    set_background("Patterns-06.png", opacity=1)
    logo_horizontal = os.path.join(logo_dir, "Horizontal_Cor.png")
    c1, c2 = st.columns([1, 3])
    with c1:
        if os.path.exists(logo_horizontal):
            st.image(logo_horizontal, width=160)  # médio, à esquerda em cima
    # Não exibir "Informações do projeto" como cabeçalho; apenas labels conforme pedido
    with st.form("info_form"):
        st.markdown("<div class='ricca-medium-20'>Seu nome</div>", unsafe_allow_html=True)
        nome_usuario = st.text_input("", value=st.session_state.get("nome_usuario", ""), key="nome_input", label_visibility="collapsed")
        st.markdown("<div class='ricca-medium-20'>Projeto</div>", unsafe_allow_html=True)
        projeto = st.text_input("", value=st.session_state.get("projeto", ""), key="projeto_input", label_visibility="collapsed")
        st.markdown("<div class='ricca-medium-20'>Time</div>", unsafe_allow_html=True)
        # selectbox com estilo aplicado por CSS global
        time_opcoes = ["Magenta", "Lilás", "Ouro", "Menta", "Patrulha", "Outro"]
        initial = time_opcoes.index(st.session_state.get("time")) if st.session_state.get("time") in time_opcoes else 0
        time_selecionado = st.selectbox("", options=time_opcoes, index=initial, key="time_select", label_visibility="collapsed")

        # Rodapé com botões: Logout (cinza, à esquerda) e Próximo (magenta, à direita)
        colL, colR = st.columns([1,1])
        with colL:
            # botão cinza: aplicamos um botão HTML para garantir estilo cinza (usar st.markdown com uma pequena forma)
            if st.form_submit_button("Logout", on_click=None, key="logout_btn"):
                # limpa sessão
                keys = ["autenticado","usuario","nome_usuario","projeto","time","glossario","pagina","revisao_em_andamento"]
                for k in keys:
                    if k in st.session_state:
                        del st.session_state[k]
                st.session_state["autenticado"] = False
                st.experimental_rerun()
        with colR:
            if st.form_submit_button("Próximo", key="next_btn"):
                st.session_state["nome_usuario"] = nome_usuario
                st.session_state["projeto"] = projeto
                st.session_state["time"] = time_selecionado
                st.session_state["pagina"] = "revisao"
                st.experimental_rerun()

# Se não for página de revisão, mostra info_page
if st.session_state.get("pagina") != "revisao":
    info_page()
    st.stop()

# ============================================================
# PÁGINA 3: REVISÃO (com glossário e botões conforme solicitado)
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
    c1, c2 = st.columns([1, 3])
    with c1:
        if os.path.exists(logo_horizontal):
            st.image(logo_horizontal, width=160)

    # Título principal em Aeonik Bold
    st.markdown("<h2 class='ricca-title-bold' style='font-size:24px;margin:0'>Revisão ortográfica e editorial</h2>", unsafe_allow_html=True)

    # Glossário: titulo estilizado e caixa com placeholder e cor magenta
    st.markdown("<div class='ricca-medium-20' style='margin-top:12px'>Glossário do cliente</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='glossario-box'>Riccu, aqui você deve inserir os padrões do cliente, com uma regra por linha.<br/>Ex.:<br/>diretor = Diretor-Presidente<br/>empresa = Companhia<br/>funcionários = colaboradores</div>",
        unsafe_allow_html=True,
    )
    # Input do glossário (text_area) com valor pré-carregado
    gloss = st.text_area("", value=st.session_state.get("glossario", ""), key="gloss_input", height=140, label_visibility="collapsed")
    # atualiza session
    st.session_state["glossario"] = gloss

    # Uploader do PDF
    uploaded_file = st.file_uploader("Selecione o PDF", type=["pdf"])

    # Botões Voltar (cinza, esquerda) e Iniciar Revisão (magenta, direita)
    col_back, col_run = st.columns([1,1])
    with col_back:
        # botão cinza: para aparência, usamos form_submit_button style via markdown wrapper
        if st.button("Voltar"):
            st.session_state["pagina"] = "info"
            st.experimental_rerun()

    with col_run:
        iniciar = st.button("Iniciar revisão")
        # Prevencao de multiplos cliques
        if iniciar and not st.session_state.get("revisao_em_andamento", False):
            st.session_state["revisao_em_andamento"] = True
            # inicia processamento
            start_time = time.time()
            texto_paginas = []
            with st.spinner("Extraindo texto..."):
                try:
                    with pdfplumber.open(uploaded_file) as pdf:
                        for i, page in enumerate(pdf.pages, start=1):
                            texto = page.extract_text() or ""
                            texto_paginas.append((i, texto))
                except Exception:
                    st.error("Erro ao extrair texto do PDF. Verifique o arquivo (pode ser escaneado).")
                    st.session_state["revisao_em_andamento"] = False
                    return

            ocorrencias = []
            api_key = st.secrets.get("OPENAI_API_KEY", None)
            if not api_key:
                st.error("OPENAI_API_KEY não configurada em st.secrets. Impossível continuar.")
                st.session_state["revisao_em_andamento"] = False
                return

            client = OpenAI(api_key=api_key)
            prompt_base = montar_prompt(st.session_state.get("glossario", ""))

            # Processamento por página
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
                                    {"role": "system", "content": prompt_base},
                                    {"role": "user", "content": texto}
                                ],
                            )
                            try:
                                resultado = resposta.choices[0].message.content
                            except Exception:
                                resultado = getattr(resposta, "text", "") or ""

                            if not resultado:
                                raise ValueError("Resposta vazia")

                            # parse seguro
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
                                        "justificativa": f"Resposta da IA fora do formato JSON esperado (t:{tentativa})"
                                    })
                                    sucesso = True
                                    break

                            if isinstance(dados, list):
                                for item in dados:
                                    if isinstance(item, dict):
                                        item.setdefault("categoria", "Ortografia")
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

            # Relatório em Excel
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
