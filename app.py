from pathlib import Path

import altair as alt
import joblib
import numpy as np
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
MONTHS_AZ = [
    "Yan", "Fev", "Mar", "Apr", "May", "İyn",
    "İyl", "Avq", "Sen", "Okt", "Noy", "Dek",
]
st.set_page_config(page_title="Sığorta ödənişlərinin hesablanması", layout="wide")


@st.cache_resource
def load_artifacts(version):
    return (
        joblib.load(MODEL_DIR / "insurance_model.pkl"),
        joblib.load(MODEL_DIR / "model_features.pkl"),
    )


@st.cache_data
def load_data():
    data = pd.concat(
        [pd.read_csv(DATA_DIR / f"insurance_2016_{year}.csv")
         for year in [2025, 2026]],
        ignore_index=True,
    )
    return data.groupby(["company", "year", "month"], as_index=False).last()


def build_input_row(company, year, month, premiums, columns):
    row = pd.DataFrame({"company": [company], "year": [year],
                        "month": [month], "premiums": [premiums]})
    row["premium_category"] = pd.cut(
        row["premiums"], [-np.inf, 1_000, 10_000, 100_000, np.inf],
        labels=[
            "under_1m_AZN", "1m_to_10m_AZN",
            "10m_to_100m_AZN", "over_100m_AZN",
        ],
        right=False,
    )
    return pd.get_dummies(
        row, columns=["company", "premium_category"], dtype=int
    ).reindex(columns=columns, fill_value=0)


st.title("Sığorta ödənişlərinin hesablanması")
st.caption(
    "Məlum sığorta haqları əsasında dövr üzrə ödənişləri hesablayın. "
    "Bütün məbləğlər min AZN ilə göstərilir."
)
if not all(
    (MODEL_DIR / name).exists()
    for name in ["insurance_model.pkl", "model_features.pkl"]
):
    st.info(
        "Əvvəlcə notebooks/project.ipynb faylını işlədib "
        "modeli öyrədin və saxlayın."
    )
    st.stop()

model, feature_cols = load_artifacts(
    (MODEL_DIR / "insurance_model.pkl").stat().st_mtime_ns
)
info_path = MODEL_DIR / "model_info.pkl"
model_info = joblib.load(info_path) if info_path.exists() else {}
data = load_data()
left, right = st.columns([1, 1.2], gap="large")

with left:
    st.subheader("Şirkət məlumatları")
    company = st.selectbox("Şirkət", sorted(data["company"].unique()))
    year = st.number_input(
        "İl", min_value=2016, max_value=2100,
        value=int(data["year"].max()), step=1,
    )
    month = st.selectbox(
        "Ay", range(1, 13),
        format_func=lambda value: MONTHS_AZ[value - 1],
    )
    selection = (company, year, month)
    selected_period = data.loc[
        data["company"].eq(company)
        & data["year"].eq(year)
        & data["month"].eq(month)
    ]
    reported_premiums = selected_period["premiums"].dropna()
    earlier = data.loc[
        data["company"].eq(company) & data["month"].eq(month)
        & data["year"].lt(year) & data["premiums"].gt(0)
    ].sort_values("year")
    suggested = earlier.iloc[-1] if not earlier.empty else None
    default_premium = (
        float(reported_premiums.iloc[0])
        if not reported_premiums.empty
        else float(suggested["premiums"]) if suggested is not None else None
    )
    if st.session_state.get("premium_selection") != selection:
        st.session_state["premium_selection"] = selection
        st.session_state["premium_input"] = default_premium
    premiums = st.number_input(
        "İlin əvvəlindən sığorta haqları",
        min_value=0.0, step=100.0, key="premium_input",
        placeholder="Müsbət məbləğ daxil edin",
    )
    if reported_premiums.empty and suggested is not None:
        st.info(
            f"Təklif olunan haqq: {default_premium:,.2f} min AZN. "
            f"Mənbə: {int(suggested['year'])}-ci ilin eyni ayı. "
            "Bu, faktiki məbləğ və ya proqnoz deyil; dəyişə bilərsiniz."
        )
    elif reported_premiums.empty:
        st.info(
            "Bu dövr üçün faktiki və ya əvvəlki eyni ay üzrə müsbət "
            "haqq yoxdur. Müsbət məbləğ daxil edin."
        )
    else:
        st.caption(
            f"Faktiki sığorta haqqı: {reported_premiums.iloc[0]:,.2f} "
            "min AZN. Sahə avtomatik doldurulub; dəyişə bilərsiniz."
        )
    can_predict = premiums is not None and premiums > 0
    if premiums is not None and premiums <= 0:
        st.warning(
            "Sıfır məbləğ məlumatlarda saxlanılır. Model yalnız müsbət "
            "məbləğlərlə öyrədilib; hesablama üçün müsbət məbləğ lazımdır."
        )
    predict_clicked = st.button(
        "Ödənişi hesabla", type="primary", use_container_width=True,
        disabled=not can_predict,
    )

