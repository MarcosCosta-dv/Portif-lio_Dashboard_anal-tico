# app_pages/home.py
# -*- coding: utf-8 -*-
import streamlit as st

def render():
    st.title("Meu Dashboard Profissional")
    st.subheader("Objetivo")
    st.write("Olá, sou Marcos Vinicius Costa, formado em Análise e Desenvolvimento de Sistemas, atualmente cursando o primeiro semestre de Engenharia de Software. Busco oportunidades desafiadoras que combinem minha base técnica com um ambiente propício ao crescimento pessoal e profissional.")

    col1, col2 = st.columns([2, 1], gap="large")
    with col1:
        st.markdown(
            """
            **Resumo**  
            - Área: Data/Tech/Negócios  
            - Foco: Monitoria/Observabilidade, Automação e Análise de Dados  
            - Contato: **silvacosta.mv@gmail.com**  
            - LinkedIn: [perfil](https://www.linkedin.com/in/marcosscosta)  
            """,
            unsafe_allow_html=True
        )
        st.link_button("🌐 Meu LinkedIn", "https://www.linkedin.com/in/marcosscosta", use_container_width=False)
    with col2:
        st.image("https://media.licdn.com/dms/image/v2/D4D03AQHfucq2OQme3w/profile-displayphoto-shrink_400_400/B4DZUZ43gCGcAk-/0/1739896093476?e=1758758400&v=beta&t=yY6Rp7XnJPx0BpP962vGVZn_txBGHlC44JVsBIypOH4", caption="(Marcos Costa)", use_container_width=True)
