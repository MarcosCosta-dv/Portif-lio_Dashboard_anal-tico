# app_pages/analise.py
# -*- coding: utf-8 -*-
import re
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

from core.data import carregar_df, correlacao_pearson

sns.set_theme(style="whitegrid")

# =========================
# Auto‑mapeamento (sinônimos)
# =========================
def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9_]+", " ", s.lower().strip())

def _find_by_patterns(columns, patterns):
    norm_cols = {c: _norm(c) for c in columns}
    # match exato
    for c, nc in norm_cols.items():
        for p in patterns:
            if re.fullmatch(p, nc):
                return c
    # contém
    for c, nc in norm_cols.items():
        for p in patterns:
            if re.search(p, nc):
                return c
    return None

ROLE_SYNONYMS = {
    # Vendas
    "data_pedido":      [r"^date$", r"order[\s_]*date", r"data[\s_]*pedido"],
    "valor_pedido":     [r"^amount$", r"valor[\s_]*pedido", r"order[\s_]*amount", r"total[\s_]*order"],
    "categoria":        [r"^category$", r"categoria"],
    "produto":          [r"^product$", r"product[\s_]*name", r"style", r"produto", r"descri[cç][aã]o", r"descricao"],
    "tipo_cliente":     [r"^b2b$", r"tipo[\s_]*cliente", r"customer[\s_]*type"],
    "regiao":           [r"ship[\s_]*state", r"ship[\s_]*city", r"estado", r"cidade", r"regi[aã]o", r"uf"],
    "quantidade":       [r"^qty$", r"quantity", r"quantidade"],
    # Cancel/Entregas
    "status_pedido":    [r"^status$", r"order[\s_]*status", r"situa[cç][aã]o"],
    "tipo_envio":       [r"^fulfil.*by$", r"^fulfilled[\s_]*by$", r"^fulfillment$", r"^fulfilment$", r"tipo[\s_]*envio"],
    "courier_status":   [r"^courier[\s_]*status$", r"ship[\s_]*service[\s_]*level", r"nível[\s_]*servi[cç]o"],
    # Produtos
    "tamanho":          [r"^size$", r"tamanho"],
    "valor_unitario":   [r"unit[\s_]*price", r"valor[\s_]*unit[aá]rio", r"pre[cç]o[\s_]*unit[aá]rio"],
    # Promoção
    "tem_promocao":     [r"promotion[\s_]*id", r"promo[cç][aã]o", r"has[\s_]*promo", r"applied[\s_]*promo"],
    # Entrega real (se existir)
    "data_entrega":     [r"deliv[\s_]*date", r"data[\s_]*entrega"]
}

def automap(df_local: pd.DataFrame) -> dict:
    m = {}
    cols = df_local.columns.tolist()
    for role, pats in ROLE_SYNONYMS.items():
        m[role] = _find_by_patterns(cols, pats)
    return m

def has(colmap, key, df):
    return key in colmap and colmap[key] in df.columns and colmap[key] is not None

