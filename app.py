import streamlit as st
import pdfplumber
import pandas as pd
from openai import OpenAI
import json
from io import BytesIO

# ============================================================
# SELO RICCA DE REVISÃO – PLATAFORMA DE REVISÃO EM PDF
# ============================================================

st.set_page_config(page_title="Selo Ricca de Revisão", layout="wide")

st.title("Selo Ricca de Revisão")
st.caption("Plataforma de revisão ortográfica, gramatical e editorial para PDFs institucionais")

st.info(
    "Esta plataforma realiza revisão automática assistida por IA.\n\n"
    "• O resultado é um RELATÓRIO DE OCORRÊNCIAS (Excel).\n"
    "• O texto NÃO é reescrito.\n"
    "• Recomenda-se iniciar com PDFs curtos para controle de custos."
)

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
        [
            "Sóbrio e institucional",
            "Técnico",
            "Leve e otimista",
            "Resiliente e de superação"
        ]
    )

diretrizes = st.text_area(
    "Outras diretrizes de linguagem",
    placeholder="Ex.: evitar voz passiva; manter linguagem impessoal"
)

glossario = st.text_area(
    "Glossário do cliente (uma regra por linha: termo incorreto = termo correto)",
    placeholder="empresa = companhia\nfuncionários = colaboradores"
)

st.divider()

# ============================================================
# UPLOAD DO PDF
# ============================================================

st.header("2. Documento para Revisão")
uploaded_file = st.file_uploader("Selecione o arquivo PDF", type=["pdf"])

# ============================================================
# PROMPT BASE
# ============================================================

def montar_prompt(padroes):
    return f"""
Você é um revisor editorial profissional especializado em relatórios institucionais
e de sustentabilidade em português do Brasil.

TAREFA:
Analise o texto fornecido SEM reescrevê-lo.

REGRAS OBRIGATÓRIAS:
1. Não reescreva o texto.
2. Não devolva o texto corrigido.
3. Apenas IDENTIFIQUE e LISTE ocorrências.
4. Se NÃO houver erros, responda com:
   {{
     "status": "Texto em conformidade",
     "ocorrencias": []
   }}

PADRÕES DO CLIENTE:
- Termo para instituição: {padroes['instituicao']}
- Termo para equipe: {padroes['equipe']}
- Tom do texto: {padroes['tom']}
- Diretrizes adicionais: {padroes['diretrizes']}
- Glossário: {padroes['glossario']}

FORMATO DE SAÍDA (JSON OBRIGATÓRIO):
{{
  "status": "Com ocorrências | Texto em conformidade",
  "ocorrencias": [
    {{
      "categoria": "Ortografia | Gramática | Numeração | Terminologia | Estilo | ODS | Elementos Visuais",
      "trecho": "trecho original",
      "sugestao": "sugestão de correção",
      "justificativa": "fundamentação técnica"
    }}
  ]
}}
"""

# ============================================================
# PROCESSAMENTO
# ============================================================

if uploaded_file and st.button("Iniciar revisão"):

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    padroes = {
        "instituicao": termo_instituicao or "não definido",
        "equipe": termo_equipe or "não definido",
        "tom": tom_texto,
        "diretrizes": diretrizes or "nenhuma",
        "glossario": glossario or "não informado"
    }

    prompt_sistema = montar_prompt(padroes)
    registros = []

    with st.spinner("Revisando documento..."):
        with pdfplumber.open(uploaded_file) as pdf:
            for numero_pagina, page in enumerate(pdf.pages, start=1):

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

                conteudo = resposta.choices[0].message.content

                try:
                    resultado = json.loads(conteudo)

                    for item in resultado.get("ocorrencias", []):
                        registros.append({
                            "Página": numero_pagina,
                            "Categoria": item.get("categoria"),
                            "Trecho": item.get("trecho"),
                            "Sugestão": item.get("sugestao"),
                            "Justificativa": item.get("justificativa")
                        })

                except json.JSONDecodeError:
                    registros.append({
                        "Página": numero_pagina,
                        "Categoria": "Erro de processamento",
                        "Trecho": "—",
                        "Sugestão": "—",
                        "Justificativa": "Resposta fora do formato JSON esperado"
                    })

    # ========================================================
    # RELATÓRIO
    # ========================================================

    if registros:
        df = pd.DataFrame(registros)

        st.success("Revisão concluída. Relatório gerado.")
        st.dataframe(df, use_container_width=True)

        buffer = BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)

        st.download_button(
            label="Baixar relatório em Excel",
            data=buffer,
            file_name="selo_ricca_relatorio_revisao.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Nenhuma ocorrência identificada. Texto em conformidade.")
