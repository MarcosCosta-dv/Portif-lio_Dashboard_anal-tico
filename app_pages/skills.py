# -*- coding: utf-8 -*-
import streamlit as st
from visuals.radar import radar_plotly
from core.config import get_appearance, PLOTLY_CONFIG

def render():
    st.title("Skills")

    tema, rmin, rmax, h, w, layout_cols = get_appearance()
    skills_dev   = {"HTML5": 80, "CSS": 78, "JavaScript": 76, "Python": 85, "SQL": 80, "Java": 65}
    skills_tools = {"Splunk": 82, "Splunk Cloud": 80, "Grafana": 75, "BigQuery": 70, "Excel": 88, "Power Automate": 78}
    skills_soft  = {"Comunicação": 86, "Pensamento Crítico": 84, "Raciocínio Lógico": 85, "Trabalho em Equipe": 90, "Organização": 82, "Proatividade": 88}
    baseline = 80

    if layout_cols == 3:   cols = st.columns(3)
    elif layout_cols == 2: cols = st.columns(2)
    else:                  cols = [st.container(), st.container(), st.container()]

    with cols[0]:
        st.subheader("Desenvolvimento")
        st.plotly_chart(
            radar_plotly("Desenvolvimento", skills_dev, baseline_val=baseline,
                         rmin=rmin, rmax=rmax, tema=tema, height=h, width=w),
            use_container_width=False, config=PLOTLY_CONFIG, key="radar_dev_main"
        )
    with cols[1]:
        st.subheader("Ferramentas & Plat.")
        st.plotly_chart(
            radar_plotly("Ferramentas & Plataformas", skills_tools, baseline_val=baseline,
                         rmin=rmin, rmax=rmax, tema=tema, height=h, width=w),
            use_container_width=False, config=PLOTLY_CONFIG, key="radar_tools_main"
        )
    with cols[2]:
        st.subheader("Soft Skills")
        st.plotly_chart(
            radar_plotly("Soft Skills", skills_soft, baseline_val=baseline,
                         rmin=rmin, rmax=rmax, tema=tema, height=h, width=w),
            use_container_width=False, config=PLOTLY_CONFIG, key="radar_soft_main"
        )
