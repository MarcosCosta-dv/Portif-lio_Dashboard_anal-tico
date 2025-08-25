# -*- coding: utf-8 -*-
import streamlit as st

def render():
    st.title("Meu Dashboard Profissional")
    st.subheader("Objetivo")
    st.write(
        "Apresente-se brevemente: área de interesse, objetivo profissional e o tipo de problema de mercado "
        "que você analisa na aba de Análise de Dados."
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(
            """
            <div class="card">
            <strong>Resumo</strong><br>
            • Área: Data/Tech/Negócios<br>
            • Foco: Monitoria/Observabilidade, Automação e Análise de Dados<br>
            • Contato: <strong>seu_email@exemplo.com</strong><br>
            <a class="btn-primary" href="https://www.linkedin.com/in/marcosscosta" target="_blank">🌐 Meu LinkedIn</a>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.image("https://avatars.githubusercontent.com/u/9919?s=200&v=4", caption="(Exemplo de avatar)")
