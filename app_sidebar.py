# -*- coding: utf-8 -*-
import os
import io
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import plotly.graph_objects as go  # radar

# =========================
# Configurações gerais
# =========================
st.set_page_config(page_title="CP1 - Dashboard Profissional", layout="wide")
sns.set_theme()

# =========================
# Funções utilitárias (dados)
# =========================
def carregar_df_padrao():
    """
    Tenta carregar data/df_selecionado.(csv|xlsx|parquet).
    Se não existir, retorna None.
    """
    base_dir = "data"
    base_name = "df_selecionado"
    possiveis = [
        os.path.join(base_dir, f"{base_name}.csv"),
        os.path.join(base_dir, f"{base_name}.xlsx"),
        os.path.join(base_dir, f"{base_name}.parquet"),
    ]
    for caminho in possiveis:
        if os.path.exists(caminho):
            ext = os.path.splitext(caminho)[1].lower()
            if ext == ".csv":
                return pd.read_csv(caminho)
            elif ext == ".xlsx":
                return pd.read_excel(caminho)
            elif ext == ".parquet":
                return pd.read_parquet(caminho)
    return None

def carregar_df():
    """
    Prioriza o arquivo padrão; se não houver, exibe uploader.
    """
    df = carregar_df_padrao()
    if df is not None:
        st.success("Base carregada automaticamente de `data/df_selecionado.*`")
        return df

    st.info("Não encontrei `data/df_selecionado.*`. Faça o upload do arquivo.")
    up = st.file_uploader("Envie df_selecionado (CSV, XLSX ou PARQUET)", type=["csv", "xlsx", "parquet"])
    if up is None:
        return None

    nome = up.name.lower()
    try:
        if nome.endswith(".csv"):
            return pd.read_csv(up)
        elif nome.endswith(".xlsx"):
            return pd.read_excel(up)
        elif nome.endswith(".parquet"):
            data = up.read()
            return pd.read_parquet(io.BytesIO(data))
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
    return None

def tipo_variavel(serie: pd.Series):
    """
    Classifica tipo de variável de forma simples.
    """
    if pd.api.types.is_numeric_dtype(serie):
        return "Numérica"
    if pd.api.types.is_bool_dtype(serie):
        return "Booleana"
    if pd.api.types.is_datetime64_any_dtype(serie):
        return "Data/Hora"
    return "Categórica/Textual"

def ic_media(serie, conf=0.95):
    """
    Intervalo de confiança da média via t-Student.
    """
    x = pd.to_numeric(serie.dropna(), errors='coerce').dropna()
    n = len(x)
    if n < 2:
        return None
    media = x.mean()
    sd = x.std(ddof=1)
    se = sd / np.sqrt(n)
    alfa = 1 - conf
    tcrit = stats.t.ppf(1 - alfa/2, df=n-1)
    li = media - tcrit * se
    ls = media + tcrit * se
    return {"media": media, "n": n, "li": li, "ls": ls, "conf": conf}

def correlacao_pearson(x, y):
    x = pd.to_numeric(x, errors='coerce')
    y = pd.to_numeric(y, errors='coerce')
    mask = x.notna() & y.notna()
    if mask.sum() < 3:
        return None
    r, p = stats.pearsonr(x[mask], y[mask])
    return r, p

