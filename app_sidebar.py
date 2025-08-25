# -*- coding: utf-8 -*-
import streamlit as st
from core.config import configura_pagina, carrega_css, aparencia_sidebar
from app_pages import home, formacao, skills, analise

# ===== Configurações globais =====
configura_pagina(title="CP1 - Dashboard Profissional", wide=True)
carrega_css("assets/styles.css")

# ===== Sidebar (roteador) =====
st.sidebar.markdown("## Navegação")
pagina = st.sidebar.radio("Ir para:", ["Home", "Formação e Experiência", "Skills", "Análise de Dados"])


# ===== Roteamento =====
if pagina == "Home":
    home.render()
elif pagina == "Formação e Experiência":
    formacao.render()
elif pagina == "Skills":
    skills.render()
else:
    analise.render()
