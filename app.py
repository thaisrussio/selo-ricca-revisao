import streamlit as st
import pdfplumber
import pandas as pd
import time
from openai import OpenAI
import base64

# ============================================================
# FUNÇÃO PARA CARREGAR FONTE AEONIK
# ============================================================
def carregar_aeonik():
    st.markdown(
        """
        <style>
        @font-face {
            font-family: 'Aeonik-Bold';
            src: url('assets/fonts/Aeonik-Bold.otf') format('opentype');
            font-weight: 700;
        }
        @font-face {
            font-family: 'Aeonik-Medium';
            src: url('assets/fonts/Aeonik-Medium.otf') format('opentype');
            font-weight: 500;
        }
        @font-face {
            font-family: 'Aeonik-Regular';
            src: url('assets/fonts/Aeonik-Regular.otf') format('opentype');
            font-weight: 400;
        }
        html, body, [class*="css"]  {
            font-family: 'Aeonik-Regular', sans-serif;
        }
        .bold { font-family: 'Aeonik-Bold'; }
        .medium { font-family: 'Aeonik-Medium'; }
        </style>
        """,
        unsafe_allow_html=True
    )

carregar_aeonik()

# ============================================================
# CONFIGURAÇÃO DE PÁGINA
# ============================================================
st.set_page_config(page_title="Selo Ricca de Revisão", layout="wide")

