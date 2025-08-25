# app_pages/home.py
# -*- coding: utf-8 -*-
import streamlit as st

def render():
    st.title("🏠 Meu Dashboard Profissional")
    st.subheader("Objetivo")
    st.write("Apresente-se brevemente: área de interesse, objetivo profissional e o tipo de problema de mercado analisado na aba **Análise de Dados**.")

    col1, col2 = st.columns([2, 1], gap="large")
    with col1:
        st.markdown(
            """
            **Resumo**  
            - Área: Data/Tech/Negócios  
            - Foco: Monitoria/Observabilidade, Automação e Análise de Dados  
            - Contato: **seu_email@exemplo.com**  
            - LinkedIn: [perfil](https://www.linkedin.com/in/marcosscosta)  
            """,
            unsafe_allow_html=True
        )
        st.link_button("🌐 Meu LinkedIn", "https://www.linkedin.com/in/marcosscosta", use_container_width=False)
    with col2:
        st.image("https://avatars.githubusercontent.com/u/9919?s=200&v=4", caption="(Exemplo de avatar)", use_container_width=True)

    st.divider()
    st.info("Dica: personalize textos acima e utilize a aba **Análise de Dados** para mostrar seu raciocínio com uma base real.")
