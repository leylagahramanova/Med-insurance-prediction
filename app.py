from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
MONTHS_AZ = [
    "Yan", "Fev", "Mar", "Apr", "May", "İyn",
    "İyl", "Avq", "Sen", "Okt", "Noy", "Dek",
]
st.set_page_config(page_title="Sığorta ödənişlərinin hesablanması", layout="wide")


@st.cache_resource
def load_artifacts(version):
    return (
        joblib.load(BASE_DIR / "insurance_model.pkl"),
        joblib.load(BASE_DIR / "model_features.pkl"),
    )


@st.cache_data
def load_data():
    data = pd.concat(
        [pd.read_csv(BASE_DIR / f"insurance_2016_{year}.csv")
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
    (BASE_DIR / name).exists()
    for name in ["insurance_model.pkl", "model_features.pkl"]
):
    st.info(
        "Əvvəlcə project.ipynb faylını işlədib modeli öyrədin və saxlayın."
    )
    st.stop()

model, feature_cols = load_artifacts(
    (BASE_DIR / "insurance_model.pkl").stat().st_mtime_ns
)
info_path = BASE_DIR / "model_info.pkl"
model_info = joblib.load(info_path) if info_path.exists() else {}
data = load_data()
left, right = st.columns([1, 1.2], gap="large")

with left:
    st.subheader("Şirkət məlumatları")
    with st.form("claims"):
        company = st.selectbox("Şirkət", sorted(data["company"].unique()))
        year = st.number_input(
            "İl", min_value=2016, max_value=2100,
            value=int(data["year"].max()), step=1,
        )
        month = st.selectbox(
            "Ay", range(1, 13),
            format_func=lambda value: MONTHS_AZ[value - 1],
        )
        premiums = st.number_input(
            "İlin əvvəlindən sığorta haqları (min AZN)", min_value=0.0, step=100.0
        )
        predict_clicked = st.form_submit_button(
            "Ödənişi hesabla", type="primary", use_container_width=True
        )

with right:
    st.subheader("Hesablanmış sığorta ödənişləri")
    if predict_clicked:
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
        if premiums == 0:
            st.warning(
                "Sıfır sığorta haqqı qeyri-sabit nəticə verə bilər. "
                "Nəticədən istifadə etməzdən əvvəl faktiki sığorta haqqını yoxlayın."
            )
        if model_info and company not in model_info["companies"]:
            st.warning("Bu şirkət seçilmiş təlim məlumatlarında olmayıb.")
        row = build_input_row(company, year, month, premiums, feature_cols)
        claims = max(0.0, float(np.expm1(model.predict(row)[0])))
        st.metric(
            (
                'İlin əvvəlindən təxmin edilən ödənişlər (min '
                'AZN)'
            ), f"{claims:,.2f}"
        )
        if not reported.empty:
            st.metric(
                "Seçilmiş dövrün faktiki ödənişləri (min AZN)",
                f"{reported.iloc[0]:,.2f}",
            )
        else:
            st.info("Seçilmiş dövr üçün faktiki ödəniş məlumatı yoxdur.")
        same_month = data.loc[data["month"].eq(month)]
        comparison = pd.Series({
            "Təxmin edilən ödənişlər": claims,
            "Şirkətin tarixi ortalaması": same_month.loc[
                same_month["company"].eq(company), "claims"
            ].mean(),
            "Bütün şirkətlər üzrə tarixi ortalama": same_month["claims"].mean(),
        }, name="Ödənişlər (min AZN)").dropna()
        if not reported.empty:
            comparison.loc["Faktiki ödənişlər (seçilmiş dövr)"] = (
                reported.iloc[0]
            )
        st.bar_chart(comparison.to_frame())
        with st.expander("Bu ay üzrə şirkətin tarixçəsi"):
            st.dataframe(
                history[["year", "premiums", "claims"]].rename(columns={
                    "year": "İl", "premiums": "Sığorta haqları (min AZN)",
                    "claims": "Sığorta ödənişləri (min AZN)",
                }),
                hide_index=True,
            )
        st.caption(
            "Tarixi ortalamalar mövcud illərin eyni ayı üzrə hesablanır. "
            "Hesablama məlum sığorta haqlarına əsaslanır; "
            "gələcək üçün proqnoz deyil."
        )
    else:
        st.info("Fill in the company details and click Ödənişi hesabla.")
