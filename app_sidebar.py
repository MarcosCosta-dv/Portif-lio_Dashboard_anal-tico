# -*- coding: utf-8 -*-
import streamlit as st
from core.config import configura_pagina, carrega_css, aparencia_sidebar
from pages import home, formacao, skills, analise

# ===== Configurações globais =====
configura_pagina(title="CP1 - Dashboard Profissional", wide=True)
carrega_css("assets/styles.css")

# ===== Menu lateral (router) =====
st.sidebar.markdown("## Navegação")
pagina = st.sidebar.radio("Ir para:", ["Home", "Formação e Experiência", "Skills", "Análise de Dados"])

st.sidebar.markdown("---")
st.sidebar.markdown("**Dica:** salve a base em `data/df_selecionado.(csv|xlsx|parquet)`")

# Aparência dos gráficos (controle global via session_state)
aparencia_sidebar()

# ===== Roteamento =====
if pagina == "Home":
    home.render()
elif pagina == "Formação e Experiência":
    formacao.render()
elif pagina == "Skills":
    skills.render()
else:
    analise.render()
