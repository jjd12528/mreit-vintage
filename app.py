"""
Non-agency mREITs - exposure to 2022-2025 production, by securitization deal year.

Separate app from streamlit_app/ (John, 2026-10-27). Reads data.json, which
gen_vintage_data.py builds from VINTAGE_PROXY_BY_DEAL_YEAR_2026Q2.xlsx. No
dependency on filings, extraction code or the workbook at run time.

Colours: bucket colours copied from streamlit_app/app.py so the two apps read
the same. Every colour is set explicitly; nothing relies on the theme.
"""
import json
import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="mREIT vintage exposure", layout="wide",
                   initial_sidebar_state="collapsed")

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "data.json")) as f:
    D = json.load(f)

TK = D["tickers"]
YEARS = D["years"]
R = D["reits"]
INK, MUTE, RULE = "#111111", "#5A6270", "#E3E7EC"

RESI_COLORS = {
    "1 Prime jumbo & agency-eligible":          "#2E75B6",
    "3 Legacy RPL / NPL":                       "#A8D5A2",
    "2 Non-QM / expanded credit":               "#2E7D32",
    "5 Business purpose - rental/DSCR term":    "#F1A7A7",
    "4 Business purpose - bridge/transitional": "#D32F2F",
    "6 Second lien, HELOC & HEI":               "#7B0F13",
    "U Residential - unallocated":              "#9AA3AE",
}
AT_RISK = ["2 Non-QM / expanded credit", "4 Business purpose - bridge/transitional",
           "5 Business purpose - rental/DSCR term", "6 Second lien, HELOC & HEI"]
SHORT = {"1 Prime jumbo & agency-eligible": "Prime / agency-eligible",
         "3 Legacy RPL / NPL": "Legacy RPL / NPL", "2 Non-QM / expanded credit": "Non-QM",
         "4 Business purpose - bridge/transitional": "Bridge / transitional",
         "5 Business purpose - rental/DSCR term": "DSCR rental",
         "6 Second lien, HELOC & HEI": "Second lien / HELOC / HEI",
         "U Residential - unallocated": "Unallocated"}
YEAR_COLORS = {"2022": "#F4B183", "2023": "#C00000", "2024": "#7B0F13", "2025": "#E8A0A0"}

st.markdown(f"""
<style>
 .block-container {{padding-top: 1.5rem; max-width: 1500px;}}
 h1, h2, h3, p, li, td, th {{color: {INK};}}
 .note {{color: {MUTE}; font-size: 0.88rem; line-height: 1.45;}}
 .tag {{display:inline-block; padding:1px 6px; border-radius:3px; background:#F4F6F9;
        color:{INK}; font-size:0.8rem; border:1px solid {RULE};}}
</style>""", unsafe_allow_html=True)


def atr(t, years):
    b = R[t]["buckets"]
    return sum(b[k][YEARS.index(y)] for k in AT_RISK for y in years)


def ratio(t, years):
    return atr(t, years) / R[t]["ce"]


def ret_ratio(t, years):
    return sum(R[t]["at_risk_retained"][YEARS.index(y)] for y in years) / R[t]["ce"]


Y2225, Y2324 = ["2022", "2023", "2024", "2025"], ["2023", "2024"]

st.title("Non-agency mREITs: exposure to 2022–2025 production")
st.markdown(
    f"<p class='note'>As of {D['as_of_label']}. Proxy: each REIT's own-shelf residential exposure "
    "mapped to the <b>year its securitization closed</b> (or the loan's origination year where the REIT "
    "discloses it: AOMR, MFA, CIM). Retained interests are net of bonds sold to third parties; loans "
    "held unsecuritized are gross. <b>At-risk</b> = non-QM + bridge + DSCR rental + second lien / HELOC / HEI. "
    "Scaled to common equity (excluding NCI, less preferred liquidation preference).</p>",
    unsafe_allow_html=True)