# =========================
# Funções utilitárias (radar)
# =========================
def radar_plotly(
    titulo,
    dicionario,
    baseline_val=None,
    rmin=0,
    rmax=100,
    height=520,
    width=600,
    tema="dark"
):
    """
    Gráfico radar polido com Plotly.
    - dicionario: {categoria: valor}
    - baseline_val: valor de meta (preenche ao fundo)
    - tema: "dark" ou "light"
    - height/width controlam tamanho absoluto (use_container_width=False)
    """
    import textwrap
    cats = list(dicionario.keys())
    vals = list(dicionario.values())

    def wrap(s, w=12):
        return "<br>".join(textwrap.wrap(str(s), width=w)) if isinstance(s, str) else s

    cats_wrapped = [wrap(c, 12) for c in cats]
    cats_closed  = cats_wrapped + [cats_wrapped[0]]
    vals_closed  = vals + [vals[0]]

    # Paleta por tema
    if tema == "dark":
        paper_bg = "#0e1117"
        plot_bg  = "#0e1117"
        grid     = "rgba(255,255,255,0.10)"
        font     = "#e5e5e5"
        line_c   = "#4cc9f0"
        fill_c   = "rgba(76,201,240,0.25)"
        base_fill= "rgba(200,200,200,0.12)"
        base_line= "rgba(160,160,160,0.6)"
    else:
        paper_bg = "#ffffff"
        plot_bg  = "#ffffff"
        grid     = "rgba(0,0,0,0.12)"
        font     = "#222"
        line_c   = "#2563eb"
        fill_c   = "rgba(37,99,235,0.20)"
        base_fill= "rgba(0,0,0,0.06)"
        base_line= "rgba(120,120,120,0.7)"

    fig = go.Figure()

    # baseline (meta)
    if baseline_val is not None:
        base_list = [baseline_val for _ in cats]
        fig.add_trace(go.Scatterpolar(
            r     = base_list + [base_list[0]],
            theta = cats_closed,
            fill  = "toself",
            name  = "Meta",
            line  = dict(width=1.2, color=base_line),
            fillcolor = base_fill,
            hoverinfo = "skip",
            opacity = 1.0
        ))

    # série principal
    fig.add_trace(go.Scatterpolar(
        r     = vals_closed,
        theta = cats_closed,
        fill  = "toself",
        name  = titulo,
        mode  = "lines+markers",
        marker= dict(size=7),
        line  = dict(width=3, color=line_c),
        fillcolor = fill_c,
        hovertemplate = "<b>%{theta}</b><br>Valor: %{r}<extra></extra>"
    ))

    fig.update_layout(
        title = dict(text=titulo, x=0.5, xanchor="center", y=0.95, font=dict(size=18, color=font)),
        paper_bgcolor = paper_bg,
        plot_bgcolor  = plot_bg,
        font = dict(color=font, size=13),
        showlegend = False,
        margin = dict(l=10, r=10, t=40, b=10),
        height = height,
        width  = width,
        autosize = False,  # << respeitar width/height
        polar = dict(
            bgcolor = plot_bg,
            radialaxis = dict(
                range=[rmin, rmax],
                gridcolor=grid,
                gridwidth=1,
                tickfont=dict(size=11),
                showline=True,
                linecolor=grid
            ),
            angularaxis = dict(
                gridcolor=grid,
                gridwidth=1,
                tickfont=dict(size=11),
                direction="clockwise",
                rotation=90
            )
        )
    )
    return fig

# =========================
# Sidebar: navegação + aparência
# =========================
menu = st.sidebar.radio(
    "Navegação",
    ["Home", "Formação e Experiência", "Skills", "Análise de Dados"]
)
st.sidebar.markdown("---")
st.sidebar.markdown("**Dica:** coloque seu arquivo em `data/df_selecionado.csv` (ou .xlsx/.parquet)")

with st.sidebar.expander("Aparência dos gráficos", expanded=True):
    tema_graf   = st.radio("Tema", ["dark", "light"], index=0, horizontal=True)
    rmin_opt    = st.number_input("r (mín)", value=0, step=5)
    rmax_opt    = st.number_input("r (máx)", value=100, step=5)
    graf_height = st.slider("Altura dos gráficos (px)", 320, 1000, 560, 20)
    graf_width  = st.slider("Largura dos gráficos (px)", 420, 1200, 620, 20)
    layout_cols = st.select_slider("Gráficos por linha", options=[1, 2, 3], value=3)

plotly_cfg = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"]
}

