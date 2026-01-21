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


# ============================================================
# 3) CSS GLOBAL (atende: fundo branco, texto preto, selectbox grafite+texto branco,
#    botões magenta com texto branco e Aeonik Bold)
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

        /* ---- Fundo branco sempre (inclusive em dark mode) ---- */
        html, body, .stApp {{
            background: #FFFFFF !important;
        }}

        /* ---- Texto padrão preto em todo o app ---- */
        html, body, .stApp, p, span, div, label, input, textarea {{
            font-family: 'Aeonik', sans-serif !important;
            color: #000000 !important;
        }}

        /* ---- Botões: magenta + texto branco + Aeonik Bold ---- */
        div.stButton > button {{
            background-color: #FF00FF !important;
            color: #FFF !important;
            font-family: 'Aeonik', sans-serif !important;
            font-weight: 700 !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 0.6rem 1.2rem !important;
            font-size: 16px !important;
        }}
        div.stButton > button:hover {{
            background-color: #E600E6 !important;
            color: #FFFFFF !important;
        }}
        div.stButton > button:active {{
            transform: scale(0.99);
        }}

        /* ---- Selectbox: fundo grafite + texto branco + Aeonik Regular ---- */
        /* Caixa do select */
        div[data-baseweb="select"] > div {{
            background-color: #333333 !important;
            border-radius: 10px !important;
            border: 1px solid #333333 !important;
            color: #FFFFFF !important;
        }}
        /* Texto selecionado */
        div[data-baseweb="select"] span {{
            color: #FFFFFF !important;
            font-family: 'Aeonik', sans-serif !important;
            font-weight: 400 !important;
        }}
        /* Ícone/seta */
        div[data-baseweb="select"] svg {{
            fill: #FFFFFF !important;
        }}

        /* Dropdown (lista de opções) */
        ul[role="listbox"] {{
            background-color: #333333 !important;
        }}
        ul[role="listbox"] * {{
            color: #FFFFFF !important;
            font-family: 'Aeonik', sans-serif !important;
            font-weight: 400 !important;
        }}

        /* Inputs e textareas com fundo branco (para bater com a identidade) */
        input, textarea {{
            background-color: #FFFFFF !important;
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
# 4) FUNDO EM CAMADA (atrás de tudo) — ocupa a página toda
# ============================================================
def set_background_image(filename: str, opacity: float = 0.18):
    path = os.path.join(ELEMENTOS_DIR, filename)
    if not os.path.exists(path):
        st.error(f"Arquivo de fundo não encontrado: {path}")
        return

    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    st.markdown(
        f"""
        <style>
        .ricca-bg {{
            position: fixed;
            inset: 0;
            width: 100vw;
            height: 100vh;
            z-index: -1;
            pointer-events: none;
            opacity: 1;
            background-image: url("data:image/png;base64,{encoded}");
            background-repeat: no-repeat;
            background-position: center;
            background-size: cover; /* página toda */
        }}
        </style>
        <div class="ricca-bg"></div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 5) PROMPT (corretamente incorporado, com glossário preenchido pelo usuário)
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
# 6) PARSER (sem eval): tenta JSON, depois literal_eval seguro
# ============================================================
def parse_model_output(text: str):
    if not text:
        return []
    t = text.strip()

    # Se o modelo devolveu algo tipo "Nenhum erro identificado", tratamos como lista vazia
    if t.lower().startswith("nenhum erro"):
        return []

    # Tenta JSON
    try:
        data = json.loads(t)
        if isinstance(data, list):
            return data
    except Exception:
        pass

    # fallback: literal_eval (seguro, não executa código)
    try:
        data = ast.literal_eval(t)
        if isinstance(data, list):
            return data
    except Exception:
        pass

    # Se falhar, retorna marcador de erro
    return [{"_parse_error": True, "raw": t}]


# ============================================================
# 7) CUSTO ESTIMADO (estimativa simples; opcionalmente melhora com usage se disponível)
# ============================================================
def estimar_custo_usd(num_chars: int) -> float:
    # Heurística conservadora: ~4 chars por token (média).
    # Sem tabela oficial aqui, então mantemos só estimativa.
    est_tokens = max(1, num_chars // 4)
    # “intermediário” — você pode ajustar depois quando quiser:
    # Ex.: US$ 0.000002 por token (valor fictício para estimativa interna)
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
    set_background_image(BG_LOGIN, opacity=1)

    # Centralizar logo e conteúdo
    left, center, right = st.columns([1, 2, 1])
    with center:
        st.image(LOGO_VERTICAL, width=340, use_column_width=False)
        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        st.markdown("<h2 style='margin:0;'>Login</h2>", unsafe_allow_html=True)

        user = st.text_input("Usuário", key="login_user")
        pwd = st.text_input("Senha", type="password", key="login_pwd")

        # Apenas 1 botão nesta página
        if st.button("Próximo"):
            if user == "riccarevisao" and pwd == "Ricc@2026!":
                st.session_state.autenticado = True
                st.session_state.etapa = "info"
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")


def pagina_info():
    set_background_image(BG_INFO, opacity=1)

    col_logo, col_space = st.columns([1, 5])
with col_logo:
    st.image(LOGO_HORIZONTAL, width=180)

    st.markdown("<h2 style='margin-top:8px;'>Informações iniciais</h2>", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        nome = st.text_input("Seu nome", key="nome_usuario")
        projeto = st.text_input("Projeto", key="nome_projeto")
    with col2:
        time_sel = st.selectbox(
            "Time",
            ["Magenta", "Lilás", "Ouro", "Menta", "Patrulha", "Outro"],
            key="time_sel",
        )

    st.markdown("<h3 style='margin-top:18px;'>Glossário do cliente</h3>", unsafe_allow_html=True)
    gloss = st.text_area(
        "Uma regra por linha (termo incorreto = termo correto)",
        placeholder="Ex.: diretor = Diretor-Presidente\nempresa = Companhia\ncolaborador(a) = funcionário(a)\nEstado - ES = Estado (ES)",
        key="glossario_cliente",
        height=160,
    )

    # Apenas 1 botão nesta página
    if st.button("Próximo"):
        if not nome.strip() or not projeto.strip():
            st.error("Preencha seu nome e o nome do projeto antes de avançar.")
        st.session_state.etapa = "revisao"
        st.rerun()


def pagina_revisao():
    set_background_image(BG_REVISAO, opacity=1)

    col_logo, col_space = st.columns([1, 5])
with col_logo:
    st.image(LOGO_HORIZONTAL, width=180)
    st.markdown("<h2 style='margin-top:8px;'>Revisão em PDF</h2>", unsafe_allow_html=True)

    st.info(
        "A revisão é automática e retorna um RELATÓRIO DE OCORRÊNCIAS (Excel). "
        "Para controlar custos, comece com PDFs curtos."
    )

    uploaded = st.file_uploader("Selecione o arquivo PDF", type=["pdf"])

    # Apenas 1 botão nesta página (além do download, que só aparece após gerar)
    if st.button("Iniciar Revisão"):
        if not uploaded:
            st.error("Faça upload de um PDF para iniciar.")
            return

        nome = st.session_state.get("nome_usuario", "").strip()
        projeto = st.session_state.get("nome_projeto", "").strip()
        time_sel = st.session_state.get("time_sel", "")
        glossario = st.session_state.get("glossario_cliente", "")

        # Etapa 1: extração
        t0 = time.time()
        status_area = st.empty()

        status_area.info("Extraindo texto...")
        with st.spinner("Extraindo texto..."):
            pages_text = []
            total_chars = 0
            with pdfplumber.open(uploaded) as pdf:
                total_pages = len(pdf.pages)
                for i, page in enumerate(pdf.pages, start=1):
                    txt = page.extract_text() or ""
                    total_chars += len(txt)
                    pages_text.append((i, txt))

        # Etapa 2: revisão
        status_area.info("Revisão em andamento, aguarde mais um pouquinho...")
        with st.spinner("Revisão em andamento, aguarde mais um pouquinho..."):
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            prompt_sistema = montar_prompt(glossario)

            ocorrencias = []
            for (page_num, txt) in pages_text:
                if not txt.strip():
                    # página sem texto extraível
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

                # Se parse falhou, registra erro
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

                # Normaliza e força pagina correta
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

        # Etapa 3: relatório
        status_area.info("Gerando relatório de erros...")
        with st.spinner("Gerando relatório de erros..."):
            dur_s = round(time.time() - t0, 2)

            # custo estimado (heurístico)
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

            # Campos adicionais (uso interno)
            df.insert(0, "usuario", nome)
            df.insert(1, "projeto", projeto)
            df.insert(2, "time", time_sel)
            df["tempo_revisao_s"] = dur_s
            df["custo_estimado_usd"] = custo_usd

            status_area.success(f"Concluído em {dur_s}s. Custo estimado: US$ {custo_usd}")

            st.dataframe(df, use_container_width=True)

            # Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Relatorio_Erros")

                # Aba de uso interno (log)
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

            # Log em memória (sessão)
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

            # Visão rápida do uso interno (sessão atual)
            with st.expander("Registro interno de uso (sessão atual)"):
                st.dataframe(pd.DataFrame(st.session_state.historico_uso), use_container_width=True)


# ============================================================
# 10) ROTEAMENTO
# ============================================================
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