# =========================
# Página
# =========================
def render():
    st.title("📊 Análise de Dados — CP1")

    # 1) Carregar base
    df = carregar_df(st)
    if df is None:
        st.warning("Carregue a base para continuar.")
        st.stop()

    # 2) Auto‑map
    colmap = automap(df)
    dfx = df.copy()

    # conversões úteis
    if has(colmap, "data_pedido", df):
        dfx[colmap["data_pedido"]] = pd.to_datetime(dfx[colmap["data_pedido"]], errors="coerce")
    if has(colmap, "data_entrega", df):
        dfx[colmap["data_entrega"]] = pd.to_datetime(dfx[colmap["data_entrega"]], errors="coerce")
    if has(colmap, "valor_pedido", df):
        dfx[colmap["valor_pedido"]] = pd.to_numeric(dfx[colmap["valor_pedido"]], errors="coerce")
    if has(colmap, "quantidade", df):
        dfx[colmap["quantidade"]] = pd.to_numeric(dfx[colmap["quantidade"]], errors="coerce")
    if has(colmap, "valor_unitario", df):
        dfx[colmap["valor_unitario"]] = pd.to_numeric(dfx[colmap["valor_unitario"]], errors="coerce")

    st.caption("Mapeamento detectado:")
    st.dataframe(pd.DataFrame([{"papel": k, "coluna": v} for k, v in colmap.items() if v], columns=["papel","coluna"]))

    # 3) Abas (um gráfico por pergunta)
    aba_v, aba_c, aba_l, aba_promo, aba_prod, aba_stat = st.tabs(
        ["1) Vendas", "2) Cancelamentos/Entregas", "3) Logística", "4) Promoções", "5) Produtos", "6) Estatística"]
    )

    # --------------------- 1) VENDAS ---------------------
    with aba_v:
        st.subheader("Vendas")

        # Volume por mês
        if has(colmap, "data_pedido", df):
            st.markdown("**Volume de pedidos por mês (sazonalidade)**")
            dd = dfx.dropna(subset=[colmap["data_pedido"]]).copy()
            dd["mes"] = dd[colmap["data_pedido"]].dt.to_period("M").dt.to_timestamp()
            g = dd.groupby("mes").size().reset_index(name="pedidos")
            if not g.empty:
                fig, ax = plt.subplots()
                ax.plot(g["mes"], g["pedidos"], marker="o")
                ax.set_title("Pedidos por mês"); ax.set_xlabel("Mês"); ax.set_ylabel("Nº de pedidos")
                st.pyplot(fig, clear_figure=True)
        else:
            st.info("Sem coluna de data do pedido.")

        # Ticket médio por categoria/produto
        if has(colmap, "valor_pedido", df) and (has(colmap, "categoria", df) or has(colmap, "produto", df)):
            alvo = colmap["categoria"] if has(colmap, "categoria", df) else colmap["produto"]
            st.markdown(f"**Ticket médio por {'categoria' if has(colmap,'categoria',df) else 'produto'}**")
            tkm = dfx.groupby(alvo)[colmap["valor_pedido"]].mean().sort_values(ascending=False).head(15)
            fig, ax = plt.subplots(figsize=(7,4))
            sns.barplot(x=tkm.values, y=tkm.index, ax=ax)
            ax.set_xlabel("Ticket médio (R$)"); ax.set_ylabel(alvo); ax.set_title("Top 15")
            st.pyplot(fig, clear_figure=True)

        # Produtos/Categorias mais vendidos
        if has(colmap, "produto", df):
            st.markdown("**Produtos mais vendidos (contagem)**")
            vc = dfx[colmap["produto"]].value_counts().head(15)
            fig, ax = plt.subplots(figsize=(7,4))
            sns.barplot(x=vc.values, y=vc.index, ax=ax)
            ax.set_xlabel("Pedidos"); ax.set_ylabel("Produto"); ax.set_title("Top 15")
            st.pyplot(fig, clear_figure=True)

        if has(colmap, "categoria", df):
            st.markdown("**Categorias mais vendidas (contagem)**")
            vc = dfx[colmap["categoria"]].value_counts().head(15)
            fig, ax = plt.subplots(figsize=(7,4))
            sns.barplot(x=vc.values, y=vc.index, ax=ax)
            ax.set_xlabel("Pedidos"); ax.set_ylabel("Categoria"); ax.set_title("Top 15")
            st.pyplot(fig, clear_igure=True)  # corrigido: clear_figure

        # Regiões mais lucrativas
        if has(colmap, "regiao", df) and has(colmap, "valor_pedido", df):
            st.markdown("**Regiões mais lucrativas (soma de vendas)**")
            gr = dfx.groupby(colmap["regiao"])[colmap["valor_pedido"]].sum().sort_values(ascending=False).head(15)
            fig, ax = plt.subplots(figsize=(7,4))
            sns.barplot(x=gr.values, y=gr.index, ax=ax)
            ax.set_xlabel("Vendas (R$)"); ax.set_ylabel("Região"); ax.set_title("Top 15")
            st.pyplot(fig, clear_figure=True)

        # Proporção B2B x B2C
        if has(colmap, "tipo_cliente", df):
            st.markdown("**Proporção de vendas B2B x B2C**")
            cnt = dfx[colmap["tipo_cliente"]].value_counts()
            fig, ax = plt.subplots()
            ax.pie(cnt.values, labels=cnt.index, autopct="%1.1f%%", startangle=90)
            ax.axis("equal"); ax.set_title("B2B vs B2C")
            st.pyplot(fig, clear_figure=True)

    # ---------------- 2) CANCELAMENTOS / ENTREGAS ----------------
    with aba_c:
        st.subheader("Cancelamentos e Entregas")
        if has(colmap, "status_pedido", df):
            status_col = colmap["status_pedido"]
            total = len(dfx)
            cancel_mask = dfx[status_col].astype(str).str.lower().str.contains("cancel", na=False)
            n_cancel = int(cancel_mask.sum())
            st.metric("Taxa de cancelamento", f"{(100*n_cancel/total):.2f}%")

            fig, ax = plt.subplots()
            ax.pie([n_cancel, total-n_cancel], labels=["Cancelado","Demais"], autopct="%1.1f%%", startangle=90)
            ax.axis("equal"); ax.set_title("Cancelamento (geral)")
            st.pyplot(fig, clear_figure=True)

            if has(colmap, "categoria", df):
                st.markdown("**Índice de cancelamento por categoria**")
                tmp = dfx.assign(_cancel=cancel_mask.astype(int))
                tab = tmp.groupby(colmap["categoria"])["_cancel"].mean().sort_values(ascending=False).head(15)
                fig, ax = plt.subplots(figsize=(7,4))
                sns.barplot(x=(100*tab.values), y=tab.index, ax=ax)
                ax.set_xlabel("% cancelado"); ax.set_ylabel("Categoria")
                ax.set_title("Top 15 categorias por taxa de cancelamento")
                st.pyplot(fig, clear_figure=True)

            if has(colmap, "tamanho", df):
                st.markdown("**Índice de cancelamento por tamanho (Size)**")
                tmp = dfx.assign(_cancel=cancel_mask.astype(int))
                tab = tmp.groupby(colmap["tamanho"])["_cancel"].mean().sort_values(ascending=False)
                fig, ax = plt.subplots(figsize=(7,4))
                sns.barplot(x=(100*tab.values), y=tab.index, ax=ax)
                ax.set_xlabel("% cancelado"); ax.set_ylabel("Size")
                ax.set_title("Cancelamento por tamanho")
                st.pyplot(fig, clear_figure=True)

            if has(colmap, "tipo_envio", df):
                st.markdown("**Cancelamento por tipo de envio (Amazon x Vendedor)**")
                tmp = dfx.assign(_cancel=cancel_mask.astype(int))
                tab = tmp.groupby(colmap["tipo_envio"])["_cancel"].mean().sort_values(ascending=False)
                fig, ax = plt.subplots()
                sns.barplot(x=(100*tab.values), y=tab.index, ax=ax)
                ax.set_xlabel("% cancelado"); ax.set_ylabel("Responsável pelo envio")
                ax.set_title("Cancelamento por tipo de envio")
                st.pyplot(fig, clear_figure=True)

            if has(colmap, "courier_status", df):
                st.markdown("**Distribuição de Courier Status (proxy de tempo de entrega)**")
                vc = dfx[colmap["courier_status"]].value_counts().head(15)
                fig, ax = plt.subplots(figsize=(7,4))
                sns.barplot(x=vc.values, y=vc.index, ax=ax)
                ax.set_xlabel("Pedidos"); ax.set_ylabel("Courier Status")
                ax.set_title("Courier Status (Top 15)")
                st.pyplot(fig, clear_figure=True)
        else:
            st.info("Coluna de Status não encontrada para medir cancelamentos.")

    # ------------------------ 3) LOGÍSTICA ------------------------
    with aba_l:
        st.subheader("Logística")

        if has(colmap, "data_pedido", df) and has(colmap, "data_entrega", df):
            st.markdown("**Tempo entre pedido e entrega (dias)**")
            dd = dfx.dropna(subset=[colmap["data_pedido"], colmap["data_entrega"]]).copy()
            dd["dias"] = (dd[colmap["data_entrega"]] - dd[colmap["data_pedido"]]).dt.days
            st.metric("Tempo médio (dias)", f"{dd['dias'].mean():.2f}")
            fig, ax = plt.subplots()
            sns.histplot(dd["dias"], kde=True, ax=ax)
            ax.set_xlabel("dias"); ax.set_title("Distribuição do tempo de entrega")
            st.pyplot(fig, clear_figure=True)
        else:
            st.info("Sem coluna de data de entrega. Se existir, nomeie como 'Delivered Date' ou similar.")

        if has(colmap, "tipo_envio", df) and has(colmap, "status_pedido", df):
            st.markdown("**Performance por tipo de envio (entregue vs cancelado)**")
            entreg_mask = dfx[colmap["status_pedido"]].astype(str).str.lower().str.contains("entreg", na=False)
            cancel_mask = dfx[colmap["status_pedido"]].astype(str).str.lower().str.contains("cancel", na=False)
            tmp = dfx.assign(_entregue=entreg_mask.astype(int), _cancel=cancel_mask.astype(int))
            tab = tmp.groupby(colmap["tipo_envio"])[["_entregue","_cancel"]].mean().sort_values("_entregue", ascending=False)
            fig, ax = plt.subplots()
            tab.plot(kind="bar", ax=ax)
            ax.set_ylabel("taxa média"); ax.set_title("Entregue vs Cancelado por tipo de envio")
            st.pyplot(fig, clear_figure=True)

        if has(colmap, "regiao", df) and has(colmap, "status_pedido", df):
            st.markdown("**Regiões com maior taxa de cancelamento**")
            cancel_mask = dfx[colmap["status_pedido"]].astype(str).str.lower().str.contains("cancel", na=False)
            tmp = dfx.assign(_cancel=cancel_mask.astype(int))
            tab = tmp.groupby(colmap["regiao"])["_cancel"].mean().sort_values(ascending=False).head(15)
            fig, ax = plt.subplots(figsize=(7,4))
            sns.barplot(x=(100*tab.values), y=tab.index, ax=ax)
            ax.set_xlabel("% cancelado"); ax.set_ylabel("Região")
            ax.set_title("Top 15 regiões por taxa de cancelamento")
            st.pyplot(fig, clear_figure=True)

        if has(colmap, "tipo_envio", df) and has(colmap, "status_pedido", df):
            st.markdown("**Taxa de entrega por responsável (Fulfilled By)**")
            entreg_mask = dfx[colmap["status_pedido"]].astype(str).str.lower().str.contains("entreg", na=False)
            tmp = dfx.assign(_entregue=entreg_mask.astype(int))
            tab = tmp.groupby(colmap["tipo_envio"])["_entregue"].mean().sort_values(ascending=False)
            fig, ax = plt.subplots()
            sns.barplot(x=(100*tab.values), y=tab.index, ax=ax)
            ax.set_xlabel("% entregue"); ax.set_ylabel("Responsável pelo envio")
            ax.set_title("Entrega por responsável")
            st.pyplot(fig, clear_figure=True)

    # ------------------------- 4) PROMOÇÕES ------------------------
    with aba_promo:
        st.subheader("Promoções")
        if has(colmap, "tem_promocao", df):
            promo = dfx[colmap["tem_promocao"]]
            promo_bool = promo.astype(str).str.strip().str.lower().isin(["1","true","sim","yes","y"]) | promo.notna()
            dfx["_has_promo"] = promo_bool

            if has(colmap, "valor_pedido", df):
                st.markdown("**Ticket médio: com x sem promoção**")
                tab = dfx.groupby("_has_promo")[colmap["valor_pedido"]].mean().rename(
                    {True:"Com Promoção", False:"Sem Promoção"})
                fig, ax = plt.subplots()
                sns.barplot(x=tab.index.map({True:"Com Promoção", False:"Sem Promoção"}), y=tab.values, ax=ax)
                ax.set_ylabel("Ticket médio (R$)"); ax.set_xlabel(""); ax.set_title("Ticket médio")
                st.pyplot(fig, clear_figure=True)

            if has(colmap, "quantidade", df):
                st.markdown("**Quantidade média por pedido (Qty)**")
                tab = dfx.groupby("_has_promo")[colmap["quantidade"]].mean().rename(
                    {True:"Com Promoção", False:"Sem Promoção"})
                fig, ax = plt.subplots()
                sns.barplot(x=tab.index.map({True:"Com Promoção", False:"Sem Promoção"}), y=tab.values, ax=ax)
                ax.set_ylabel("Qty médio"); ax.set_xlabel(""); ax.set_title("Quantidade média")
                st.pyplot(fig, clear_figure=True)

            if has(colmap, "status_pedido", df):
                st.markdown("**Taxa de cancelamento: com x sem promoção**")
                cancel_mask = dfx[colmap["status_pedido"]].astype(str).str.lower().str.contains("cancel", na=False)
                tmp = dfx.assign(_cancel=cancel_mask.astype(int))
                tab = tmp.groupby("_has_promo")["_cancel"].mean().rename({True:"Com Promoção", False:"Sem Promoção"})
                fig, ax = plt.subplots()
                sns.barplot(x=tab.index, y=(100*tab.values), ax=ax)
                ax.set_ylabel("% cancelado"); ax.set_xlabel(""); ax.set_title("Cancelamento por promoção")
                st.pyplot(fig, clear_figure=True)
        else:
            st.info("Coluna de promoção não encontrada.")

    # -------------------------- 5) PRODUTOS --------------------------
    with aba_prod:
        st.subheader("Produtos")

        if has(colmap, "tamanho", df):
            st.markdown("**Tamanhos (Size) mais comprados**")
            vc = dfx[colmap["tamanho"]].value_counts().head(15)
            fig, ax = plt.subplots(figsize=(7,4))
            sns.barplot(x=vc.values, y=vc.index, ax=ax)
            ax.set_xlabel("Pedidos"); ax.set_ylabel("Size"); ax.set_title("Top 15 Sizes")
            st.pyplot(fig, clear_figure=True)

        if has(colmap, "valor_unitario", df) and has(colmap, "produto", df):
            st.markdown("**Produtos com maior valor unitário médio**")
            tab = dfx.groupby(colmap["produto"])[colmap["valor_unitario"]].mean().sort_values(ascending=False).head(15)
            fig, ax = plt.subplots(figsize=(7,4))
            sns.barplot(x=tab.values, y=tab.index, ax=ax)
            ax.set_xlabel("Valor unitário médio (R$)"); ax.set_ylabel("Produto"); ax.set_title("Top 15")
            st.pyplot(fig, clear_figure=True)

        if has(colmap, "quantidade", df) and has(colmap, "valor_pedido", df):
            st.markdown("**Correlação: Quantidade (Qty) x Valor do Pedido (R$)**")
            x = pd.to_numeric(dfx[colmap["quantidade"]], errors="coerce")
            y = pd.to_numeric(dfx[colmap["valor_pedido"]], errors="coerce")
            mask = x.notna() & y.notna()
            fig, ax = plt.subplots()
            ax.scatter(x[mask], y[mask], alpha=0.6)
            try:
                coef = np.polyfit(x[mask], y[mask], 1)
                xr = np.linspace(x[mask].min(), x[mask].max(), 100)
                ax.plot(xr, coef[0]*xr + coef[1])
            except Exception:
                pass
            ax.set_xlabel("Quantidade (Qty)"); ax.set_ylabel("Valor do Pedido (R$)")
            ax.set_title("Dispersão com tendência")
            st.pyplot(fig, clear_figure=True)

    # ---------------------- 6) ESTATÍSTICA AVANÇADA ----------------------
    with aba_stat:
        st.subheader("Estatística / Avançadas")

        if has(colmap, "valor_pedido", df) and has(colmap, "tipo_cliente", df):
            st.markdown("**Ticket médio — B2B vs B2C**")
            fig, ax = plt.subplots()
            sns.boxplot(x=dfx[colmap["tipo_cliente"]], y=dfx[colmap["valor_pedido"]], ax=ax)
            ax.set_xlabel("Tipo de cliente"); ax.set_ylabel("Valor do pedido (R$)")
            ax.set_title("Boxplot — Ticket por grupo")
            st.pyplot(fig, clear_figure=True)

            g = dfx[colmap["tipo_cliente"]].astype(str)
            grupos = g.dropna().unique()
            if len(grupos) >= 2:
                a, b = grupos[:2]
                x1 = pd.to_numeric(dfx.loc[g==a, colmap["valor_pedido"]], errors="coerce").dropna()
                x2 = pd.to_numeric(dfx.loc[g==b, colmap["valor_pedido"]], errors="coerce").dropna()
                if len(x1) >= 2 and len(x2) >= 2:
                    tstat, pval = stats.ttest_ind(x1, x2, equal_var=False)
                    st.write(f"{a} vs {b} — t = {tstat:.4f}, p-valor = {pval:.4g}")

        if has(colmap, "valor_pedido", df) and has(colmap, "tipo_envio", df):
            st.markdown("**Ticket médio — Amazon vs Vendedor**")
            fig, ax = plt.subplots()
            sns.boxplot(x=dfx[colmap["tipo_envio"]], y=dfx[colmap["valor_pedido"]], ax=ax)
            ax.set_xlabel("Responsável pelo envio"); ax.set_ylabel("Valor do pedido (R$)")
            ax.set_title("Boxplot — Ticket por envio")
            st.pyplot(fig, clear_figure=True)

            g = dfx[colmap["tipo_envio"]].astype(str)
            grupos = g.dropna().unique()
            if len(grupos) >= 2:
                a, b = grupos[:2]
                x1 = pd.to_numeric(dfx.loc[g==a, colmap["valor_pedido"]], errors="coerce").dropna()
                x2 = pd.to_numeric(dfx.loc[g==b, colmap["valor_pedido"]], errors="coerce").dropna()
                if len(x1) >= 2 and len(x2) >= 2:
                    tstat, pval = stats.ttest_ind(x1, x2, equal_var=False)
                    st.write(f"{a} vs {b} — t = {tstat:.4f}, p-valor = {pval:.4g}")

        if has(colmap, "quantidade", df) and has(colmap, "valor_pedido", df):
            st.markdown("**Correlação — Nº Itens (Qty) x Valor do Pedido (R$)**")
            r_p = correlacao_pearson(dfx[colmap["quantidade"]], dfx[colmap["valor_pedido"]])
            if r_p is not None:
                r, p = r_p
                st.write(f"r = {r:.4f}, p-valor = {p:.4g}")

        if has(colmap, "valor_pedido", df) and has(colmap, "categoria", df):
            st.markdown("**ANOVA — Ticket entre categorias (Top 8 por volume)**")
            top = dfx[colmap["categoria"]].value_counts().head(8).index
            subset = dfx[dfx[colmap["categoria"]].isin(top)]
            fig, ax = plt.subplots(figsize=(8,4))
            sns.boxplot(x=subset[colmap["categoria"]], y=subset[colmap["valor_pedido"]], ax=ax)
            ax.set_xlabel("Categoria"); ax.set_ylabel("Valor do pedido (R$)")
            ax.set_title("Boxplot — Ticket por categoria (Top 8)")
            st.pyplot(fig, clear_figure=True)

            grupos = [pd.to_numeric(subset.loc[subset[colmap["categoria"]]==k, colmap["valor_pedido"]],
                                    errors="coerce").dropna() for k in top]
            grupos = [g for g in grupos if len(g) >= 2]
            if len(grupos) >= 2:
                fstat, pval = stats.f_oneway(*grupos)
                st.write(f"F = {fstat:.4f}, p-valor = {pval:.4g}")
