import streamlit as st
import pdfplumber
import language_tool_python
import pandas as pd
import re

# ============================================================
# SELO RICCA DE REVISÃO — APLICAÇÃO STREAMLIT
# ============================================================

st.set_page_config(
    page_title="Selo Ricca de Revisão",
    layout="wide"
)

# ============================================================
# PÁGINA INICIAL — TÍTULO E DISCLAIMERS
# ============================================================

st.title("Selo Ricca de Revisão")

st.markdown("""
### Revisão Ortográfica, Gramatical e Editorial Assistida

**O que esta plataforma faz:**
- Realiza revisão **ortográfica, gramatical e normativa** em português (Brasil)
- Aplica **padrões linguísticos definidos pelo cliente**
- Verifica **consistência terminológica, numérica e estilística**
- Gera um **relatório técnico detalhado**, com página, regra aplicada e sugestão

**O que esta plataforma NÃO faz:**
- Não altera automaticamente o PDF original
- Não substitui a revisão humana especializada
- Não garante leitura perfeita de gráficos complexos ou imagens ilegíveis
- Não interpreta intenções estratégicas do texto

**Importante:**
Este é um sistema de **revisão assistida**, destinado a apoiar decisões editoriais.
Toda correção sugerida deve ser validada por um(a) revisor(a) responsável.
""")

st.divider()

# ============================================================
# PADRÕES DO CLIENTE
# ============================================================

st.header("1. Padrões do Cliente")

col1, col2, col3 = st.columns(3)

with col1:
    termo_instituicao = st.text_input("Termo para a instituição", placeholder="ex.: organização")

with col2:
    termo_equipe = st.text_input("Termo para a equipe", placeholder="ex.: colaboradores")

with col3:
    tom_texto = st.selectbox(
        "Tom do texto",
        ["Sóbrio e institucional", "Técnico", "Leve e otimista", "Resiliente e de superação"]
    )

diretrizes = st.text_area(
    "Outras diretrizes de linguagem",
    placeholder="Descreva aqui regras específicas do cliente (opcional)"
)

glossario = st.text_area(
    "Glossário do cliente (uma regra por linha: termo incorreto = termo correto)",
    placeholder="empresa = companhia\nfuncionários = colaboradores"
)

# Processa glossário
regras_glossario = {}
for linha in glossario.splitlines():
    if "=" in linha:
        errado, correto = linha.split("=", 1)
        regras_glossario[errado.strip().lower()] = correto.strip()

st.divider()

# ============================================================
# UPLOAD DO PDF
# ============================================================

st.header("2. Documento para Revisão")

uploaded_file = st.file_uploader("Selecione o arquivo PDF", type=["pdf"])

# ============================================================
# PROCESSAMENTO
# ============================================================

if uploaded_file and st.button("Iniciar revisão"):
    tool = language_tool_python.LanguageToolPublicAPI('pt-BR')
    erros = []

    with pdfplumber.open(uploaded_file) as pdf:
        for num_pagina, page in enumerate(pdf.pages, start=1):
            texto = page.extract_text() or ""

            # Revisão linguística automática
            matches = tool.check(texto)
            for m in matches:
                erros.append({
                    "Página": num_pagina,
                    "Categoria": "Linguagem",
                    "Severidade": "Crítico",
                    "Regra": m.ruleIssueType,
                    "Trecho original": texto[m.offset:m.offset + m.errorLength],
                    "Sugestão": ", ".join(m.replacements[:3]),
                    "Observação / justificativa": "Norma-padrão da língua portuguesa"
                })

            # Números de 0 a 10
            for match in re.finditer(r"\b([0-9]|10)\b", texto):
                erros.append({
                    "Página": num_pagina,
                    "Categoria": "Numeração",
                    "Severidade": "Médio",
                    "Regra": "Números de zero a dez por extenso",
                    "Trecho original": match.group(),
                    "Sugestão": "Escrever por extenso",
                    "Observação / justificativa": "Verificar se não se trata de medida técnica ou tabela"
                })

            # Glossário
            for termo_errado, termo_correto in regras_glossario.items():
                if termo_errado in texto.lower():
                    erros.append({
                        "Página": num_pagina,
                        "Categoria": "Terminologia",
                        "Severidade": "Médio",
                        "Regra": "Glossário do cliente",
                        "Trecho original": termo_errado,
                        "Sugestão": termo_correto,
                        "Observação / justificativa": "Padronização conforme padrão do cliente"
                    })

    if erros:
        df = pd.DataFrame(erros)
        st.success("Revisão concluída. Relatório gerado.")
        st.dataframe(df, use_container_width=True)

        st.download_button(
            "Baixar relatório (Excel)",
            df.to_excel(index=False),
            file_name="selo_ricca_relatorio_revisao.xlsx"
        )
    else:
        st.info("Nenhuma ocorrência relevante encontrada segundo os critérios definidos.")
