# -*- coding: utf-8 -*-
import streamlit as st

def render():
    st.title("Formação e Experiência")

    st.subheader("Sobre mim")
    st.markdown(
        """
        **Experiência em Desenvolvimento:** HTML5, JavaScript, CSS, Python, SQL e Java.  
        **Proficiência em Software:** Pacote Office e Adobe.  
        **Habilidades Comportamentais:** Comunicativo, pensamento crítico, raciocínio lógico e trabalho em equipe.
        """
    )

    st.subheader("Experiência Profissional")
    st.markdown(
        """
        **C6 Bank — Analista Jr (Monitoriação)** *(fev/2025 – atual, remoto)*  
        - Splunk, automações em Python e Power Automate.  
        - Stack: Splunk Cloud, BigQuery, Excel, Salesforce, ServiceNow, Azure DevOps, RunDeck, Grafana.
        """
    )
    st.markdown(
        """
        **C6 Bank — Monitoriação 24x7 (Estágio)** *(jun/2024 – fev/2025, presencial)*  
        - Monitoria de funcionalidades e lançamentos.  
        - Análise de bases, indicadores, dashboards e logs.  
        - Stack: Azure DevOps, PostgreSQL, Grafana, ServiceNow, etc.
        """
    )

    st.markdown("---")
    st.markdown("📬 **Contato:** [LinkedIn /marcosscosta](https://www.linkedin.com/in/marcosscosta)", unsafe_allow_html=True)
