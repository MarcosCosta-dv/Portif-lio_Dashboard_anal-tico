# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
from core.data import carregar_df, tipo_variavel, ic_media, correlacao_pearson

def render():
    st.title("Análise de Dados — CP1")

    df = carregar_df()
    if df is None:
        st.warning("Carregue a base para continuar.")
        st.stop()

    st.subheader("1) Apresentação do Conjunto de Dados e Tipos de Variáveis")
    st.write("Descreva o contexto do problema, a origem da base e os objetivos da análise.")
    st.markdown("**Prévia:**")
    st.dataframe(df.head(20), use_container_width=True)

    meta = [{"coluna": c, "tipo_inferido": tipo_variavel(df[c]), "n_missing": int(df[c].isna().sum())} for c in df.columns]
    st.markdown("**Tipos de variáveis (inferidos):**")
    st.dataframe(pd.DataFrame(meta))

    st.markdown("**Perguntas de Análise (exemplos):**")
    st.markdown("""
    - Quais variáveis explicam melhor a variável-alvo?  
    - Existem diferenças significativas entre grupos (ex.: região, categoria)?  
    - Qual a média estimada e o IC para uma métrica crítica?  
    - Há correlação entre pares numéricos relevantes?
    """)

    st.subheader("2) Medidas Centrais, Dispersão, Correlação e Distribuições")
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = [c for c in df.columns if c not in num_cols]

    if len(num_cols) > 0:
        st.markdown("### Estatísticas Descritivas (Numéricas)")
        st.dataframe(df[num_cols].describe().T)

        sel_num = st.selectbox("Escolha uma variável numérica:", num_cols, index=0)
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

        st.markdown("### Matriz de Correlação (Pearson)")
        if len(num_cols) >= 2:
            corr = df[num_cols].corr(numeric_only=True)
            figc, axc = plt.subplots(figsize=(6, 4))
            sns.heatmap(corr, annot=True, fmt=".2f", ax=axc)
            axc.set_title("Correlação (Pearson)")
            st.pyplot(figc, clear_figure=True)

            st.markdown("**Teste de Correlação (Pearson)**")
            c1 = st.selectbox("X:", num_cols, key="corr_x")
            c2 = st.selectbox("Y:", num_cols, key="corr_y")
            if c1 != c2:
                r_p = correlacao_pearson(df[c1], df[c2])
                if r_p is not None:
                    r, p = r_p
                    st.write(f"r = {r:.4f}, p-valor = {p:.4g}")
                    st.success("Significativo (α=0,05)." if p < 0.05 else "Não significativo (α=0,05).")

            st.markdown("**Dispersão com tendência (regressão linear simples)**")
            x_sc = st.selectbox("Eixo X:", num_cols, key="scat_x")
            y_sc = st.selectbox("Eixo Y:", num_cols, key="scat_y")
            if x_sc != y_sc:
                x = pd.to_numeric(df[x_sc], errors='coerce')
                y = pd.to_numeric(df[y_sc], errors='coerce')
                mask = x.notna() & y.notna()
                fig_s, ax_s = plt.subplots()
                ax_s.scatter(x[mask], y[mask], alpha=0.6)
                try:
                    coef = np.polyfit(x[mask], y[mask], deg=1)
                    xr = np.linspace(x[mask].min(), x[mask].max(), 100)
                    ax_s.plot(xr, coef[0]*xr + coef[1])
                except Exception:
                    pass
                ax_s.set_xlabel(x_sc); ax_s.set_ylabel(y_sc); ax_s.set_title(f"{y_sc} ~ {x_sc}")
                st.pyplot(fig_s, clear_figure=True)
    else:
        st.info("Não foram detectadas colunas numéricas.")

    st.subheader("3) Intervalos de Confiança e Testes de Hipótese")
    aba_ic, aba_testes = st.tabs(["Intervalo de Confiança", "Testes de Hipótese"])

    with aba_ic:
        if len(num_cols) > 0:
            target_ic = st.selectbox("Variável alvo (numérica):", num_cols, key="ic_target")
            conf = st.slider("Nível de confiança", 0.80, 0.99, 0.95, 0.01)
            res = ic_media(df[target_ic], conf=conf)
            if res:
                st.write(f"n = {res['n']}, média = {res['media']:.4f}")
                st.write(f"IC {int(conf*100)}%: [{res['li']:.4f}, {res['ls']:.4f}]")
                import matplotlib.pyplot as plt
                fig_ic, ax_ic = plt.subplots(figsize=(5, 1.8))
                ax_ic.errorbar([0], [res['media']], yerr=[[res['media']-res['li']], [res['ls']-res['media']]], fmt='o', capsize=6)
                ax_ic.set_xlim(-1, 1); ax_ic.set_xticks([]); ax_ic.set_title(f"IC {int(conf*100)}% para {target_ic}")
                st.pyplot(fig_ic, clear_figure=True)
            else:
                st.warning("Amostra insuficiente (n≥2).")
        else:
            st.info("Carregue uma base com ao menos uma coluna numérica.")

    with aba_testes:
        testes = [
            "t de 1 amostra (média = valor de referência)",
            "t de 2 amostras (independentes)",
            "Mann-Whitney (2 grupos, não-paramétrico)",
            "Qui-Quadrado de Independência (categóricas)"
        ]
        teste = st.selectbox("Escolha o teste:", testes)

        if teste == testes[0]:
            if len(num_cols) > 0:
                var = st.selectbox("Variável numérica:", num_cols, key="t1_var")
                mu0 = st.number_input("Valor de referência (H0: média = mu0)", value=float(np.nanmean(pd.to_numeric(df[var], errors='coerce'))))
                alpha = st.slider("α", 0.01, 0.10, 0.05, 0.01)
                x = pd.to_numeric(df[var], errors='coerce').dropna()
                if len(x) >= 2:
                    from scipy import stats
                    tstat, pval = stats.ttest_1samp(x, mu0)
                    st.write(f"t = {tstat:.4f}, p-valor = {pval:.4g}")
                    st.success("Rejeitamos H0." if pval < alpha else "Não rejeitamos H0.")
                else:
                    st.warning("Dados insuficientes.")
            else:
                st.info("Necessária ao menos uma variável numérica.")

        elif teste == testes[1]:
            if len(num_cols) > 0:
                cat_cols = [c for c in df.columns if c not in num_cols]
                if len(cat_cols) == 0:
                    st.info("Adicione uma coluna categórica (2 níveis).")
                else:
                    var = st.selectbox("Variável numérica:", num_cols, key="t2_var")
                    cat = st.selectbox("Variável categórica (2 grupos):", cat_cols, key="t2_cat")
                    alpha = st.slider("α", 0.01, 0.10, 0.05, 0.01)
                    grupos = df[cat].dropna().unique()
                    if len(grupos) == 2:
                        g1, g2 = grupos[0], grupos[1]
                        x1 = pd.to_numeric(df.loc[df[cat] == g1, var], errors='coerce').dropna()
                        x2 = pd.to_numeric(df.loc[df[cat] == g2, var], errors='coerce').dropna()
                        if len(x1) >= 2 and len(x2) >= 2:
                            from scipy import stats
                            tstat, pval = stats.ttest_ind(x1, x2, equal_var=False)  # Welch
                            st.write(f"Grupos: {g1} (n={len(x1)}) vs {g2} (n={len(x2)})")
                            st.write(f"t = {tstat:.4f}, p-valor = {pval:.4g}")
                            st.success("Rejeitamos H0." if pval < alpha else "Não rejeitamos H0.")
                            import seaborn as sns, matplotlib.pyplot as plt
                            figx, axx = plt.subplots()
                            sns.boxplot(x=df[cat], y=df[var], ax=axx)
                            axx.set_title(f"{var} por {cat}")
                            st.pyplot(figx, clear_figure=True)
                        else:
                            st.warning("Amostras insuficientes (n≥2 por grupo).")
                    else:
                        st.warning("Escolha uma categórica com exatamente 2 grupos.")
            else:
                st.info("Necessária uma numérica e uma categórica.")

        elif teste == testes[2]:
            cat_cols = [c for c in df.columns if c not in num_cols]
            if len(num_cols) == 0 or len(cat_cols) == 0:
                st.info("Necessária uma numérica e uma categórica.")
            else:
                var  = st.selectbox("Variável numérica:", num_cols, key="mw_var")
                cat  = st.selectbox("Variável categórica (2 grupos):", cat_cols, key="mw_cat")
                alpha= st.slider("α", 0.01, 0.10, 0.05, 0.01)
                grupos = df[cat].dropna().unique()
                if len(grupos) == 2:
                    from scipy import stats
                    g1, g2 = grupos[0], grupos[1]
                    x1 = pd.to_numeric(df.loc[df[cat] == g1, var], errors='coerce').dropna()
                    x2 = pd.to_numeric(df.loc[df[cat] == g2, var], errors='coerce').dropna()
                    if len(x1) >= 1 and len(x2) >= 1:
                        u, pval = stats.mannwhitneyu(x1, x2, alternative='two-sided')
                        st.write(f"U = {u:.4f}, p-valor = {pval:.4g}")
                        st.success("Rejeitamos H0." if pval < alpha else "Não rejeitamos H0.")
                    else:
                        st.warning("Dados insuficientes.")
                else:
                    st.warning("Escolha categórica com 2 grupos.")

        elif teste == testes[3]:
            cat_cols = [c for c in df.columns if c not in num_cols]
            if len(cat_cols) >= 2:
                c1 = st.selectbox("Categórica 1:", cat_cols, key="chi_c1")
                c2 = st.selectbox("Categórica 2:", cat_cols, key="chi_c2")
                alpha = st.slider("α", 0.01, 0.10, 0.05, 0.01)
                if c1 != c2:
                    tabela = pd.crosstab(df[c1], df[c2])
                    from scipy import stats
                    chi2, p, dof, _ = stats.chi2_contingency(tabela)
                    st.write("Tabela de contingência:"); st.dataframe(tabela)
                    st.write(f"χ² = {chi2:.4f}, gl = {dof}, p-valor = {p:.4g}")
                    st.success("Rejeitamos H0 (há associação)." if p < alpha else "Não rejeitamos H0.")
                else:
                    st.warning("Escolha variáveis diferentes.")
            else:
                st.info("Necessárias duas categóricas.")

    st.markdown("---")
    st.markdown("**Interpretação:** escreva sua análise dos resultados, implicações para o negócio e próximos passos.")
