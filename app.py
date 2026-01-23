# app.py — Selo Ricca de Revisão
# Requisitos: streamlit, pdfplumber, pandas, openai, openpyxl

import os
import time
import json
import base64
import io
import ast
import streamlit as st
import pdfplumber
import pandas as pd
from openai import OpenAI


# ============================================================
# 1) CONFIG (sempre primeiro no Streamlit)
# ============================================================
st.set_page_config(page_title="Selo Ricca de Revisão", layout="wide")


# ============================================================
# 2) PATHS (conforme sua estrutura)
# ============================================================
LOGO_DIR = "assets/logo.png"
FONTS_DIR = "assets/fonts"
ELEMENTOS_DIR = "assets/Elementos"

LOGO_VERTICAL = os.path.join(LOGO_DIR, "Vertical_Cor.png")
LOGO_HORIZONTAL = os.path.join(LOGO_DIR, "Horizontal_Cor.png")

BG_LOGIN = "Patterns Escuras-03.png"
BG_INFO = "Patterns-06.png"
BG_REVISAO = "Patterns Escuras_Prancheta 1.png"

# Tamanhos (ajuste fino aqui)
LOGO_HORIZONTAL_WIDTH = 300
LOGO_LOGIN_WIDTH = 300  # logo menor na página inicial