# ------------------------------------------------------------------ 1. ranking
st.header("1. Ranking")
df = pd.DataFrame({
    "REIT": TK,
    "2022–25 at-risk ÷ equity": [ratio(t, Y2225) for t in TK],
    "2023–24 at-risk ÷ equity": [ratio(t, Y2324) for t in TK],
    "Retained only, 22–25 ÷ equity": [ret_ratio(t, Y2225) for t in TK],
    "2022–25 at-risk ($mm)": [atr(t, Y2225) / 1e3 for t in TK],
})
df = df.sort_values("2022–25 at-risk ÷ equity", ascending=False).reset_index(drop=True)
df.index = df.index + 1
c1, c2 = st.columns([1.1, 1])
with c1:
    order = list(df["REIT"])[::-1]
    fig = go.Figure()
    for y in Y2225:
        fig.add_bar(y=order, x=[atr(t, [y]) / R[t]["ce"] for t in order], name=y, orientation="h",
                    marker_color=YEAR_COLORS[y],
                    hovertemplate="%{y} " + y + ": %{x:.2f}x equity<extra></extra>")
    fig.update_layout(barmode="stack", height=360, margin=dict(l=10, r=10, t=30, b=10),
                      title=dict(text="2022–25 at-risk exposure ÷ common equity, by deal year",
                                 font=dict(color=INK, size=14)),
                      paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font=dict(color=INK),
                      legend=dict(orientation="h", y=-0.12, font=dict(color=INK), traceorder="normal"),
                      xaxis=dict(ticksuffix="x", gridcolor=RULE, color=INK),
                      yaxis=dict(color=INK))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
with c2:
    st.dataframe(df.style.format({"2022–25 at-risk ÷ equity": "{:.2f}x", "2023–24 at-risk ÷ equity": "{:.2f}x",
                                  "Retained only, 22–25 ÷ equity": "{:.2f}x",
                                  "2022–25 at-risk ($mm)": "{:,.0f}"}),
                 width="stretch", height=300)
    st.markdown("<p class='note'><b>Retained only</b> drops loans held unsecuritized "
                "(warehouse and pipeline). It is the pure deal-year proxy.</p>", unsafe_allow_html=True)

# ------------------------------------------------------------------ 2. per REIT
st.header("2. Each REIT by year and loan type")
st.markdown("<p class='note'>At-risk exposure ÷ common equity, same scale for all seven. Prime jumbo, agency-eligible "
            "and legacy RPL are mapped in the workbook but not shown. 2026 is mostly warehouse and pipeline.</p>",
            unsafe_allow_html=True)
ymax = max(sum(R[t]["buckets"][b][i] for b in AT_RISK) / R[t]["ce"] for t in TK for i in range(len(YEARS)))
cols = st.columns(len(TK))
for col, t in zip(cols, TK):
    fig = go.Figure()
    for b, c in RESI_COLORS.items():
        if b not in AT_RISK:
            continue
        v = [x / R[t]["ce"] for x in R[t]["buckets"][b]]
        if sum(v) == 0:
            continue
        fig.add_bar(x=["≤2021", "2022", "2023", "2024", "2025", "2026"], y=v, name=SHORT[b], marker_color=c,
                    showlegend=(t == TK[0]),
                    hovertemplate=SHORT[b] + " %{x}: %{y:.2f}x<extra></extra>")
    fig.update_layout(barmode="stack", height=300, margin=dict(l=5, r=5, t=40, b=5),
                      title=dict(text=f"<b>{t}</b><br><span style='font-size:11px;color:{MUTE}'>"
                                      f"22–25: {ratio(t, Y2225):.2f}x · 23–24: {ratio(t, Y2324):.2f}x</span>",
                                 font=dict(color=INK, size=14)),
                      paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font=dict(color=INK, size=10),
                      showlegend=False, xaxis=dict(color=INK, type="category", tickangle=-45),
                      yaxis=dict(range=[0, ymax * 1.05], ticksuffix="x", gridcolor=RULE, color=INK))
    with col:
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
st.markdown(" ".join(f"<span class='tag' style='border-left:10px solid {c}'>{SHORT[b]}</span>"
                     for b, c in RESI_COLORS.items() if b in AT_RISK), unsafe_allow_html=True)
