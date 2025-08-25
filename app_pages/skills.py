# app_pages/skills.py
# -*- coding: utf-8 -*-
import streamlit as st
from visuals.radar import radar_plotly   # importa do visuals/radar.py

CSS = """
section.main > div.block-container h1:first-of-type {
  text-align: center;
  margin-bottom: 0.5rem;
}
section.main h2 {
  text-align: left !important;
  margin-top: 1.2rem;
  margin-bottom: 0.6rem;
}
"""
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

def render():
    st.title("🧠 Skills")

    with st.sidebar.expander("Aparência (Skills)", expanded=False):
        tema_graf   = st.radio("Tema", ["dark", "light"], index=0, horizontal=True)
        rmin_opt    = st.number_input("r (mín)", value=0, step=5)
        rmax_opt    = st.number_input("r (máx)", value=100, step=5)
        graf_height = st.slider("Altura (px)", 320, 1000, 560, 20)
        mostrar_meta = st.toggle("Mostrar baseline/meta = 80", value=True)

    baseline = 80 if mostrar_meta else None
    plotly_cfg = {"displaylogo": False,
                  "modeBarButtonsToRemove": ["lasso2d","select2d","autoScale2d"]}

    skills_dev   = {"HTML5": 80, "CSS": 78, "JavaScript": 76, "Python": 85, "SQL": 80, "Java": 65}
    skills_tools = {"Splunk": 82, "Splunk Cloud": 80, "Grafana": 75, "BigQuery": 70,
                    "Excel": 88, "Power Automate": 78}
    skills_soft  = {"Comunicação": 86, "Pensamento Crítico": 84, "Raciocínio Lógico": 85,
                    "Trabalho em Equipe": 90, "Organização": 82, "Proatividade": 88}

    st.markdown("## Desenvolvimento")
    st.plotly_chart(radar_plotly("", skills_dev,
                                 baseline_val=baseline, rmin=rmin_opt, rmax=rmax_opt,
                                 tema=tema_graf, height=graf_height, width=600),
                    use_container_width=True, config=plotly_cfg)

    st.markdown("## Ferramentas & Plataformas")
    st.plotly_chart(radar_plotly("", skills_tools,
                                 baseline_val=baseline, rmin=rmin_opt, rmax=rmax_opt,
                                 tema=tema_graf, height=graf_height, width=600),
                    use_container_width=True, config=plotly_cfg)

    st.markdown("## Soft Skills")
    st.plotly_chart(radar_plotly("", skills_soft,
                                 baseline_val=baseline, rmin=rmin_opt, rmax=rmax_opt,
                                 tema=tema_graf, height=graf_height, width=600),
                    use_container_width=True, config=plotly_cfg)
