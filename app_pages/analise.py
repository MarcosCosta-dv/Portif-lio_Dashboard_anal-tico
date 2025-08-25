# -*- coding: utf-8 -*-
import re
import io
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
from scipy import stats

# Se você já criou core/data.py conforme combinei, importe daqui.
# Caso ainda não tenha, troque pelas suas funções locais de carregar e helpers.
from core.data import carregar_df, tipo_variavel, ic_media, correlacao_pearson


# ============================================================
# Helpers visuais e utilitários
# ============================================================
def _safe_numeric(s):
    return pd.to_numeric(s, errors="coerce")

def _kpi(label, value, help_text=None):
    c = st.container()
    c.markdown(f"""
    <div class="card" style="padding:12px 14px; display:flex; gap:.5rem; align-items:center;">
      <div style="font-weight:700; font-size: .95rem;">{label}</div>
      <div style="margin-left:auto; font-size:1.2rem; font-weight:800;">{value}</div>
    </div>
    """, unsafe_allow_html=True)
    if help_text:
        c.caption(help_text)

def _ratio_str(num, den, prec=2):
    if den == 0:
        return "0%"
    return f"{(100.0 * num / den):.{prec}f}%"

def _month_key(dt_series):
    return dt_series.dt.to_period("M").dt.to_timestamp()

def _exists(colmap, key):
    return (
        key in colmap and
        colmap[key] is not None and
        colmap[key] != "" and
        colmap[key] in st.session_state.get("all_cols", [])
    )


# ============================================================
# AUTO-MAPEAMENTO DE COLUNAS (FIAP + heurísticas)
# ============================================================
ROLE_SYNONYMS = {
    # Vendas
    "data_pedido":      [r"^date$", r"order[\s_]*date", r"data[\s_]*pedido"],
    "valor_pedido":     [r"^amount$", r"valor[\s_]*pedido", r"order[\s_]*amount", r"total[\s_]*order"],
    "categoria":        [r"^category$", r"categoria"],
    "produto":          [r"^product$", r"product[\s_]*name", r"style", r"produto", r"descri[cç][aã]o", r"descricao"],
    "tipo_cliente":     [r"^b2b$", r"tipo[\s_]*cliente", r"customer[\s_]*type"],
    "regiao":           [r"ship[\s_]*state", r"ship[\s_]*city", r"estado", r"cidade", r"regi[aã]o", r"uf"],
    "quantidade":       [r"^qty$", r"quantity", r"quantidade"],

    # Cancelamentos/entregas
    "status_pedido":    [r"^status$", r"order[\s_]*status", r"situa[cç][aã]o"],
    "tipo_envio":       [r"^fulfil.*by$", r"^fulfilled[\s_]*by$", r"^fulfillment$", r"^fulfilment$",
                         r"tipo[\s_]*envio", r"envio[\s_]*por"],
    "courier_status":   [r"^courier[\s_]*status$", r"ship[\s_]*service[\s_]*level", r"nível[\s_]*servi[cç]o"],

    # Produtos
    "tamanho":          [r"^size$", r"tamanho"],
    "valor_unitario":   [r"unit[\s_]*price", r"valor[\s_]*unit[aá]rio", r"pre[cç]o[\s_]*unit[aá]rio"],

    # Promoções
    "tem_promocao":     [r"promotion[\s_]*id", r"promo[cç][aã]o", r"has[\s_]*promo", r"applied[\s_]*promo"],
}

ROLE_LABELS = {
    "data_pedido": "Data do pedido (datetime)",
    "valor_pedido": "Valor do pedido em BRL (numérico)",
    "categoria": "Categoria do produto (texto)",
    "produto": "Produto (texto)",
    "tipo_cliente": "Tipo de cliente (B2B/B2C)",
    "regiao": "Região/Estado/Cidade do cliente",
    "quantidade": "Quantidade do pedido (Qty, numérico)",
    "status_pedido": "Status do pedido (ex.: Cancelado/Entregue/Em trânsito)",
    "tipo_envio": "Tipo de envio (ex.: Amazon/Vendedor)",
    "courier_status": "Status do courier (para tempo de entrega)",
    "tamanho": "Tamanho (Size, ex.: P/M/G ou variações)",
    "valor_unitario": "Valor unitário do item (numérico)",
    "tem_promocao": "Indicador de promoção aplicada (bool/0-1/Sim-Não)",
}

