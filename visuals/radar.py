# -*- coding: utf-8 -*-
import plotly.graph_objects as go
import textwrap

def radar_plotly(
    titulo, dicionario, baseline_val=None,
    rmin=0, rmax=100, height=520, width=600, tema="dark"
):
    cats = list(dicionario.keys()); vals = list(dicionario.values())

    def wrap(s, w=12): return "<br>".join(textwrap.wrap(str(s), width=w)) if isinstance(s, str) else s
    cats_wrapped = [wrap(c, 12) for c in cats]
    cats_closed  = cats_wrapped + [cats_wrapped[0]]
    vals_closed  = vals + [vals[0]]

    if tema == "dark":
        paper_bg = plot_bg = "#0e1117"; grid="rgba(255,255,255,0.10)"; font="#e5e5e5"
        line_c="#4cc9f0"; fill_c="rgba(76,201,240,0.25)"; base_fill="rgba(200,200,200,0.12)"; base_line="rgba(160,160,160,0.6)"
    else:
        paper_bg = plot_bg = "#ffffff"; grid="rgba(0,0,0,0.12)"; font="#222"
        line_c="#2563eb"; fill_c="rgba(37,99,235,0.20)"; base_fill="rgba(0,0,0,0.06)"; base_line="rgba(120,120,120,0.7)"

    fig = go.Figure()

    if baseline_val is not None:
        base_list = [baseline_val for _ in cats]
        fig.add_trace(go.Scatterpolar(
            r=base_list+[base_list[0]], theta=cats_closed, fill="toself",
            name="Meta", line=dict(width=1.2, color=base_line),
            fillcolor=base_fill, hoverinfo="skip", opacity=1.0
        ))

    fig.add_trace(go.Scatterpolar(
        r=vals_closed, theta=cats_closed, fill="toself", name=titulo,
        mode="lines+markers", marker=dict(size=7),
        line=dict(width=3, color=line_c), fillcolor=fill_c,
        hovertemplate="<b>%{theta}</b><br>Valor: %{r}<extra></extra>"
    ))

    fig.update_layout(
        title=dict(text=titulo, x=0.5, y=0.95, font=dict(size=18, color=font)),
        paper_bgcolor=paper_bg, plot_bgcolor=plot_bg, font=dict(color=font, size=13),
        showlegend=False, margin=dict(l=10, r=10, t=40, b=10),
        height=height, width=width, autosize=False,
        polar=dict(
            bgcolor=plot_bg,
            radialaxis=dict(range=[rmin, rmax], gridcolor=grid, gridwidth=1,
                            tickfont=dict(size=11), showline=True, linecolor=grid),
            angularaxis=dict(gridcolor=grid, gridwidth=1, tickfont=dict(size=11),
                             direction="clockwise", rotation=90)
        )
    )
    return fig
