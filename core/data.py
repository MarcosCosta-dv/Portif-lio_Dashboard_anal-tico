# core/data.py
# -*- coding: utf-8 -*-
import os, io
import numpy as np
import pandas as pd
from scipy import stats
import streamlit as st

# ----------------------------
# Localização automática do arquivo padrão
# ----------------------------
def _candidatos_df_padrao():
    """Gera caminhos candidatos para df_selecionado.*"""
    base_name = "df_selecionado"
    pastas = ["data", ".", "/mnt/data"]
    exts = [".csv", ".xlsx", ".parquet"]
    for pasta in pastas:
        for ext in exts:
            yield os.path.join(pasta, f"{base_name}{ext}")

def _primeiro_existente():
    for caminho in _candidatos_df_padrao():
        if os.path.exists(caminho):
            return caminho
    return None

@st.cache_data(show_spinner=False)
def _ler_df(caminho: str):
    """Leitura com cache do Streamlit."""
    if caminho.lower().endswith(".csv"):
        return pd.read_csv(caminho)
    if caminho.lower().endswith(".xlsx"):
        return pd.read_excel(caminho)
    if caminho.lower().endswith(".parquet"):
        return pd.read_parquet(caminho)
    raise ValueError(f"Extensão não suportada: {caminho}")

def carregar_df(stmod=st):
    """
    Tenta carregar automaticamente `df_selecionado.*`. 
    Caso não encontre, exibe uploader e lê o arquivo enviado.
    Retorna um DataFrame ou None.
    """
    caminho = _primeiro_existente()
    if caminho:
        stmod.success(f"Base carregada automaticamente de `{caminho}`")
        return _ler_df(caminho)

    stmod.info("Não encontrei `df_selecionado.*`. Faça upload (CSV, XLSX ou PARQUET):")
    up = stmod.file_uploader("Envie df_selecionado.*", type=["csv", "xlsx", "parquet"])
    if up is None:
        return None

    try:
        nome = up.name.lower()
        if nome.endswith(".csv"):
            return pd.read_csv(up)
        if nome.endswith(".xlsx"):
            return pd.read_excel(up)
        if nome.endswith(".parquet"):
            # alguns providers entregam BytesIO
            data = up.read() if hasattr(up, "read") else up.getvalue()
            return pd.read_parquet(io.BytesIO(data))
        stmod.error("Formato não suportado.")
    except Exception as e:
        stmod.error(f"Erro ao ler o arquivo: {e}")
    return None

# ----------------------------
# Tipagem simples
# ----------------------------
def tipo_variavel(serie: pd.Series) -> str:
    if pd.api.types.is_numeric_dtype(serie):          return "Numérica"
    if pd.api.types.is_bool_dtype(serie):             return "Booleana"
    if pd.api.types.is_datetime64_any_dtype(serie):   return "Data/Hora"
    return "Categórica/Textual"

# ----------------------------
# Estatística utilitária
# ----------------------------
def ic_media(serie, conf=0.95):
    """
    Intervalo de confiança da média (t de Student).
    Retorna (li, ls, media, n) ou None se amostra insuficiente.
    """
    x = pd.to_numeric(pd.Series(serie).dropna(), errors='coerce').dropna()
    n = len(x)
    if n < 2:
        return None
    media = x.mean()
    sd = x.std(ddof=1)
    se = sd / np.sqrt(n)
    alfa = 1 - conf
    tcrit = stats.t.ppf(1 - alfa/2, df=n-1)
    li, ls = media - tcrit*se, media + tcrit*se
    return li, ls, media, n

def correlacao_pearson(x, y):
    """
    Correlação de Pearson com coerção para numérico.
    Retorna (r, p) ou None se não houver dados suficientes.
    """
    xv = pd.to_numeric(pd.Series(x), errors="coerce")
    yv = pd.to_numeric(pd.Series(y), errors="coerce")
    mask = xv.notna() & yv.notna()
    xv = xv[mask]; yv = yv[mask]
    if len(xv) < 3:
        return None
    r, p = stats.pearsonr(xv, yv)
    return r, p
