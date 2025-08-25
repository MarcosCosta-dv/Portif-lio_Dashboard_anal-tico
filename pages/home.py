# -*- coding: utf-8 -*-
import streamlit as st

def render():
    st.title("Meu Dashboard Profissional")
    st.subheader("Objetivo")
    st.write("Apresente-se brevemente: área de interesse, objetivo profissional e o tipo de problema de mercado que você analisa na aba de Análise de Dados.")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(
            """
            **Resumo**  
            - Área: Data/Tech/Negócios  
            - Foco: Monitoria/Observabilidade, Automação e Análise de Dados  
            - Contato: **seu_email@exemplo.com**  
            - [![LinkedIn](https://img.shields.io/badge/LinkedIn-blue?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/marcosscosta)  
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            """
            <a href="https://www.linkedin.com/in/marcosscosta" target="_blank">
                <button class="btn-primary">
                    🌐 Meu LinkedIn
                </button>
            </a>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.image("https://avatars.githubusercontent.com/u/9919?s=200&v=4", caption="(Exemplo de avatar)")