ESSENCIAIS = [
    "data_pedido", "valor_pedido", "categoria", "produto",
    "tipo_cliente", "regiao", "quantidade", "status_pedido", "tipo_envio"
]

def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9_]+", " ", s.lower().strip())

def _find_by_patterns(columns, patterns):
    norm_cols = {c: _norm(c) for c in columns}
    # 1) match exato
    for c, nc in norm_cols.items():
        for p in patterns:
            if re.fullmatch(p, nc):
                return c
    # 2) contém
    for c, nc in norm_cols.items():
        for p in patterns:
            if re.search(p, nc):
                return c
    return None

def automap_columns(df: pd.DataFrame) -> dict:
    colmap = {}
    cols = df.columns.tolist()
    for role, pats in ROLE_SYNONYMS.items():
        found = _find_by_patterns(cols, pats)
        colmap[role] = found
    return colmap

def ensure_colmap(df: pd.DataFrame):
    """Cria/atualiza o colmap na session. Retorna (colmap, completo: bool)."""
    if "all_cols" not in st.session_state:
        st.session_state["all_cols"] = df.columns.tolist()

    # cria se não existir
    if "colmap" not in st.session_state:
        st.session_state["colmap"] = automap_columns(df)

    # atualiza vazios com auto novamente
    auto = automap_columns(df)
    for k, v in auto.items():
        if not st.session_state["colmap"].get(k):
            st.session_state["colmap"][k] = v

    completo = all(st.session_state["colmap"].get(k) for k in ESSENCIAIS)
    return st.session_state["colmap"], completo

def mapear_colunas_ui(df: pd.DataFrame):
    """Mostra a UI APENAS se faltarem colunas essenciais. Quando mostra, já vem pré‑selecionada."""
    colmap, completo = ensure_colmap(df)
    all_cols = ["(nenhuma)"] + df.columns.tolist()

    if completo:
        st.success("✅ Colunas detectadas automaticamente. Você pode seguir para as análises.")
        st.dataframe(pd.DataFrame(
            [{"papel": k, "coluna": v or "(nenhuma)"} for k, v in colmap.items()]
        ), use_container_width=True)
        return

    st.warning("Nem todas as colunas essenciais foram detectadas. Revise/complete o mapeamento abaixo.")
    left, right = st.columns(2)

    with left:
        st.subheader("Vendas")
        for key in ["data_pedido","valor_pedido","categoria","produto","tipo_cliente","regiao","quantidade"]:
            val = colmap.get(key)
            st.session_state["colmap"][key] = st.selectbox(
                ROLE_LABELS[key], all_cols, index=all_cols.index(val) if val in df.columns else 0
            )

    with right:
        st.subheader("Cancelamentos/Entregas")
        for key in ["status_pedido","tipo_envio","courier_status"]:
            val = colmap.get(key)
            st.session_state["colmap"][key] = st.selectbox(
                ROLE_LABELS[key], all_cols, index=all_cols.index(val) if val in df.columns else 0
            )

        st.subheader("Produtos / Promoções")
        for key in ["tamanho","valor_unitario","tem_promocao"]:
            val = colmap.get(key)
            st.session_state["colmap"][key] = st.selectbox(
                ROLE_LABELS[key], all_cols, index=all_cols.index(val) if val in df.columns else 0
            )

    st.info("Configuração salva. Volte às abas de perguntas/estatística quando terminar.")


# ============================================================
# VIEWS: Exploratório, Perguntas de Negócio e Estatística
# ============================================================
def view_exploratoria(df):
    st.subheader("Exploração Rápida")
    st.markdown("**Amostra:**")
    st.dataframe(df.head(20), use_container_width=True)

    st.markdown("**Descrição Numérica:**")
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(num_cols) > 0:
        st.dataframe(df[num_cols].describe().T)
    else:
        st.info("Não foram detectadas colunas numéricas.")