# ============================================================
# LOGIN
# ============================================================
def pagina_login():
    st.markdown(
        f"""
        <style>
        .login-background {{
            background-image: url("assets/Elementos/Patterns Escuras-03.png");
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center;
            height: 100vh;
        }}
        .logo {{
            display: flex;
            justify-content: center;
            margin-top: 80px;
        }}
        </style>
        <div class="login-background">
            <div class="logo">
                <img src="assets/logo.png/Vertical_Cor.png" width="300">
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.session_state['usuario'] = st.text_input("Usuário")
    st.session_state['senha'] = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if st.session_state['usuario'] == "riccarevisao" and st.session_state['senha'] == "Ricc@2026!":
            st.session_state['autenticado'] = True
            st.success("Login realizado com sucesso!")
        else:
            st.error("Usuário ou senha incorretos.")

# ============================================================
# PÁGINA DE INFORMAÇÕES DO PROJETO
# ============================================================
def pagina_informacoes():
    st.markdown(
        f"""
        <style>
        .info-background {{
            background-image: url("assets/Elementos/Patterns-06.png");
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center;
        }}
        .logo-horizontal {{
            display: flex;
            justify-content: left;
            margin-top: 10px;
        }}
        </style>
        <div class="info-background">
            <div class="logo-horizontal">
                <img src="assets/logo.png/Horizontal_Cor.png" width="200">
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.header("Informações do Projeto")
    nome_usuario = st.text_input("Seu nome")
    nome_projeto = st.text_input("Nome do projeto")
    time = st.selectbox(
        "Time",
        ["Magenta", "Lilás", "Ouro", "Menta", "Patrulha", "Outro"]
    )

    st.divider()
    
    st.header("Glossário e diretrizes do cliente")
    glossario = st.text_area(
        "Glossário do cliente (uma regra por linha: termo incorreto = termo correto)",
        placeholder="Ex.: diretor = Diretor-Presidente"
    )
    diretrizes = st.text_area(
        "Diretrizes adicionais",
        placeholder="Ex.: evitar voz passiva, priorizar linguagem impessoal"
    )
    
    return nome_usuario, nome_projeto, time, glossario, diretrizes

# ============================================================
# FUNÇÃO DE PROMPT
# ============================================================
def montar_prompt(glossario, diretrizes):
    return f"""
Você atuará como revisor(a) e analista de consistência editorial. Seu papel é revisar de forma minuciosa os arquivos PDF.

REGRAS:
1. Use somente o glossário fornecido pelo usuário.
2. Não altere conteúdo, tom ou números.
3. Números de 0 a 10 por extenso, exceto em tabelas.
4. Conferir elementos visuais, ODS, tipografia, legendas e layout.

GLOSSÁRIO:
{glossario or "Nenhum glossário fornecido"}

DIRETRIZES:
{diretrizes or "Nenhuma"}

FORMATO DE SAÍDA:
[
  {{
    "pagina": "número da página",
    "paragrafo": "número do parágrafo",
    "elemento": "parágrafo | título | tabela | gráfico | infográfico | box | legenda | rodapé | ODS",
    "trecho": "trecho original",
    "sugestao": "correção sugerida (somente se houver erro)",
    "tipo_erro": "Ortografia | Gramática | Concordância | Estilo | Numérico | Terminologia | Formatação | Visual | Legenda | ODS",
    "observacao": "comentário opcional"
  }}
]
"""

# ============================================================
# PÁGINA DE REVISÃO
# ============================================================
def pagina_revisao(nome_usuario, nome_projeto, time, glossario, diretrizes):
    st.markdown(
        f"""
        <style>
        .revisao-background {{
            background-image: url("assets/Elementos/Patterns Escuras_Prancheta 1.png");
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center;
        }}
        .logo-horizontal {{
            display: flex;
            justify-content: left;
            margin-top: 10px;
        }}
        </style>
        <div class="revisao-background">
            <div class="logo-horizontal">
                <img src="assets/logo.png/Horizontal_Cor.png" width="200">
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    uploaded_file = st.file_uploader("Selecione o arquivo PDF", type=["pdf"])
    
    if uploaded_file and st.button("Iniciar revisão"):
        if not nome_usuario or not nome_projeto:
            st.error("Preencha seu nome e o nome do projeto antes de iniciar.")
        else:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            prompt_sistema = montar_prompt(glossario, diretrizes)
            ocorrencias = []
            custo_estimado = 0.0
            tempo_inicio = time.time()
            
            with pdfplumber.open(uploaded_file) as pdf:
                paginas = pdf.pages
                st.success(f"Texto extraído de {len(paginas)} página(s).")
                
                for i, page in enumerate(paginas, start=1):
                    texto = page.extract_text()
                    if not texto:
                        continue
                    with st.spinner(f"Revisão em andamento (página {i}/{len(paginas)})..."):
                        try:
                            resposta = client.chat.completions.create(
                                model="gpt-4.1-mini",
                                temperature=0,
                                messages=[
                                    {"role": "system", "content": prompt_sistema},
                                    {"role": "user", "content": texto}
                                ]
                            )
                            resultado = eval(resposta.choices[0].message.content)
                            for item in resultado:
                                item["pagina"] = i
                                ocorrencias.append(item)
                            # Estimativa simples: $0.0004 por palavra
                            custo_estimado += 0.0004 * len(texto.split())
                        except Exception as e:
                            ocorrencias.append({
                                "pagina": i,
                                "paragrafo": "-",
                                "elemento": "parágrafo",
                                "trecho": "—",
                                "sugestao": "—",
                                "tipo_erro": "Erro de processamento",
                                "observacao": str(e)
                            })
            
            with st.spinner("Gerando relatório de erros e estimativa de custo..."):
                df = pd.DataFrame(ocorrencias)
                tempo_total = time.time() - tempo_inicio
                
                # Adiciona coluna de custo estimado
                df["custo_estimado_usd"] = round(custo_estimado, 4)
                
                st.success(f"Revisão concluída em {round(tempo_total, 2)} segundos. Custo estimado: ${round(custo_estimado, 4)}")
                st.dataframe(df, use_container_width=True)
                
                # Botão para download Excel
                output = pd.ExcelWriter("relatorio_revisao.xlsx", engine='openpyxl')
                df.to_excel(output, index=False)
                output.save()
                
                st.download_button(
                    "Baixar relatório em Excel",
                    data=open("relatorio_revisao.xlsx", "rb").read(),
                    file_name="selo_ricca_relatorio_revisao.xlsx"
                )
                
                # Histórico interno
                registro_uso = {
                    "Usuario": nome_usuario,
                    "Projeto": nome_projeto,
                    "Time": time,
                    "PDFs_Revisados": len(paginas),
                    "Tempo_Segundos": round(tempo_total,2),
                    "Custo_Estimado_USD": round(custo_estimado, 4)
                }
                st.session_state.setdefault("historico_uso", []).append(registro_uso)
                st.header("Relatório interno de uso")
                st.dataframe(pd.DataFrame(st.session_state["historico_uso"]))

# ============================================================
# MAIN
# ============================================================
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    pagina_login()
else:
    nome_usuario, nome_projeto, time, glossario, diretrizes = pagina_informacoes()
    pagina_revisao(nome_usuario, nome_projeto, time, glossario, diretrizes)