# =========================
# HOME
# =========================
if menu == "Home":
    st.title("Meu Dashboard Profissional")
    st.subheader("Objetivo")
    st.write("Apresente-se brevemente: área de interesse, objetivo profissional e o tipo de problema de mercado que você analisa na aba de Análise de Dados.")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(
            """
            **Resumo**  
            - Área: Data/Tech/Negócios  
            - Foco: Monitoria/Observabilidade, Automação e Análise de Dados  
            - Contato: **seu_email@exemplo.com**  
            - [![LinkedIn](https://img.shields.io/badge/LinkedIn-blue?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/marcosscosta)  
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            """
            <a href="https://www.linkedin.com/in/marcosscosta" target="_blank">
                <button style="background-color:#0077b5;color:white;padding:8px 14px;border:none;border-radius:6px;cursor:pointer;">
                    🌐 Meu LinkedIn
                </button>
            </a>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.image("https://avatars.githubusercontent.com/u/9919?s=200&v=4", caption="(Exemplo de avatar)")

# =========================
# FORMAÇÃO E EXPERIÊNCIA
# =========================
elif menu == "Formação e Experiência":
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
    with st.container():
        st.markdown(
            """
            **C6 Bank — Analista Jr (Monitoriação)** *(fev/2025 – atual, remoto)*  
            - Criação e implementação de monitorias via **Splunk** para avaliar desempenho de produtos.  
            - Criação de **automações** via **Python** e **Microsoft Power Automate** para agilizar processos de TI.  
            - Stack/Competências: Splunk Cloud, Splunk, Google BigQuery, Microsoft Excel, Salesforce, ServiceNow, Azure DevOps, RunDeck, Grafana, Power Automate.
            """
        )
        st.markdown(
            """
            **C6 Bank — Monitoriação 24x7 (Estágio)** *(jun/2024 – fev/2025, presencial)*  
            - Monitoria de funcionalidades de produtos/aplicativos e acompanhamento de lançamentos.  
            - Análise de bases, indicadores, dashboards e logs.  
            - Stack/Competências: Azure DevOps, PostgreSQL, Grafana, ServiceNow, etc.
            """
        )

    st.markdown("---")
    st.markdown(
        "📬 **Contato:** [LinkedIn /marcosscosta](https://www.linkedin.com/in/marcosscosta)",
        unsafe_allow_html=True
    )

# =========================
# SKILLS
# =========================
elif menu == "Skills":
    st.title("Skills")

    # Radares (3 painéis)
    skills_dev = {"HTML5": 80, "CSS": 78, "JavaScript": 76, "Python": 85, "SQL": 80, "Java": 65}
    skills_tools = {"Splunk": 82, "Splunk Cloud": 80, "Grafana": 75, "BigQuery": 70, "Excel": 88, "Power Automate": 78}
    skills_soft = {"Comunicação": 86, "Pensamento Crítico": 84, "Raciocínio Lógico": 85, "Trabalho em Equipe": 90, "Organização": 82, "Proatividade": 88}
    baseline_meta = 80  # meta de proficiência (fundo cinza)

    # layout dinâmico
    if layout_cols == 3:
        cols = st.columns(3)
    elif layout_cols == 2:
        cols = st.columns(2)
    else:
        cols = [st.container(), st.container(), st.container()]

    with cols[0]:
        st.subheader("Desenvolvimento")
        st.plotly_chart(
            radar_plotly("Desenvolvimento", skills_dev, baseline_val=baseline_meta,
                         rmin=rmin_opt, rmax=rmax_opt, tema=tema_graf,
                         height=graf_height, width=graf_width),
            use_container_width=False,     # << respeitar width/height
            key="radar_dev_main",
            config=plotly_cfg
        )
    with cols[1]:
        st.subheader("Ferramentas & Plat.")
        st.plotly_chart(
            radar_plotly("Ferramentas & Plataformas", skills_tools, baseline_val=baseline_meta,
                         rmin=rmin_opt, rmax=rmax_opt, tema=tema_graf,
                         height=graf_height, width=graf_width),
            use_container_width=False,
            key="radar_tools_main",
            config=plotly_cfg
        )
    with cols[2]:
        st.subheader("Soft Skills")
        st.plotly_chart(
            radar_plotly("Soft Skills", skills_soft, baseline_val=baseline_meta,
                         rmin=rmin_opt, rmax=rmax_opt, tema=tema_graf,
                         height=graf_height, width=graf_width),
            use_container_width=False,
            key="radar_soft_main",
            config=plotly_cfg
        )

# =========================
# ANÁLISE DE DADOS
# =========================
elif menu == "Análise de Dados":
    st.title("Análise de Dados — CP1")

    df = carregar_df()
    if df is None:
        st.warning("Carregue a base para continuar.")
        st.stop()

    st.subheader("1) Apresentação do Conjunto de Dados e Tipos de Variáveis")
    st.write("Descreva o contexto do problema de mercado, a origem da base e os objetivos da análise.")
    st.markdown("**Prévia:**")
    st.dataframe(df.head(20), use_container_width=True)

    # Tipos de variáveis
    meta = []
    for c in df.columns:
        meta.append({"coluna": c, "tipo_inferido": tipo_variavel(df[c]), "n_missing": int(df[c].isna().sum())})
    st.markdown("**Tipos de variáveis (inferidos):**")
    st.dataframe(pd.DataFrame(meta))

    st.markdown("**Perguntas de Análise (exemplos):**")
    st.markdown("""
    - Quais variáveis explicam melhor a variável-alvo?  
    - Existem diferenças significativas entre grupos (ex.: região, categoria)?  
    - Qual a média estimada e o IC para uma métrica crítica (ex.: ticket médio)?  
    - Há correlação entre pares numéricos relevantes?
    """)

    st.subheader("2) Medidas Centrais, Dispersão, Correlação e Distribuições")
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = [c for c in df.columns if c not in num_cols]

    if len(num_cols) > 0:
        st.markdown("### Estatísticas Descritivas (Numéricas)")
        st.dataframe(df[num_cols].describe().T)

        # Escolha de variável para explorar distribuição
        sel_num = st.selectbox("Escolha uma variável numérica para explorar:", num_cols, index=0)
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("**Histograma + KDE**")
            fig, ax = plt.subplots()
            sns.histplot(df[sel_num].dropna(), kde=True, ax=ax)
            ax.set_title(f"Distribuição de {sel_num}")
            st.pyplot(fig, clear_figure=True)

        with col_b:
            st.markdown("**Boxplot (dispersão, outliers)**")
            fig2, ax2 = plt.subplots()
            sns.boxplot(x=df[sel_num], ax=ax2)
            ax2.set_title(f"Boxplot de {sel_num}")
            st.pyplot(fig2, clear_figure=True)

        # Correlação
        st.markdown("### Matriz de Correlação (Pearson)")
        if len(num_cols) >= 2:
            corr = df[num_cols].corr(numeric_only=True)
            figc, axc = plt.subplots(figsize=(6, 4))
            sns.heatmap(corr, annot=True, fmt=".2f", ax=axc)
            axc.set_title("Correlação (Pearson)")
            st.pyplot(figc, clear_figure=True)

            # Teste de correlação entre dois campos
            st.markdown("**Teste de Correlação entre dois campos (Pearson)**")
            c1 = st.selectbox("X:", num_cols, key="corr_x")
            c2 = st.selectbox("Y:", num_cols, key="corr_y")
            if c1 != c2:
                r_p = correlacao_pearson(df[c1], df[c2])
                if r_p is not None:
                    r, p = r_p
                    st.write(f"r = {r:.4f}, p-valor = {p:.4g}")
                    if p < 0.05:
                        st.success("Correlação estatisticamente significativa (α=0,05).")
                    else:
                        st.info("Correlação não significativa (α=0,05).")

            # Dispersão com linha de tendência
            st.markdown("**Dispersão com tendência (regressão linear simples)**")
            x_scatter = st.selectbox("Eixo X:", num_cols, key="scat_x")
            y_scatter = st.selectbox("Eixo Y:", num_cols, key="scat_y")
            if x_scatter != y_scatter:
                x = pd.to_numeric(df[x_scatter], errors='coerce')
                y = pd.to_numeric(df[y_scatter], errors='coerce')
                mask = x.notna() & y.notna()
                fig_s, ax_s = plt.subplots()
                ax_s.scatter(x[mask], y[mask], alpha=0.6)
                # reta
                try:
                    coef = np.polyfit(x[mask], y[mask], deg=1)
                    x_line = np.linspace(x[mask].min(), x[mask].max(), 100)
                    y_line = coef[0] * x_line + coef[1]
                    ax_s.plot(x_line, y_line)
                except Exception:
                    pass
                ax_s.set_xlabel(x_scatter)
                ax_s.set_ylabel(y_scatter)
                ax_s.set_title(f"{y_scatter} ~ {x_scatter}")
                st.pyplot(fig_s, clear_figure=True)

    else:
        st.info("Não foram detectadas colunas numéricas para as estatísticas descritivas.")

    st.subheader("3) Intervalos de Confiança e Testes de Hipótese")

    aba_ic, aba_testes = st.tabs(["Intervalo de Confiança", "Testes de Hipótese"])

    with aba_ic:
        st.markdown("**IC para a média (t-Student)**")
        if len(num_cols) > 0:
            target_ic = st.selectbox("Variável alvo (numérica):", num_cols, key="ic_target")
            conf = st.slider("Nível de confiança", 0.80, 0.99, 0.95, 0.01)
            res = ic_media(df[target_ic], conf=conf)
            if res:
                st.write(f"n = {res['n']}, média = {res['media']:.4f}")
                st.write(f"IC {int(conf*100)}%: [{res['li']:.4f}, {res['ls']:.4f}]")
                # gráfico do IC
                fig_ic, ax_ic = plt.subplots(figsize=(5, 1.8))
                ax_ic.errorbar([0], [res['media']], yerr=[[res['media']-res['li']], [res['ls']-res['media']]], fmt='o', capsize=6)
                ax_ic.set_xlim(-1, 1)
                ax_ic.set_xticks([])
                ax_ic.set_title(f"IC {int(conf*100)}% para {target_ic}")
                st.pyplot(fig_ic, clear_figure=True)
            else:
                st.warning("A amostra não tem tamanho suficiente para IC (precisa de n≥2).")
        else:
            st.info("Carregue uma base com pelo menos uma coluna numérica.")

    with aba_testes:
        teste = st.selectbox(
            "Escolha o teste:",
            [
                "t de 1 amostra (média = valor de referência)",
                "t de 2 amostras (independentes, médias de dois grupos)",
                "Mann-Whitney (2 grupos, não-paramétrico)",
                "Qui-Quadrado de Independência (duas variáveis categóricas)"
            ]
        )

        if teste == "t de 1 amostra (média = valor de referência)":
            if len(num_cols) > 0:
                var = st.selectbox("Variável numérica:", num_cols, key="t1_var")
                mu0 = st.number_input("Valor de referência (H0: média = mu0)", value=float(np.nanmean(pd.to_numeric(df[var], errors='coerce'))))
                alpha = st.slider("α (nível de significância)", 0.01, 0.10, 0.05, 0.01)
                x = pd.to_numeric(df[var], errors='coerce').dropna()
                if len(x) >= 2:
                    tstat, pval = stats.ttest_1samp(x, mu0)
                    st.write(f"t = {tstat:.4f}, p-valor = {pval:.4g}")
                    if pval < alpha:
                        st.success("Rejeitamos H0 (diferença significativa).")
                    else:
                        st.info("Não rejeitamos H0 (sem diferença significativa).")
                else:
                    st.warning("Dados insuficientes para o teste.")
            else:
                st.info("Necessária ao menos uma variável numérica.")

        elif teste == "t de 2 amostras (independentes, médias de dois grupos)":
            # precisa de uma numérica e uma categórica de 2 níveis
            if len(num_cols) > 0 and len(cat_cols) > 0:
                var = st.selectbox("Variável numérica:", num_cols, key="t2_var")
                cat = st.selectbox("Variável categórica (grupos):", cat_cols, key="t2_cat")
                alpha = st.slider("α", 0.01, 0.10, 0.05, 0.01)
                grupos = df[cat].dropna().unique()
                if len(grupos) == 2:
                    g1, g2 = grupos[0], grupos[1]
                    x1 = pd.to_numeric(df.loc[df[cat] == g1, var], errors='coerce').dropna()
                    x2 = pd.to_numeric(df.loc[df[cat] == g2, var], errors='coerce').dropna()
                    if len(x1) >= 2 and len(x2) >= 2:
                        # Welch por segurança
                        tstat, pval = stats.ttest_ind(x1, x2, equal_var=False)
                        st.write(f"Grupos: {g1} (n={len(x1)}) vs {g2} (n={len(x2)})")
                        st.write(f"t = {tstat:.4f}, p-valor = {pval:.4g}")
                        if pval < alpha:
                            st.success("Rejeitamos H0 (médias diferentes).")
                        else:
                            st.info("Não rejeitamos H0 (médias semelhantes).")
                        # Boxplot comparativo
                        figx, axx = plt.subplots()
                        sns.boxplot(x=df[cat], y=df[var], ax=axx)
                        axx.set_title(f"{var} por {cat}")
                        st.pyplot(figx, clear_figure=True)
                    else:
                        st.warning("Amostras insuficientes em um dos grupos (precisa de n≥2 cada).")
                else:
                    st.warning("Escolha uma variável categórica com exatamente 2 grupos distintos.")
            else:
                st.info("Necessária uma numérica e uma categórica.")

        elif teste == "Mann-Whitney (2 grupos, não-paramétrico)":
            if len(num_cols) > 0 and len(cat_cols) > 0:
                var = st.selectbox("Variável numérica:", num_cols, key="mw_var")
                cat = st.selectbox("Variável categórica (2 grupos):", cat_cols, key="mw_cat")
                alpha = st.slider("α", 0.01, 0.10, 0.05, 0.01)
                grupos = df[cat].dropna().unique()
                if len(grupos) == 2:
                    g1, g2 = grupos[0], grupos[1]
                    x1 = pd.to_numeric(df.loc[df[cat] == g1, var], errors='coerce').dropna()
                    x2 = pd.to_numeric(df.loc[df[cat] == g2, var], errors='coerce').dropna()
                    if len(x1) >= 1 and len(x2) >= 1:
                        u, pval = stats.mannwhitneyu(x1, x2, alternative='two-sided')
                        st.write(f"U = {u:.4f}, p-valor = {pval:.4g}")
                        if pval < alpha:
                            st.success("Rejeitamos H0 (distribuições diferentes).")
                        else:
                            st.info("Não rejeitamos H0.")
                    else:
                        st.warning("Dados insuficientes para o teste.")
                else:
                    st.warning("Escolha uma variável categórica com exatamente 2 grupos distintos.")
            else:
                st.info("Necessária uma numérica e uma categórica.")

        elif teste == "Qui-Quadrado de Independência (duas variáveis categóricas)":
            if len(cat_cols) >= 2:
                c1 = st.selectbox("Variável categórica 1:", cat_cols, key="chi_c1")
                c2 = st.selectbox("Variável categórica 2:", cat_cols, key="chi_c2")
                alpha = st.slider("α", 0.01, 0.10, 0.05, 0.01)
                if c1 != c2:
                    tabela = pd.crosstab(df[c1], df[c2])
                    chi2, p, dof, exp = stats.chi2_contingency(tabela)
                    st.write("Tabela de contingência:")
                    st.dataframe(tabela)
                    st.write(f"χ² = {chi2:.4f}, gl = {dof}, p-valor = {p:.4g}")
                    if p < alpha:
                        st.success("Rejeitamos H0 (há associação entre as variáveis).")
                    else:
                        st.info("Não rejeitamos H0 (sem evidência de associação).")
                else:
                    st.warning("Escolha variáveis diferentes.")
            else:
                st.info("Necessárias duas variáveis categóricas.")

    st.markdown("---")
    st.markdown("**Interpretação:** escreva sua análise dos resultados, implicações para o negócio e próximos passos.")