def view_perguntas_negocio(df):
    st.subheader("Perguntas de Negócio")

    if "colmap" not in st.session_state:
        st.warning("Mapeie as colunas na aba 'Mapeamento de Colunas'.")
        st.stop()

    cm = st.session_state["colmap"]

    # aliases
    col_dt   = cm.get("data_pedido")
    col_val  = cm.get("valor_pedido")
    col_cat  = cm.get("categoria")
    col_prod = cm.get("produto")
    col_cli  = cm.get("tipo_cliente")
    col_reg  = cm.get("regiao")
    col_qty  = cm.get("quantidade")
    col_st   = cm.get("status_pedido")
    col_ship = cm.get("tipo_envio")
    col_cour = cm.get("courier_status")
    col_size = cm.get("tamanho")
    col_unit = cm.get("valor_unitario")
    col_promo= cm.get("tem_promocao")

    dfx = df.copy()
    # conversões
    if _exists(cm, "data_pedido"):      dfx[col_dt]  = pd.to_datetime(dfx[col_dt], errors="coerce")
    if _exists(cm, "valor_pedido"):     dfx[col_val] = _safe_numeric(dfx[col_val])
    if _exists(cm, "quantidade"):       dfx[col_qty] = _safe_numeric(dfx[col_qty])
    if _exists(cm, "valor_unitario"):   dfx[col_unit]= _safe_numeric(dfx[col_unit])

    # ------------------- 1) Vendas -------------------
    st.markdown("### 1) Vendas")
    cols = st.columns(3)
    n_pedidos = len(dfx)
    total_vendas = dfx[col_val].sum() if _exists(cm,"valor_pedido") else np.nan
    ticket_medio = (total_vendas / n_pedidos) if (n_pedidos > 0 and _exists(cm,"valor_pedido")) else np.nan

    with cols[0]:
        _kpi("Pedidos (N)", f"{n_pedidos:,}".replace(",", "."))
    with cols[1]:
        _kpi("Vendas (R$)", f"{total_vendas:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
             if pd.notna(total_vendas) else "-")
    with cols[2]:
        _kpi("Ticket médio (R$)", f"{ticket_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
             if pd.notna(ticket_medio) else "-")

    # 1.a Volume por mês
    if _exists(cm,"data_pedido"):
        st.markdown("**Volume de pedidos por mês (sazonalidade)**")
        gdf = dfx.dropna(subset=[col_dt])
        bym = gdf.groupby(_month_key(gdf[col_dt])).size().reset_index(name="pedidos")
        if not bym.empty:
            fig, ax = plt.subplots()
            ax.plot(bym[col_dt], bym["pedidos"], marker="o")
            ax.set_title("Pedidos por mês"); ax.set_xlabel("Mês"); ax.set_ylabel("Nº de pedidos")
            st.pyplot(fig, clear_figure=True)
        else:
            st.info("Sem datas válidas para agrupar por mês.")

    # 1.b Ticket médio por categoria/produto
    if _exists(cm, "valor_pedido") and (_exists(cm,"categoria") or _exists(cm,"produto")):
        st.markdown("**Ticket médio por categoria/produto**")
        alvo = col_cat if _exists(cm,"categoria") else col_prod
        tkm = dfx.groupby(alvo)[col_val].mean().sort_values(ascending=False)
        st.dataframe(tkm.to_frame("ticket_medio_R$"))

    # 1.c Mais vendidos
    if _exists(cm,"produto"):
        st.markdown("**Produtos mais vendidos (contagem de pedidos)**")
        st.dataframe(dfx[col_prod].value_counts().head(10).to_frame("pedidos"))
    if _exists(cm,"categoria"):
        st.markdown("**Categorias mais vendidas**")
        st.dataframe(dfx[col_cat].value_counts().head(10).to_frame("pedidos"))

    # 1.d Regiões mais lucrativas
    if _exists(cm,"regiao") and _exists(cm,"valor_pedido"):
        st.markdown("**Regiões mais lucrativas (soma de vendas)**")
        reg = dfx.groupby(col_reg)[col_val].sum().sort_values(ascending=False).head(15)
        st.dataframe(reg.to_frame("vendas_R$"))

    # 1.e B2B x B2C
    if _exists(cm,"tipo_cliente"):
        st.markdown("**Proporção de vendas B2B x B2C**")
        counts = dfx[col_cli].value_counts()
        total = counts.sum()
        dfp = pd.DataFrame({"tipo": counts.index, "qtd": counts.values,
                            "pct": [100*c/total for c in counts.values] if total>0 else 0})
        st.dataframe(dfp)

    st.markdown("---")
    # ------------------- 2) Cancelamentos e Entregas -------------------
    st.markdown("### 2) Cancelamentos e Entregas")
    if _exists(cm,"status_pedido"):
        total = len(dfx)
        cancelados = (dfx[col_st].astype(str).str.lower().str.contains("cancel", na=False)).sum()
        _kpi("Taxa de cancelamento", _ratio_str(cancelados, total), "Cancelados / Total de pedidos")

        if _exists(cm,"categoria"):
            st.markdown("**Cancelamento por categoria**")
            st.dataframe(pd.crosstab(dfx[col_cat], dfx[col_st]))
        if _exists(cm,"tamanho"):
            st.markdown("**Cancelamento por tamanho (Size)**")
            st.dataframe(pd.crosstab(dfx[col_size], dfx[col_st]))
        if _exists(cm,"tipo_envio"):
            st.markdown("**Cancelamento por Tipo de Envio (Amazon vs. Vendedor)**")
            st.dataframe(pd.crosstab(dfx[col_ship], dfx[col_st]))
        if _exists(cm,"courier_status"):
            st.markdown("**Distribuição de status do courier**")
            st.dataframe(dfx[col_cour].value_counts().to_frame("qtd"))
    else:
        st.info("Para análises de cancelamento/entrega, mapeie 'status_pedido'.")

    st.markdown("---")
    # ------------------- 3) Logística -------------------
    st.markdown("### 3) Logística")
    st.caption("Estimativas dependem da qualidade de datas/status disponíveis.")
    if _exists(cm,"data_pedido") and _exists(cm,"courier_status"):
        entregues_mask = dfx[col_cour].astype(str).str.lower().str.contains("entreg", na=False) | \
                         dfx[col_st].astype(str).str.lower().str.contains("entreg", na=False) if _exists(cm,"status_pedido") else \
                         dfx[col_cour].astype(str).str.lower().str.contains("entreg", na=False)
        total_entregues = entregues_mask.sum()
        _kpi("Entregas (proxy)", f"{total_entregues}", "Courier/Status contendo 'entreg'")
    else:
        st.info("Mapeie data_pedido e courier/status para estimar logística.")

    if _exists(cm,"tipo_envio") and _exists(cm,"status_pedido"):
        st.markdown("**Performance por Tipo de Envio (entregas vs cancelamentos)**")
        st.dataframe(pd.crosstab(dfx[col_ship], dfx[col_st]))

    if _exists(cm,"regiao") and _exists(cm,"status_pedido"):
        st.markdown("**Atraso/Cancelamento por Região**")
        st.dataframe(pd.crosstab(dfx[col_reg], dfx[col_st]))

    st.markdown("---")
    # ------------------- 4) Promoções -------------------
    st.markdown("### 4) Promoções")
    if _exists(cm,"tem_promocao"):
        promo = dfx[col_promo].astype(str).str.lower().isin(["1","true","sim","yes","y"])
        dfx["_has_promo"] = promo

        if _exists(cm,"valor_pedido"):
            st.markdown("**Ticket médio: com x sem promoção**")
            dcmp = dfx.groupby("_has_promo")[col_val].agg(["count","mean"]).rename(
                index={True:"Com Promoção", False:"Sem Promoção"})
            st.dataframe(dcmp)

        if _exists(cm,"quantidade"):
            st.markdown("**Quantidade por pedido (Qty): com x sem promoção**")
            dqty = dfx.groupby("_has_promo")[col_qty].agg(["count","mean"]).rename(
                index={True:"Com Promoção", False:"Sem Promoção"})
            st.dataframe(dqty)

        if _exists(cm,"status_pedido"):
            st.markdown("**Promoção x Cancelamento**")
            st.dataframe(pd.crosstab(dfx["_has_promo"], dfx[col_st]))
    else:
        st.info("Mapeie 'tem_promocao' para avaliar impacto de promoções.")

    st.markdown("---")
    # ------------------- 5) Produtos -------------------
    st.markdown("### 5) Produtos")
    if _exists(cm,"tamanho"):
        st.markdown("**Tamanhos (Size) mais comprados**")
        st.dataframe(dfx[col_size].value_counts().to_frame("qtd"))

    if _exists(cm,"valor_unitario") and _exists(cm,"produto"):
        st.markdown("**Produtos com maior valor unitário médio**")
        vunit = dfx.groupby(col_prod)[col_unit].mean().sort_values(ascending=False).head(15)
        st.dataframe(vunit.to_frame("valor_unit_médio_R$"))

    if _exists(cm,"quantidade") and _exists(cm,"valor_pedido"):
        st.markdown("**Correlação entre quantidade (Qty) e valor do pedido (R$)**")
        r_p = correlacao_pearson(dfx[col_qty], dfx[col_val])
        if r_p is not None:
            r, p = r_p
            st.write(f"r = {r:.4f}, p-valor = {p:.4g}")
            fig, ax = plt.subplots()
            mask = dfx[col_qty].notna() & dfx[col_val].notna()
            ax.scatter(dfx.loc[mask, col_qty], dfx.loc[mask, col_val], alpha=0.6)
            ax.set_xlabel("Quantidade (Qty)"); ax.set_ylabel("Valor Pedido (R$)"); ax.set_title("Dispersão Qty x Valor")
            st.pyplot(fig, clear_figure=True)
        else:
            st.info("Amostra insuficiente para correlação.")


