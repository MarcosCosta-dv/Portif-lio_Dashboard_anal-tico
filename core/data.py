# -*- coding: utf-8 -*-
import os, io
import numpy as np
import pandas as pd
from scipy import stats
import streamlit as st

# ---------- Leitura ----------
def carregar_df_padrao():
    base_dir = "data"; base_name = "df_selecionado"
    for ext in (".csv", ".xlsx", ".parquet"):
        caminho = os.path.join(base_dir, f"{base_name}{ext}")
        if os.path.exists(caminho):
            if ext == ".csv":      return pd.read_csv(caminho)
            if ext == ".xlsx":     return pd.read_excel(caminho)
            if ext == ".parquet":  return pd.read_parquet(caminho)
    return None

def carregar_df():
    df = carregar_df_padrao()
    if df is not None:
        st.success("Base carregada automaticamente de `data/df_selecionado.*`")
        return df

    st.info("Não encontrei `data/df_selecionado.*`. Faça upload:")
    up = st.file_uploader("Envie df_selecionado (CSV, XLSX ou PARQUET)", type=["csv", "xlsx", "parquet"])
    if up is None:
        return None

    try:
        nome = up.name.lower()
        if nome.endswith(".csv"):    return pd.read_csv(up)
        if nome.endswith(".xlsx"):   return pd.read_excel(up)
        if nome.endswith(".parquet"):return pd.read_parquet(io.BytesIO(up.read()))
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
    return None

# ---------- Tipagem simples ----------
def tipo_variavel(serie: pd.Series) -> str:
    if pd.api.types.is_numeric_dtype(serie):          return "Numérica"
    if pd.api.types.is_bool_dtype(serie):             return "Booleana"
    if pd.api.types.is_datetime64_any_dtype(serie):   return "Data/Hora"
    return "Categórica/Textual"

# ---------- Estatística ----------
def ic_media(serie, conf=0.95):
    x = pd.to_numeric(serie.dropna(), errors='coerce').dropna()
    n = len(x)
    if n < 2: return None
    media = x.mean()
    sd = x.std(ddof=1)
    se = sd / np.sqrt(n)
    alfa = 1 - conf
    tcrit = stats.t.ppf(1 - alfa/2, df=n-1)
    li = media - tcrit * se
    ls = media + tcrit * se
    return {"media": media, "n": n, "li": li, "ls": ls, "conf": conf}

def correlacao_pearson(x, y):
    x = pd.to_numeric(x, errors='coerce'); y = pd.to_numeric(y, errors='coerce')
    mask = x.notna() & y.notna()
    if mask.sum() < 3: return None
    r, p = stats.pearsonr(x[mask], y[mask])
    return r, p