with st.expander("What drives each REIT, and how solid the year split is"):
    for t in TK:
        st.markdown(f"**{t} — {D['names'][t]}.** {R[t]['note']}")

# ------------------------------------------------------------------ 3. MFA check
st.header("3. Does the proxy work? The MFA check")
m = [r for r in D["mfa_check"] if r["year"] not in ("2022-2025", "2023-2024")]
fig = go.Figure()
xs = [r["year"].replace("Prior (<=2021)", "≤2021") for r in m]
fig.add_bar(x=xs, y=[r["disclosed"] for r in m], name="MFA disclosed (6/30/26)", marker_color="#1F3864")
fig.add_bar(x=xs, y=[r["proxy_v1"] for r in m], name="Proxy, naive", marker_color="#C8D3E0")
fig.add_bar(x=xs, y=[r["proxy_v2"] for r in m], name="Proxy, as used", marker_color="#9DC3E6")
fig.update_layout(barmode="group", height=320, margin=dict(l=10, r=10, t=10, b=10),
                  paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", font=dict(color=INK),
                  legend=dict(orientation="h", y=-0.15, font=dict(color=INK)),
                  yaxis=dict(tickformat=".0%", gridcolor=RULE, color=INK), xaxis=dict(color=INK, type="category"))
c1, c2 = st.columns([1.3, 1])
with c1:
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
with c2:
    s = {r["year"]: r for r in D["mfa_check"]}
    st.markdown(
        f"MFA is the one REIT that discloses dollars by origination year, so the proxy was run on MFA's own "
        f"deal history and compared.\n\n"
        f"- **2022–25 share:** proxy {s['2022-2025']['proxy_v2']:.0%} vs disclosed {s['2022-2025']['disclosed']:.0%}.\n"
        f"- **2023–24 share:** proxy {s['2023-2024']['proxy_v2']:.0%} vs disclosed {s['2023-2024']['disclosed']:.0%}.\n"
        "- The naive version failed because re-securitizations put old loans into new deal years. "
        "The version used moves those deals back to the loans' years.\n"
        "- **Verdict:** usable for ranking, not for point estimates. It leans recent for any REIT with a legacy book.")

# ------------------------------------------------------------------ 4. performance
st.header("4. Delinquency where disclosed")
rows = []
for t in TK:
    for p in R[t]["perf"]:
        if p["value"] is not None:
            rows.append({"REIT": t, "Pool": p["pool"], "Measure": p["measure"], "Value": p["value"],
                         "Source": p["source"]})
pf = pd.DataFrame(rows).sort_values("Value", ascending=False).reset_index(drop=True)
pf.index = pf.index + 1
st.dataframe(pf.style.format({"Value": "{:.1%}"}), width="stretch", height=420)
st.markdown("<p class='note'>CIM and EFC do not disclose delinquency by deal. Per-deal rating-agency "
            "surveillance is subscription-only and is not included.</p>", unsafe_allow_html=True)

# ------------------------------------------------------------------ 5. caveats
st.header("5. Read before relying on this")
st.markdown("""
- **Most year splits are inferred.** Amounts come from 10-Qs and decks; how each REIT's retained book divides
  across deal years is an allocation, except at AOMR, MFA and CIM. RWT's 2022 figure is the least certain (±50%).
- **Deal year is not loan year** for re-securitizations. CIM's recent deals hold 2005–07 loans, so CIM uses its
  disclosed origination years instead.
- **Retained value is assumed proportional to loan balance.** Old low-coupon deals carry deep-discount
  subordinate bonds; new deals carry IO value.
- **Perimeter differs from the companion exposure app.** This app counts own-shelf exposure only; third-party
  RMBS, agency, reverse mortgages, MSRs and commercial are out.
""")
st.markdown("<p class='note'>Source: SEC EDGAR 10-Q/10-K filings, Q2-2026 earnings exhibits, and ABS-15G "
            "filings. Not investment advice.</p>", unsafe_allow_html=True)