def view_estatistica_avancada(df):
    st.subheader("Estatística Avançada")

    if "colmap" not in st.session_state:
        st.warning("Mapeie as colunas na aba 'Mapeamento de Colunas'.")
        st.stop()

    cm = st.session_state["colmap"]

    col_val  = cm.get("valor_pedido")
    col_cli  = cm.get("tipo_cliente")
    col_ship = cm.get("tipo_envio")
    col_cat  = cm.get("categoria")
    col_qty  = cm.get("quantidade")

    # 6.a Ticket médio B2B vs B2C
    st.markdown("### Ticket médio — B2B vs B2C")
    if col_val and col_cli and col_val in df.columns and col_cli in df.columns:
        x = _safe_numeric(df[col_val])
        grupo = df[col_cli].astype(str)
        grupos = grupo.dropna().unique()
        if len(grupos) >= 2:
            g1, g2 = grupos[:2]
            x1 = x[grupo == g1].dropna(); x2 = x[grupo == g2].dropna()
            if len(x1) >= 2 and len(x2) >= 2:
                tstat, pval = stats.ttest_ind(x1, x2, equal_var=False)  # Welch
                st.write(f"Grupos: {g1} (n={len(x1)}) vs {g2} (n={len(x2)})")
                st.write(f"t = {tstat:.4f}, p-valor = {pval:.4g}")
                st.success("Diferença significativa (α=0,05)." if pval < 0.05 else "Não significativa (α=0,05).")
            else:
                st.info("Amostras insuficientes (n≥2 por grupo).")
        else:
            st.info("É necessário ter ao menos dois grupos em tipo de cliente.")
    else:
        st.info("Mapeie valor_pedido e tipo_cliente.")

    # 6.b Ticket médio — Amazon vs Vendedor
    st.markdown("### Ticket médio — Amazon vs Vendedor")
    if col_val and col_ship and col_val in df.columns and col_ship in df.columns:
        x = _safe_numeric(df[col_val])
        grupo = df[col_ship].astype(str)
        grupos = grupo.dropna().unique()
        if len(grupos) >= 2:
            a, b = grupos[:2]
            x1 = x[grupo == a].dropna(); x2 = x[grupo == b].dropna()
            if len(x1) >= 2 and len(x2) >= 2:
                tstat, pval = stats.ttest_ind(x1, x2, equal_var=False)
                st.write(f"Tipos: {a} (n={len(x1)}) vs {b} (n={len(x2)})")
                st.write(f"t = {tstat:.4f}, p-valor = {pval:.4g}")
                st.success("Diferença significativa (α=0,05)." if pval < 0.05 else "Não significativa (α=0,05).")
            else:
                st.info("Amostras insuficientes (n≥2 por grupo).")
        else:
            st.info("Precisa de ao menos dois tipos de envio distintos.")
    else:
        st.info("Mapeie valor_pedido e tipo_envio.")

    # 6.c Correlação Qty x Valor
    st.markdown("### Correlação — Nº Itens (Qty) x Valor do Pedido (R$)")
    if col_qty and col_val and col_qty in df.columns and col_val in df.columns:
        r_p = correlacao_pearson(df[col_qty], df[col_val])
        if r_p is not None:
            r, p = r_p
            st.write(f"r = {r:.4f}, p-valor = {p:.4g}")
            st.success("Correlação significativa (α=0,05)." if p < 0.05 else "Não significativa (α=0,05).")
        else:
            st.info("Amostra insuficiente para correlação.")
    else:
        st.info("Mapeie quantidade (Qty) e valor_pedido.")

    # 6.d ANOVA — ticket médio por categoria
    st.markdown("### ANOVA — Ticket médio entre categorias")
    if col_val and col_cat and col_val in df.columns and col_cat in df.columns:
        x = _safe_numeric(df[col_val])
        g = df[col_cat].astype(str)
        grupos = [x[g == k].dropna() for k in g.dropna().unique()]
        grupos = [arr for arr in grupos if len(arr) >= 2]
        if len(grupos) >= 2:
            fstat, pval = stats.f_oneway(*grupos)
            st.write(f"F = {fstat:.4f}, p-valor = {pval:.4g}")
            st.success("Diferença significativa entre pelo menos duas categorias (α=0,05)."
                       if pval < 0.05 else "Não significativa (α=0,05).")
        else:
            st.info("Precisa de pelo menos duas categorias com n≥2 cada.")
    else:
        st.info("Mapeie valor_pedido e categoria.")