with right:
    st.subheader("Hesablanmış sığorta ödənişləri")
    if predict_clicked and can_predict:
        history = data.loc[
            data["company"].eq(company) & data["month"].eq(month)
        ].sort_values("year")
        reported = history.loc[history["year"].eq(year), "claims"].dropna()
        premium_history = history["premiums"].dropna()
        if not premium_history.empty:
            low, high = premium_history.quantile([0.05, 0.95])
            if premiums < low or premiums > high:
                st.warning(
                    f"Bu şirkət və ay üçün qeyri-adi sığorta haqqı: "
                    f"tarixi 5–95% intervalı {low:,.2f}–{high:,.2f} "
                    "min AZN-dir. Hesablama etibarsız ola bilər."
                )
        if model_info and company not in model_info["companies"]:
            st.warning("Bu şirkət seçilmiş təlim məlumatlarında olmayıb.")
        row = build_input_row(company, year, month, premiums, feature_cols)
        claims = max(0.0, float(np.expm1(model.predict(row)[0])))
        metrics = st.columns(3)
        metrics[0].metric("Təxmin", f"{claims:,.2f}")
        if not reported.empty:
            actual = float(reported.iloc[0])
            difference = claims - actual
            metrics[1].metric("Faktiki", f"{actual:,.2f}")
            metrics[2].metric("Fərq", f"{difference:+,.2f}")
            st.caption(
                "Müsbət fərq yüksək, mənfi fərq aşağı təxmin deməkdir. "
                "Müqayisə üçün dövrün faktiki sığorta haqqını daxil edin."
            )
        else:
            st.info(
                "Bu dövr üçün faktiki ödəniş yoxdur; fərq hesablanmır."
            )
        if not reported.empty:
            chart_data = pd.DataFrame({
                "Göstərici": ["Təxmin edilən ödənişlər", "Faktiki ödənişlər"],
                "Məbləğ": [claims, actual],
            })
            base = alt.Chart(chart_data).encode(
                x=alt.X("Göstərici:N", sort=None, title=None,
                        axis=alt.Axis(labelAngle=0)),
                y=alt.Y("Məbləğ:Q", title="Məbləğ"),
                color=alt.Color("Göstərici:N", legend=None),
                tooltip=["Göstərici:N",
                         alt.Tooltip("Məbləğ:Q", format=",.2f")],
            )
            chart = base.mark_bar() + base.mark_text(dy=-8).encode(
                text=alt.Text("Məbləğ:Q", format=",.2f")
            )
            st.altair_chart(chart, width="stretch")
        with st.expander("Bu ay üzrə şirkətin tarixçəsi"):
            st.dataframe(
                history[["year", "premiums", "claims"]].rename(columns={
                    "year": "İl", "premiums": "Sığorta haqları",
                    "claims": "Sığorta ödənişləri",
                }),
                hide_index=True,
            )
        st.caption(
            "Hesablama məlum sığorta haqlarına əsaslanır; "
            "gələcək üçün proqnoz deyil."
        )
    else:
        st.info("Məlumatları daxil edib «Ödənişi hesabla» düyməsinə basın.")

# Faktiki göstəricilər model təxminindən və daxil edilən haqdan asılı deyil.
st.divider()
st.subheader("Şirkətin faktiki göstəriciləri")
period = data.loc[data["year"].eq(year) & data["month"].eq(month)]
previous = data.loc[
    data["year"].eq(year - 1) & data["month"].eq(month),
    ["company", "premiums", "claims"],
].rename(columns={"premiums": "prior_premiums", "claims": "prior_claims"})
comparison = period.merge(previous, on="company", how="left")
for measure in ["premiums", "claims"]:
    base = comparison[f"prior_{measure}"]
    comparison[f"{measure}_growth"] = (
        comparison[measure].div(base.where(base > 0)).sub(1).mul(100)
    )
total_premiums = period["premiums"].sum(min_count=1)
comparison["premium_share"] = (
    comparison["premiums"] / total_premiums * 100
    if pd.notna(total_premiums) and total_premiums > 0 else np.nan
)
company_report = comparison.loc[comparison["company"].eq(company)]


def percent_label(value):
    return f"{value:,.1f}%" if pd.notna(value) else "Məlumat yoxdur"


if not company_report.empty:
    actual_row = company_report.iloc[0]
    cards = st.columns(3)
    cards[0].metric(
        "Sığorta haqlarının illik dəyişməsi",
        percent_label(actual_row["premiums_growth"]),
    )
    cards[1].metric(
        "Ödənişlərin illik dəyişməsi",
        percent_label(actual_row["claims_growth"]),
    )
    cards[2].metric(
        "Məlumatlardakı sığorta haqqı payı",
        percent_label(actual_row["premium_share"]),
    )
else:
    st.info("Seçilmiş şirkət və dövr üçün faktiki göstəricilər yoxdur.")

st.caption(
    f"Müqayisə: {year} və {year - 1}-ci illərin yanvar–"
    f"{MONTHS_AZ[month - 1]} dövrləri. Əvvəlki məbləğ sıfırdırsa "
    "və ya yoxdursa, faiz hesablanmır. Pay yalnız CSV-dəki şirkətlər "
    "üzrədir; rəsmi bazar payı deyil. Şirkətlərin əhatəsi dəyişə bilər."
)
if not comparison.empty:
    report = comparison[[
        "company", "premiums", "claims", "premiums_growth",
        "claims_growth", "premium_share",
    ]].sort_values("premiums", ascending=False).rename(columns={
        "company": "Şirkət",
        "premiums": "Sığorta haqları",
        "claims": "Ödənişlər",
        "premiums_growth": "Haqların illik dəyişməsi (%)",
        "claims_growth": "Ödənişlərin illik dəyişməsi (%)",
        "premium_share": "Məlumatlardakı haqq payı (%)",
    })
    with st.expander("Şirkətlərin eyni dövr üzrə müqayisəsi"):
        st.dataframe(report.round(2), hide_index=True)
    st.download_button(
        "Müqayisəni CSV kimi yüklə",
        report.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"sigorta_muqayise_{year}_{month:02d}.csv",
        mime="text/csv",
    )
