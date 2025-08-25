# core/config.py
# -*- coding: utf-8 -*-
import streamlit as st

def configura_pagina(title: str = "App", wide: bool = True):
    """Configura layout global do Streamlit."""
    st.set_page_config(page_title=title, layout="wide")

def carrega_css(path_css: str):
    """Injeta CSS externo, se existir."""
    try:
        with open(path_css, "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except Exception:
        # CSS é opcional — evitar travar o app.
        pass

def get_appearance():
    """Lê preferências visuais da sessão."""
    tema = st.session_state.get("tema_graf", "dark")
    rmin = st.session_state.get("rmin_opt", 0)
    rmax = st.session_state.get("rmax_opt", 100)
    h    = st.session_state.get("graf_height", 560)
    w    = st.session_state.get("graf_width", 620)
    cols = st.session_state.get("layout_cols", 3)
    return tema, rmin, rmax, h, w, cols

def aparencia_sidebar():
    """Controles de aparência globais (valem para todas as páginas)."""
    with st.sidebar.expander("Aparência dos gráficos", expanded=True):
        st.radio("Tema", ["dark", "light"], index=0, horizontal=True, key="tema_graf")
        st.number_input("r (mín)", value=0, step=5, key="rmin_opt")
        st.number_input("r (máx)", value=100, step=5, key="rmax_opt")
        st.slider("Altura (px)", 320, 1000, 560, 20, key="graf_height")
        st.slider("Largura (px)", 420, 1200, 620, 20, key="graf_width")
        st.select_slider("Gráficos por linha", options=[1, 2, 3], value=3, key="layout_cols")

# Config da barra Plotly (centralizado)
PLOTLY_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"]
}