# ============================================================
# Página principal (entry point desta page)
# ============================================================
def render():
    st.title("Análise de Dados — CP1 (perguntas de negócio + estatística)")

    # 1) Carregar base
    df = carregar_df()
    if df is None:
        st.warning("Carregue a base para continuar.")
        st.stop()

    # 2) Abas principais
    aba_map, aba_explo, aba_q, aba_stat = st.tabs([
        "Mapeamento de Colunas",
        "Exploração",
        "Perguntas de Negócio",
        "Estatística Avançada"
    ])

    # 2.1) Mapeamento (auto + UI condicional)
    with aba_map:
        mapear_colunas_ui(df)

        # Dicionário de dados didático (opcional, ajuda o usuário)
        st.markdown("#### 📖 Dicionário de Dados (exemplo FIAP)")
        dicionario = {
            "Order ID": "Identificador único do pedido.",
            "Date": "Data do pedido.",
            "Status": "Situação do pedido (Enviado/Cancelado/etc.).",
            "Fulfilment / Fulfilled By": "Responsável pelo envio (Amazon ou Vendedor).",
            "Sales Channel": "Canal de vendas.",
            "Ship Service Level / Courier Status": "Nível/status do envio (Padrão/Expresso/Entregue/etc.).",
            "Style / Product": "Nome/descrição do produto.",
            "SKU": "Código único de estoque.",
            "Category": "Categoria do produto.",
            "Currency": "Moeda da transação.",
            "Amount": "Valor total do pedido.",
            "Ship City/State/Country": "Destino do envio.",
            "Promotion IDs": "Identificadores de promoções aplicadas.",
            "B2B": "Indica se a compra é B2B (True) ou B2C (False).",
            "Size": "Tamanho do produto (P/M/G...).",
            "Unit Price": "Preço unitário.",
        }
        st.dataframe(pd.DataFrame(list(dicionario.items()), columns=["Coluna", "Descrição"]),
                     use_container_width=True)

    # 2.2) Exploratório
    with aba_explo:
        view_exploratoria(df)

    # 2.3) Perguntas de negócio
    with aba_q:
        view_perguntas_negocio(df)

    # 2.4) Estatística
    with aba_stat:
        view_estatistica_avancada(df)