# ============================================================
# 3) CSS GLOBAL (ATENÇÃO: dentro de f-string, use {{ e }} no CSS)
# ============================================================
def inject_global_css():
    st.markdown(
        f"""
        <style>
        /* ---- Fontes Aeonik ---- */
        @font-face {{
            font-family: 'Aeonik';
            src: url('{FONTS_DIR}/Aeonik-Regular.otf') format('opentype');
            font-weight: 400;
        }}
        @font-face {{
            font-family: 'Aeonik';
            src: url('{FONTS_DIR}/Aeonik-Medium.otf') format('opentype');
            font-weight: 500;
        }}
        @font-face {{
            font-family: 'Aeonik';
            src: url('{FONTS_DIR}/Aeonik-Bold.otf') format('opentype');
            font-weight: 700;
        }}

        :root {{
            --ricca-grafite: #333333;
            --ricca-branco: #FFFFFF;
            --ricca-preto: #000000;
            --ricca-magenta: #FF00FF;
            --ricca-magenta-hover: #E600E6;
        }}

        /* ---- Fundo branco sempre (inclusive em dark mode) ---- */
        html, body, .stApp {{
            background: #FFFFFF !important;
        }}

        /* ---- Texto padrão preto no app (labels, títulos etc.) ---- */
        html, body, .stApp, p, span, div, label {{
            font-family: 'Aeonik', sans-serif !important;
            color: var(--ricca-preto) !important;
        }}

        /* ---- Botões: magenta + texto branco + Aeonik Bold ---- */
        div.stButton > button {{
            background-color: var(--ricca-magenta) !important;
            color: var(--ricca-branco) !important;
            font-family: 'Aeonik', sans-serif !important;
            font-weight: 700 !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 0.6rem 1.2rem !important;
            font-size: 16px !important;
        }}
        div.stButton > button:hover {{
            background-color: var(--ricca-magenta-hover) !important;
            color: var(--ricca-branco) !important;
        }}
        div.stButton > button:active {{
            transform: scale(0.99);
        }}

        /* ============================================================
           INPUTS / TEXTAREAS: grafite + texto branco (Aeonik Regular)
           ============================================================ */
        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea {{
            background-color: var(--ricca-grafite) !important;
            color: var(--ricca-branco) !important;
            font-family: 'Aeonik', sans-serif !important;
            font-weight: 400 !important;
            border-radius: 10px !important;
            border: 1px solid var(--ricca-grafite) !important;
        }}
        div[data-testid="stTextInput"] input::placeholder,
        div[data-testid="stTextArea"] textarea::placeholder {{
            color: rgba(255,255,255,0.75) !important;
        }}

        /* ============================================================
           SELECTBOX: grafite + texto branco (Aeonik Regular)
           ============================================================ */
        div[data-baseweb="select"] > div {{
            background-color: var(--ricca-grafite) !important;
            border-radius: 10px !important;
            border: 1px solid var(--ricca-grafite) !important;
        }}

        /* Garante texto branco no valor selecionado e nas camadas internas */
        div[data-baseweb="select"] *,
        div[data-baseweb="select"] div,
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] input {{
            color: var(--ricca-branco) !important;
            font-family: 'Aeonik', sans-serif !important;
            font-weight: 400 !important;
        }}

        /* Ícone/seta do select */
        div[data-baseweb="select"] svg {{
            fill: var(--ricca-branco) !important;
        }}

        /* Dropdown (lista de opções) — reforço BaseWeb/Streamlit */
        div[data-baseweb="popover"] ul[role="listbox"] {{
            background-color: var(--ricca-grafite) !important;
        }}
        div[data-baseweb="popover"] ul[role="listbox"] * {{
            color: var(--ricca-branco) !important;
            font-family: 'Aeonik', sans-serif !important;
            font-weight: 400 !important;
        }}
        div[data-baseweb="popover"] li[role="option"] {{
            color: var(--ricca-branco) !important;
            font-family: 'Aeonik', sans-serif !important;
            font-weight: 400 !important;
        }}
        div[data-baseweb="popover"] li[role="option"] * {{
            color: var(--ricca-branco) !important;
        }}

        /* ============================================================
           FILE UPLOADER: grafite + texto branco
           ============================================================ */
        section[data-testid="stFileUploaderDropzone"] {{
            background-color: var(--ricca-grafite) !important;
            border: 1px dashed rgba(255,255,255,0.55) !important;
            border-radius: 12px !important;
        }}
        section[data-testid="stFileUploaderDropzone"] * {{
            color: var(--ricca-branco) !important;
            font-family: 'Aeonik', sans-serif !important;
            font-weight: 400 !important;
        }}
        section[data-testid="stFileUploaderDropzone"] button {{
            color: var(--ricca-branco) !important;
            font-family: 'Aeonik', sans-serif !important;
            font-weight: 700 !important;
        }}

        /* Remove padding extra do topo */
        .block-container {{
            padding-top: 1.5rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 4) FUNDO EM CAMADA (mais robusto — corrige pág 2 e 3)
# ============================================================
def set_background_image(filename: str, opacity: float = 0.1):
    path = os.path.join(ELEMENTOS_DIR, filename)
    if not os.path.exists(path):
        st.error(f"Arquivo de fundo não encontrado: {path}")
        return

    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    st.markdown(
        f"""
        <style>
        /* base branca */
        html, body, .stApp {{
            background: #FFFFFF !important;
        }}

        /* força transparência nos containers que podem estar "tapando" o fundo */
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] > div,
        section.main,
        .main,
        .block-container {{
            background: transparent !important;
        }}

        /* fundo */
        .stApp::before {{
            content: "";
            position: fixed;
            inset: 0;
            background-image: url("data:image/png;base64,{encoded}");
            background-repeat: no-repeat;
            background-position: center;
            background-size: cover;
            : {0,5};
            pointer-events: none;
            z-index: 0;
        }}

        /* garante conteúdo acima do fundo */
        .stApp > .main {{
            position: relative;
            z-index: 1;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 5) PROMPT
# ============================================================
def montar_prompt(glossario_cliente: str) -> str:
    gloss = (glossario_cliente or "").strip()
    if not gloss:
        gloss = "Nenhum glossário fornecido."

    return f"""
Você atuará como revisor(a) e analista de consistência editorial (PT-BR).
Seu trabalho é IDENTIFICAR erros e inconsistências; NÃO reescrever o texto.

REGRAS OBRIGATÓRIAS:
1) NÃO reescreva o texto completo e NÃO proponha mudanças de conteúdo, títulos, nomes próprios, fatos ou números.
2) Só proponha substituições terminológicas se estiverem no GLOSSÁRIO DO CLIENTE (abaixo).
3) Corrija/aponte: ortografia, acentuação, concordância verbal/nominal, regência, pontuação, caixa, hífen, crase e acentos diferenciais.
4) Números de 0 a 10 devem estar por extenso, EXCETO em medidas técnicas e tabelas; nesse caso, manter número e justificar em "observacao".
5) Unidades (SI/uso ABNT): separar número e unidade com espaço (ex.: 10 km, 5 m). Padronize casas decimais entre texto/tabelas/gráficos e aponte inconsistências.
6) Elementos visuais (tabelas, gráficos, boxes, infográficos, quadros, legendas, rodapés): aponte inconsistências numéricas, somas, percentuais (pizza=100%), unidades, casas decimais, títulos/legendas/fonte/crédito.
7) ODS em abertura de capítulos: verifique número, título curto, coerência com o capítulo e consistência (registre se estiver incorreto).
8) Tipografia/layout quando perceptível: viúvas/órfãs, inconsistências claras de espaçamento e hierarquia (apenas sinalize).
9) Se NÃO houver erros, retorne uma lista vazia [].

GLOSSÁRIO DO CLIENTE (aplique SOMENTE estas substituições; formato “termo incorreto = termo correto”):
{gloss}

FORMATO DE SAÍDA (OBRIGATÓRIO — JSON puro, sem comentários, sem markdown):
[
  {{
    "pagina": 1,
    "paragrafo": "opcional (ex.: 3) ou vazio",
    "elemento": "parágrafo | título | tabela | gráfico | infográfico | box | legenda | rodapé | ODS",
    "trecho": "trecho exato com o problema",
    "sugestao": "correção sugerida (somente o necessário)",
    "tipo_erro": "Ortografia | Gramática | Concordância | Pontuação | Numeração | Terminologia | Estilo | Formatação | Visual | Legenda | ODS",
    "observacao": "opcional (use para justificar exceções, como números em tabelas/medidas)"
  }}
]
"""


# ============================================================
# 6) PARSER (sem eval)
# ============================================================
def parse_model_output(text: str):
    if not text:
        return []
    t = text.strip()

    if t.lower().startswith("nenhum erro"):
        return []

    try:
        data = json.loads(t)
        if isinstance(data, list):
            return data
    except Exception:
        pass

    try:
        data = ast.literal_eval(t)
        if isinstance(data, list):
            return data
    except Exception:
        pass

    return [{"_parse_error": True, "raw": t}]


# ============================================================
# 7) CUSTO ESTIMADO
# ============================================================
def estimar_custo_usd(num_chars: int) -> float:
    est_tokens = max(1, num_chars // 4)
    return round(est_tokens * 0.000002, 6)


# ============================================================
# 8) ESTADO
# ============================================================
inject_global_css()

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "etapa" not in st.session_state:
    st.session_state.etapa = "login"
if "historico_uso" not in st.session_state:
    st.session_state.historico_uso = []


# ============================================================
# 9) PÁGINAS
# ============================================================
def pagina_login():
    set_background_image(BG_LOGIN, opacity=0.1)

    left, center, right = st.columns([1, 2, 1])
    with center:
        st.image(LOGO_VERTICAL, width=LOGO_LOGIN_WIDTH, use_column_width=300)
        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        st.markdown("<h2 style='margin:0;'>Login</h2>", unsafe_allow_html=True)

        user = st.text_input("Usuário", key="login_user")
        pwd = st.text_input("Senha", type="password", key="login_pwd")

        if st.button("Próximo"):
            if user == "riccarevisao" and pwd == "Ricc@2026!":
                st.session_state.autenticado = True
                st.session_state.etapa = "info"
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")


def pagina_info():
    # fundo da pág 2 (corrigido para aparecer)
    set_background_image(BG_INFO, opacity=1)

    col_logo, col_spacer = st.columns([1, 6])
    with col_logo:
        st.image(LOGO_HORIZONTAL, width=LOGO_HORIZONTAL_WIDTH, use_column_width=300)

    st.markdown("<h2 style='margin-top:8px;'>Informações iniciais</h2>", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.text_input("Seu nome", key="nome_usuario")
        st.text_input("Projeto", key="nome_projeto")
    with col2:
        st.selectbox(
            "Time",
            ["Lilás", "Magenta", "Menta", "Ouro", "Patrulha", "Outro"],
            key="time_sel",
        )


    if st.button("Próximo"):
        if not st.session_state.nome_usuario.strip() or not st.session_state.nome_projeto.strip():
            st.error("Preencha seu nome e o nome do projeto antes de avançar.")
            st.stop()
        st.session_state.etapa = "revisao"
        st.rerun()


def pagina_revisao():
    # fundo da pág 3 (corrigido para aparecer)
    set_background_image(BG_REVISAO, opacity=0.4)

    col_logo, col_spacer = st.columns([1, 6])
    with col_logo:
        st.image(LOGO_HORIZONTAL, width=LOGO_HORIZONTAL_WIDTH, use_column_width=300)

    st.markdown("<h2 style='margin-top:8px;'>Revisão em PDF</h2>", unsafe_allow_html=True)

    st.info(
        "A revisão é automática e retorna um RELATÓRIO DE OCORRÊNCIAS (Excel). "
        "Para controlar custos, comece com PDFs curtos."
    )

    # ✅ Glossário MOVIDO para a página 3
    st.markdown("<h3 style='margin-top:10px;'>Glossário do cliente</h3>", unsafe_allow_html=True)
    st.text_area(
        "Uma regra por linha (termo incorreto = termo correto)",
        placeholder="Ex.: diretor = Diretor-Presidente\nempresa = Companhia\ncolaborador(a) = funcionário(a)\nEstado - ES = Estado (ES)",
        key="glossario_cliente",
        height=140,
    )

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    uploaded = st.file_uploader("Selecione o arquivo PDF", type=["pdf"])

    # Botões lado a lado (canto esq / canto dir)
    col_left, col_right = st.columns([1, 1])
    with col_left:
        if st.button("Voltar"):
            st.session_state.etapa = "info"
            st.rerun()
    with col_right:
        iniciar = st.button("Iniciar Revisão")

    if iniciar:
        if not uploaded:
            st.error("Faça upload de um PDF para iniciar.")
            st.stop()

        nome = st.session_state.get("nome_usuario", "").strip()
        projeto = st.session_state.get("nome_projeto", "").strip()
        time_sel = st.session_state.get("time_sel", "")
        glossario = st.session_state.get("glossario_cliente", "")

        t0 = time.time()
        status_area = st.empty()

        status_area.info("Extraindo texto...")
        with st.spinner("Extraindo texto..."):
            pages_text = []
            total_chars = 0
            with pdfplumber.open(uploaded) as pdf:
                for i, page in enumerate(pdf.pages, start=1):
                    txt = page.extract_text() or ""
                    total_chars += len(txt)
                    pages_text.append((i, txt))

        status_area.info("Revisão em andamento, aguarde mais um pouquinho...")
        with st.spinner("Revisão em andamento, aguarde mais um pouquinho..."):
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            prompt_sistema = montar_prompt(glossario)

            ocorrencias = []
            for (page_num, txt) in pages_text:
                if not txt.strip():
                    ocorrencias.append(
                        {
                            "pagina": page_num,
                            "paragrafo": "",
                            "elemento": "parágrafo",
                            "trecho": "",
                            "sugestao": "",
                            "tipo_erro": "Formatação",
                            "observacao": "Página sem texto extraível (pode ser imagem/scan).",
                        }
                    )
                    continue

                resp = client.chat.completions.create(
                    model="gpt-4.1-mini",
                    temperature=0,
                    messages=[
                        {"role": "system", "content": prompt_sistema},
                        {"role": "user", "content": txt},
                    ],
                )

                raw = resp.choices[0].message.content
                data = parse_model_output(raw)

                if data and isinstance(data, list) and data[0].get("_parse_error"):
                    ocorrencias.append(
                        {
                            "pagina": page_num,
                            "paragrafo": "",
                            "elemento": "parágrafo",
                            "trecho": "—",
                            "sugestao": "—",
                            "tipo_erro": "Erro de processamento",
                            "observacao": "Resposta fora do JSON esperado. Ajuste o prompt/validação.",
                        }
                    )
                    continue

                for item in data:
                    if not isinstance(item, dict):
                        continue
                    item["pagina"] = page_num
                    item.setdefault("paragrafo", "")
                    item.setdefault("elemento", "parágrafo")
                    item.setdefault("trecho", "")
                    item.setdefault("sugestao", "")
                    item.setdefault("tipo_erro", "Estilo")
                    item.setdefault("observacao", "")
                    ocorrencias.append(item)

        status_area.info("Gerando relatório de erros...")
        with st.spinner("Gerando relatório de erros..."):
            dur_s = round(time.time() - t0, 2)
            custo_usd = estimar_custo_usd(total_chars)

            if not ocorrencias:
                df = pd.DataFrame(
                    [
                        {
                            "pagina": "",
                            "paragrafo": "",
                            "elemento": "",
                            "trecho": "",
                            "sugestao": "",
                            "tipo_erro": "",
                            "observacao": "Nenhum erro identificado nas páginas analisadas. Texto revisado segundo os padrões solicitados.",
                        }
                    ]
                )
            else:
                df = pd.DataFrame(ocorrencias)

            df.insert(0, "usuario", nome)
            df.insert(1, "projeto", projeto)
            df.insert(2, "time", time_sel)
            df["tempo_revisao_s"] = dur_s
            df["custo_estimado_usd"] = custo_usd

            status_area.success(f"Concluído em {dur_s}s. Custo estimado: US$ {custo_usd}")

            st.dataframe(df, use_container_width=True)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Relatorio_Erros")

                uso = pd.DataFrame(
                    [
                        {
                            "usuario": nome,
                            "projeto": projeto,
                            "time": time_sel,
                            "pdf_paginas": len(pages_text),
                            "tempo_revisao_s": dur_s,
                            "custo_estimado_usd": custo_usd,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    ]
                )
                uso.to_excel(writer, index=False, sheet_name="Uso_Interno")

            output.seek(0)

            st.session_state.historico_uso.append(
                {
                    "usuario": nome,
                    "projeto": projeto,
                    "time": time_sel,
                    "pdf_paginas": len(pages_text),
                    "tempo_revisao_s": dur_s,
                    "custo_estimado_usd": custo_usd,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

            st.download_button(
                "Baixar relatório em Excel",
                data=output,
                file_name="selo_ricca_relatorio_revisao.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            with st.expander("Registro interno de uso (sessão atual)"):
                st.dataframe(pd.DataFrame(st.session_state.historico_uso), use_container_width=True)


# ============================================================
# 10) ROTEAMENTO
# ============================================================
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    pagina_login()
else:
    if st.session_state.etapa == "login":
        st.session_state.etapa = "info"
        st.rerun()
    elif st.session_state.etapa == "info":
        pagina_info()
    else:
        pagina_revisao()
