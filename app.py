import streamlit as st
from openai import OpenAI

# Inicializa cliente OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("Selo Ricca de Revisão – Teste OpenAI")

texto = st.text_area("Cole um texto curto para revisão")

if st.button("Revisar texto") and texto.strip():
    with st.spinner("Revisando..."):
        resposta = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Você é um revisor editorial profissional em português do Brasil."
                },
                {
                    "role": "user",
                    "content": texto
                }
            ],
            temperature=0.2
        )

    st.subheader("Resultado")
    st.write(resposta.choices[0].message.content)
