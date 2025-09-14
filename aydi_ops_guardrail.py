# aydi_ops_guardrail.py
# Streamlit app: AYDI Ops Guardrail — daily KPI tracker, budgets, and risk alerts.
# Now with EN/AR language toggle.

import os
import io
from datetime import date
import pandas as pd
import streamlit as st

APP_TITLE_EN = "AYDI Ops Guardrail — KPI & Risk Tracker"
APP_TITLE_AR = "حارس عمليات أيدي — مؤشرات الأداء والمخاطر"

DATA_PATH = "daily_metrics.csv"

# paths
LOGO_PATH = "assets/aydi_logo.png"


DEFAULT_TARGETS = {
    "annual_gmv_products": 482_125.0,    # OMR — sum of product categories only (excludes shipping & subs)
    "annual_units_products": 20_555,     # units — total units across 10 product categories
    "annual_deliveries": 14_550,         # deliveries — target handovers to last-mile partner
    "annual_vendors": 118,               # vendors onboarded
}

DEFAULT_FINANCE = {
    "commission_rate": 0.15,             # 15% platform commission (confirmed)
    "delivery_fee_per_order": 0.50,      # OMR — coordination fee from last-mile partner
    "annual_marketing_budget": 6_000.0,  # OMR
    "annual_admin_general": 58_487.0,    # OMR — admin & general
    "working_capital": 85_487.0,         # OMR — operating capital
}

DEFAULT_THRESHOLDS = {
    "min_conversion": 0.015,   # 1.5%
    "max_cac": 8.0,            # OMR
    "min_otd": 0.95,           # 95% on-time delivery
    "max_returns_rate": 0.07,  # 7%
    "min_aov": 20.0,           # OMR
}

COLUMNS = [
    "date","sessions","orders","gmv_products","marketing_spend",
    "deliveries","returns","first_mile_pickups","handoff_last_mile",
    "vendors_new","skus_added","skus_backlog",
    "csat","otd_total","otd_on_time",
]

# -------------------- Localization --------------------
L = {
    "EN": {
        "title": APP_TITLE_EN,
        "caption": "Track daily KPIs, budgets, and operational risks. Configure targets in the sidebar, enter daily metrics, and watch alerts fire when thresholds are breached.",
        "lang_label": "Language",
        "sidebar_header": "Targets & Finance",
        "sidebar_caption": "Adjust targets and financial assumptions as needed.",
        "annual_gmv": "Annual GMV target (products only, OMR)",
        "annual_units": "Annual units target (products)",
        "annual_deliveries": "Annual deliveries target",
        "annual_vendors": "Annual vendors target",
        "commission_rate": "Commission rate (platform)",
        "delivery_fee": "Delivery coordination fee (OMR/order)",
        "marketing_budget": "Annual marketing budget (OMR)",
        "admin_general": "Annual admin & general (OMR)",
        "working_capital": "Working capital (OMR)",
        "thresholds_header": "Alert Thresholds",
        "min_conv": "Min conversion rate",
        "max_cac": "Max CAC (OMR)",
        "min_otd": "Min on-time delivery rate",
        "max_returns": "Max returns rate",
        "min_aov": "Min AOV (OMR)",

        "kpi_header": "Today / MTD / YTD KPIs",
        "no_data_yet": "No data yet. Add your first daily record below.",
        "metric_aov_mtd": "AOV (OMR) — MTD",
        "metric_conv_mtd": "Conversion — MTD",
        "metric_cac_mtd": "CAC (OMR) — MTD",
        "metric_otd_mtd": "OTD — MTD",
        "metric_returns_mtd": "Returns — MTD",
        "metric_gmv_ytd": "GMV — YTD (OMR)",
        "metric_orders_ytd": "Orders — YTD",
        "metric_commission_ytd": "Commission Rev — YTD",
        "metric_delivery_ytd": "Delivery Rev — YTD",
        "metric_marketing_ytd": "Marketing — YTD",

        "risk_header": "Risk Alerts",
        "risk_no_data": "No alerts — add data first.",
        "risk_all_clear": "All clear. No threshold breaches this month.",
        "risk_low_conversion": "Low conversion: {val:.2f}% < target {target:.1f}%.",
        "risk_low_aov": "Low AOV: {val:.2f} OMR < target {target:.2f}.",
        "risk_high_cac": "High CAC: {val:.2f} OMR > limit {target:.2f}.",
        "risk_low_otd": "OTD below target: {val:.1f}% < {target:.0f}%.",
        "risk_high_returns": "Returns rate high: {val:.1f}% > {target:.0f}%.",

        "progress_header": "Progress vs Annual Targets",
        "progress_no_data": "No data yet.",
        "progress_gmv": "GMV {cur:.0f} / {tar:.0f}",
        "progress_units": "Units {cur} / {tar}",
        "progress_deliveries": "Deliveries {cur} / {tar}",
        "progress_vendors": "Vendors {cur} / {tar}",

        "trends_header": "Trends",

        "form_header": "Add / Update Daily Record",
        "date": "Date",
        "sessions": "Sessions (site visits)",
        "orders": "Orders (units sold)",
        "gmv": "GMV (products only, OMR)",
        "marketing": "Marketing spend (OMR)",
        "deliveries": "Deliveries (handed to last-mile)",
        "returns": "Returns (count)",
        "first_mile": "First-mile pickups (count)",
        "handoff": "Deliveries completed (POD)",
        "vendors_new": "Vendors onboarded (new)",
        "skus_added": "SKUs added",
        "skus_backlog": "SKU backlog (open)",
        "csat": "CSAT (0–100)",
        "otd_total": "OTD — total delivered today",
        "otd_on_time": "OTD — on-time subset",
        "save_update": "Save / Update",
        "saved": "Saved.",

        "export_header": "Data Export",
        "export_caption": "Add data to enable export.",
        "download_csv": "Download CSV",
    },
    "AR": {
        "title": APP_TITLE_AR,
        "caption": "تتبّع مؤشرات الأداء اليومية والميزانيات والمخاطر التشغيلية. عدّل الأهداف من الشريط الجانبي، وأدخل بياناتك اليومية، وستظهر التنبيهات عند تجاوز الحدود.",
        "lang_label": "اللغة",
        "sidebar_header": "الأهداف والمالية",
        "sidebar_caption": "يمكن تعديل الأهداف والافتراضات المالية عند الحاجة.",
        "annual_gmv": "هدف GMV السنوي (المنتجات فقط، ر.ع)",
        "annual_units": "هدف عدد الوحدات السنوي (منتجات)",
        "annual_deliveries": "هدف عدد التوصيلات السنوي",
        "annual_vendors": "هدف عدد المورّدين السنوي",
        "commission_rate": "نسبة العمولة (المنصّة)",
        "delivery_fee": "رسوم تنسيق التوصيل (ر.ع/طلب)",
        "marketing_budget": "ميزانية التسويق السنوية (ر.ع)",
        "admin_general": "المصاريف الإدارية والعمومية السنوية (ر.ع)",
        "working_capital": "رأس المال العامل (ر.ع)",
        "thresholds_header": "حدود التنبيه",
        "min_conv": "أدنى معدل تحويل",
        "max_cac": "أعلى CAC (ر.ع)",
        "min_otd": "أدنى معدل التسليم في الوقت",
        "max_returns": "أعلى معدل مرتجعات",
        "min_aov": "أدنى AOV (ر.ع)",

        "kpi_header": "مؤشرات اليوم / الشهر حتى تاريخه / السنة حتى تاريخه",
        "no_data_yet": "لا توجد بيانات بعد. أضف أول سجل يومي أدناه.",
        "metric_aov_mtd": "متوسط السلة (ر.ع) — شهر",
        "metric_conv_mtd": "التحويل — شهر",
        "metric_cac_mtd": "CAC (ر.ع) — شهر",
        "metric_otd_mtd": "OTD — شهر",
        "metric_returns_mtd": "المرتجعات — شهر",
        "metric_gmv_ytd": "GMV — سنة (ر.ع)",
        "metric_orders_ytd": "الطلبات — سنة",
        "metric_commission_ytd": "إيراد العمولة — سنة",
        "metric_delivery_ytd": "إيراد التوصيل — سنة",
        "metric_marketing_ytd": "التسويق — سنة",

        "risk_header": "تنبيهات المخاطر",
        "risk_no_data": "لا توجد تنبيهات — أضف بيانات أولاً.",
        "risk_all_clear": "لا توجد تجاوزات هذا الشهر.",
        "risk_low_conversion": "تحويل منخفض: {val:.2f}% < الهدف {target:.1f}%.",
        "risk_low_aov": "متوسط السلة منخفض: {val:.2f} ر.ع < الهدف {target:.2f}.",
        "risk_high_cac": "CAC مرتفع: {val:.2f} ر.ع > الحد {target:.2f}.",
        "risk_low_otd": "معدل التسليم في الوقت أقل من الهدف: {val:.1f}% < {target:.0f}%.",
        "risk_high_returns": "معدل المرتجعات مرتفع: {val:.1f}% > {target:.0f}%.",

        "progress_header": "التقدّم مقابل الأهداف السنوية",
        "progress_no_data": "لا توجد بيانات بعد.",
        "progress_gmv": "GMV ‏{cur:.0f} / ‏{tar:.0f}",
        "progress_units": "الوحدات ‏{cur} / ‏{tar}",
        "progress_deliveries": "التوصيلات ‏{cur} / ‏{tar}",
        "progress_vendors": "المورّدون ‏{cur} / ‏{tar}",

        "trends_header": "الاتجاهات",

        "form_header": "إضافة / تحديث سجل يومي",
        "date": "التاريخ",
        "sessions": "الزيارات (سيشنز)",
        "orders": "الطلبات (عدد الوحدات المباعة)",
        "gmv": "GMV (المنتجات فقط، ر.ع)",
        "marketing": "إنفاق التسويق (ر.ع)",
        "deliveries": "التوصيلات (المسلَّمة لآخر ميل)",
        "returns": "المرتجعات (عدد)",
        "first_mile": "سحوبات First-mile (عدد)",
        "handoff": "التسليم للعميل (تمّ)",
        "vendors_new": "المورّدون المسجّلون (جدد)",
        "skus_added": "عدد المنتجات المضافة (SKUs)",
        "skus_backlog": "تراكم المنتجات المفتوحة (SKU)",
        "csat": "رضا العملاء CSAT (0–100)",
        "otd_total": "OTD — إجمالي المسلَّم اليوم",
        "otd_on_time": "OTD — المسلَّم في الوقت",
        "save_update": "حفظ / تحديث",
        "saved": "تم الحفظ.",

        "export_header": "تصدير البيانات",
        "export_caption": "أضف بيانات لتفعيل التصدير.",
        "download_csv": "تنزيل CSV",
    }
}

def rtl_css():
    st.markdown(
        """
        <style>
        .block-container { direction: rtl; text-align: right; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    

# -------------------- Data store --------------------
def init_store():
    if not os.path.exists(DATA_PATH):
        df = pd.DataFrame(columns=COLUMNS)
        df.to_csv(DATA_PATH, index=False)

def load_data():
    init_store()
    df = pd.read_csv(DATA_PATH)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"]).dt.date
        for col in COLUMNS[1:]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df

def save_data(df):
    df.to_csv(DATA_PATH, index=False)

# -------------------- UI --------------------
def ui_lang():
    st.sidebar.selectbox(
        f"{L['EN']['lang_label']} / {L['AR']['lang_label']}",
        options=["EN","AR"],
        index=0 if st.session_state.get("lang","EN")=="EN" else 1,
        key="lang"
    )
    if st.session_state["lang"] == "AR":
        st.html('<div dir="rtl"></div>')
        rtl_css()
    else:
        st.html('<div dir="ltr"></div>')
    return st.session_state["lang"]

def t(lang, key):
    return L[lang][key]

def ui_sidebar(lang):
    st.sidebar.header(t(lang,"sidebar_header"))
    st.sidebar.caption(t(lang,"sidebar_caption"))

    annual_gmv = st.sidebar.number_input(t(lang,"annual_gmv"),
                                         value=float(DEFAULT_TARGETS["annual_gmv_products"]), step=100.0)
    annual_units = st.sidebar.number_input(t(lang,"annual_units"),
                                           value=int(DEFAULT_TARGETS["annual_units_products"]), step=10)
    annual_deliveries = st.sidebar.number_input(t(lang,"annual_deliveries"),
                                                value=int(DEFAULT_TARGETS["annual_deliveries"]), step=50)
    annual_vendors = st.sidebar.number_input(t(lang,"annual_vendors"),
                                             value=int(DEFAULT_TARGETS["annual_vendors"]), step=5)

    st.sidebar.divider()
    commission_rate = st.sidebar.number_input(t(lang,"commission_rate"),
                                              value=float(DEFAULT_FINANCE["commission_rate"]),
                                              step=0.01, min_value=0.0, max_value=1.0, format="%.2f")
    delivery_fee = st.sidebar.number_input(t(lang,"delivery_fee"),
                                           value=float(DEFAULT_FINANCE["delivery_fee_per_order"]), step=0.1)
    marketing_budget = st.sidebar.number_input(t(lang,"marketing_budget"),
                                               value=float(DEFAULT_FINANCE["annual_marketing_budget"]), step=100.0)
    admin_general = st.sidebar.number_input(t(lang,"admin_general"),
                                            value=float(DEFAULT_FINANCE["annual_admin_general"]), step=500.0)
    working_capital = st.sidebar.number_input(t(lang,"working_capital"),
                                              value=float(DEFAULT_FINANCE["working_capital"]), step=500.0)

    st.sidebar.divider()
    st.sidebar.header(t(lang,"thresholds_header"))
    min_conv = st.sidebar.number_input(t(lang,"min_conv"),
                                       value=float(DEFAULT_THRESHOLDS["min_conversion"]), step=0.001, format="%.3f")
    max_cac = st.sidebar.number_input(t(lang,"max_cac"),
                                      value=float(DEFAULT_THRESHOLDS["max_cac"]), step=0.5)
    min_otd = st.sidebar.number_input(t(lang,"min_otd"),
                                      value=float(DEFAULT_THRESHOLDS["min_otd"]), step=0.01, format="%.2f")
    max_returns = st.sidebar.number_input(t(lang,"max_returns"),
                                          value=float(DEFAULT_THRESHOLDS["max_returns_rate"]), step=0.01, format="%.2f")
    min_aov = st.sidebar.number_input(t(lang,"min_aov"),
                                      value=float(DEFAULT_THRESHOLDS["min_aov"]), step=1.0)

    return {
        "targets": {
            "annual_gmv": annual_gmv,
            "annual_units": annual_units,
            "annual_deliveries": annual_deliveries,
            "annual_vendors": annual_vendors,
        },
        "finance": {
            "commission_rate": commission_rate,
            "delivery_fee": delivery_fee,
            "marketing_budget": marketing_budget,
            "admin_general": admin_general,
            "working_capital": working_capital,
        },
        "thresholds": {
            "min_conv": min_conv,
            "max_cac": max_cac,
            "min_otd": min_otd,
            "max_returns": max_returns,
            "min_aov": min_aov,
        }
    }

def kpi_cards(df, config, lang):
    st.subheader(t(lang,"kpi_header"))
    if df.empty:
        st.info(t(lang,"no_data_yet"))
        return

    df_sorted = df.sort_values("date")
    today = df_sorted["date"].max()
    this_month = pd.to_datetime(today).month
    this_year = pd.to_datetime(today).year

    df_mtd = df_sorted[(pd.to_datetime(df_sorted["date"]).dt.month == this_month) &
                       (pd.to_datetime(df_sorted["date"]).dt.year == this_year)]
    df_ytd = df_sorted[pd.to_datetime(df_sorted["date"]).dt.year == this_year]

    def agg(dfx):
        sessions = dfx["sessions"].sum()
        orders = dfx["orders"].sum()
        gmv = dfx["gmv_products"].sum()
        deliveries = dfx["deliveries"].sum()
        marketing = dfx["marketing_spend"].sum()
        returns = dfx["returns"].sum()
        commission_revenue = gmv * config["finance"]["commission_rate"]
        handoffs = dfx["handoff_last_mile"].sum()
        delivery_revenue = handoffs * config["finance"]["delivery_fee"]  # use handoffs
        aov = (gmv / orders) if orders > 0 else 0.0
        conv = (orders / sessions) if sessions > 0 else 0.0
        cac = (marketing / orders) if orders > 0 else 0.0
        returns_rate = (returns / max(orders,1))
        otd_on_time = dfx["otd_on_time"].sum()
        otd_total = dfx["otd_total"].sum()
        otd_rate = (otd_on_time / otd_total) if otd_total > 0 else 0.0
        return {
            "sessions": sessions, "orders": orders, "gmv": gmv, "deliveries": deliveries,
            "marketing": marketing, "returns": returns, "commission_rev": commission_revenue,
            "delivery_rev": delivery_revenue, "aov": aov, "conv": conv, "cac": cac,
            "returns_rate": returns_rate, "otd_rate": otd_rate
        }

    mtd = agg(df_mtd)
    ytd = agg(df_ytd)
    today_row = df_sorted[df_sorted["date"] == today]
    td = agg(today_row) if not today_row.empty else {k:0 for k in mtd.keys()}

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(t(lang,"metric_aov_mtd"), f"{mtd['aov']:.2f}")
    c2.metric(t(lang,"metric_conv_mtd"), f"{mtd['conv']*100:.2f}%")
    c3.metric(t(lang,"metric_cac_mtd"), f"{mtd['cac']:.2f}")
    c4.metric(t(lang,"metric_otd_mtd"), f"{mtd['otd_rate']*100:.1f}%")
    c5.metric(t(lang,"metric_returns_mtd"), f"{mtd['returns_rate']*100:.1f}%")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(t(lang,"metric_gmv_ytd"), f"{ytd['gmv']:.0f}")
    c2.metric(t(lang,"metric_orders_ytd"), f"{int(ytd['orders'])}")
    c3.metric(t(lang,"metric_commission_ytd"), f"{ytd['commission_rev']:.0f}")
    c4.metric(t(lang,"metric_delivery_ytd"), f"{ytd['delivery_rev']:.0f}")
    c5.metric(t(lang,"metric_marketing_ytd"), f"{ytd['marketing']:.0f}")

def risk_alerts(df, config, lang):
    st.subheader(t(lang,"risk_header"))
    if df.empty:
        st.info(t(lang,"risk_no_data"))
        return

    df_sorted = df.sort_values("date")
    latest = df_sorted["date"].max()
    this_month = pd.to_datetime(latest).month
    this_year = pd.to_datetime(latest).year
    df_mtd = df_sorted[(pd.to_datetime(df_sorted["date"]).dt.month == this_month) &
                       (pd.to_datetime(df_sorted["date"]).dt.year == this_year)]

    sessions = df_mtd["sessions"].sum()
    orders = df_mtd["orders"].sum()
    gmv = df_mtd["gmv_products"].sum()
    marketing = df_mtd["marketing_spend"].sum()
    deliveries = df_mtd["deliveries"].sum()
    returns = df_mtd["returns"].sum()
    otd_on_time = df_mtd["otd_on_time"].sum()
    otd_total = df_mtd["otd_total"].sum()

    aov = (gmv / orders) if orders > 0 else 0.0
    conv = (orders / sessions) if sessions > 0 else 0.0
    cac = (marketing / orders) if orders > 0 else 0.0
    returns_rate = (returns / max(orders,1))
    otd_rate = (otd_on_time / otd_total) if otd_total > 0 else 0.0

    warnings = []
    if conv < config["thresholds"]["min_conv"]:
        warnings.append(t(lang,"risk_low_conversion").format(val=conv*100, target=config["thresholds"]["min_conv"]*100))
    if aov < config["thresholds"]["min_aov"]:
        warnings.append(t(lang,"risk_low_aov").format(val=aov, target=config["thresholds"]["min_aov"]))
    if cac > config["thresholds"]["max_cac"] and orders > 0:
        warnings.append(t(lang,"risk_high_cac").format(val=cac, target=config["thresholds"]["max_cac"]))
    if otd_rate < config["thresholds"]["min_otd"] and otd_total > 0:
        warnings.append(t(lang,"risk_low_otd").format(val=otd_rate*100, target=config["thresholds"]["min_otd"]*100))
    if returns_rate > config["thresholds"]["max_returns"] and orders > 0:
        warnings.append(t(lang,"risk_high_returns").format(val=returns_rate*100, target=config["thresholds"]["max_returns"]*100))

    if not warnings:
        st.success(t(lang,"risk_all_clear"))
    else:
        for w in warnings:
            st.error("• " + w)

def progress_vs_targets(df, config, lang):
    st.subheader(t(lang,"progress_header"))
    if df.empty:
        st.info(t(lang,"progress_no_data"))
        return

    df["year"] = pd.to_datetime(df["date"]).dt.year
    current_year = df["year"].max()
    dfx = df[df["year"] == current_year]

    gmv = dfx["gmv_products"].sum()
    orders = dfx["orders"].sum()
    deliveries = dfx["handoff_last_mile"].sum()  # progress vs annual handover target
    vendors_added = dfx["vendors_new"].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.progress(min(gmv / config["targets"]["annual_gmv"], 1.0),
                text=t(lang,"progress_gmv").format(cur=gmv, tar=config["targets"]["annual_gmv"]))
    c2.progress(min(orders / config["targets"]["annual_units"], 1.0),
                text=t(lang,"progress_units").format(cur=int(orders), tar=int(config["targets"]["annual_units"])))
    c3.progress(min(deliveries / config["targets"]["annual_deliveries"], 1.0),
                text=t(lang,"progress_deliveries").format(cur=int(deliveries), tar=int(config["targets"]["annual_deliveries"])))
    c4.progress(min(vendors_added / config["targets"]["annual_vendors"], 1.0),
                text=t(lang,"progress_vendors").format(cur=int(vendors_added), tar=int(config["targets"]["annual_vendors"])))

def charts(df, lang):
    st.subheader(t(lang,"trends_header"))
    if df.empty:
        return
    df_plot = df.copy()
    df_plot["date"] = pd.to_datetime(df_plot["date"])
    df_plot = df_plot.sort_values("date")

    st.line_chart(df_plot.set_index("date")[["gmv_products","orders","deliveries","marketing_spend"]], height=260)
    st.line_chart(df_plot.set_index("date")[["otd_on_time","otd_total","returns"]], height=200)

def input_form(df, lang):
    st.subheader(t(lang,"form_header"))
    with st.form("daily_input"):
        c1, c2, c3 = st.columns(3)
        d = c1.date_input(t(lang,"date"), value=date.today())
        sessions = c2.number_input(t(lang,"sessions"), min_value=0, step=10)
        orders = c3.number_input(t(lang,"orders"), min_value=0, step=1)

        c4, c5, c6 = st.columns(3)
        gmv = c4.number_input(t(lang,"gmv"), min_value=0.0, step=10.0, format="%.2f")
        marketing = c5.number_input(t(lang,"marketing"), min_value=0.0, step=5.0, format="%.2f")
        deliveries = c6.number_input(t(lang,"deliveries"), min_value=0, step=1)

        c7, c8, c9 = st.columns(3)
        returns = c7.number_input(t(lang,"returns"), min_value=0, step=1)
        first_mile = c8.number_input(t(lang,"first_mile"), min_value=0, step=1)
        handoff = c9.number_input(t(lang,"handoff"), min_value=0, step=1)

        c10, c11, c12 = st.columns(3)
        vendors_new = c10.number_input(t(lang,"vendors_new"), min_value=0, step=1)
        skus_added = c11.number_input(t(lang,"skus_added"), min_value=0, step=5)
        skus_backlog = c12.number_input(t(lang,"skus_backlog"), min_value=0, step=5)

        c13, c14, c15 = st.columns(3)
        csat = c13.number_input(t(lang,"csat"), min_value=0.0, max_value=100.0, step=1.0, format="%.0f")
        otd_total = c14.number_input(t(lang,"otd_total"), min_value=0, step=1)
        otd_on_time = c15.number_input(t(lang,"otd_on_time"), min_value=0, step=1)

        submitted = st.form_submit_button(t(lang,"save_update"))
        if submitted:
            row = {
                "date": d, "sessions": sessions, "orders": orders, "gmv_products": gmv,
                "marketing_spend": marketing, "deliveries": deliveries, "returns": returns,
                "first_mile_pickups": first_mile, "handoff_last_mile": handoff, "vendors_new": vendors_new,
                "skus_added": skus_added, "skus_backlog": skus_backlog, "csat": csat,
                "otd_total": otd_total, "otd_on_time": otd_on_time
            }
            if (df["date"] == d).any():
                df.loc[df["date"] == d, list(row.keys())] = list(row.values())
            else:
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            save_data(df)
            st.success(t(lang,"saved"))
    return load_data()

def downloads(df, lang):
    st.subheader(t(lang,"export_header"))
    if df.empty:
        st.caption(t(lang,"export_caption"))
        return
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(t(lang,"download_csv"), data=buf.getvalue(),
                       file_name="aydi_daily_metrics.csv", mime="text/csv")

# -------------------- Main --------------------
def main():
    st.set_page_config(page_title=APP_TITLE_EN, page_icon=LOGO_PATH, layout="wide")
    # Language selector first
    col_logo, col_title = st.columns([1, 9])
    with col_logo:
        st.image(LOGO_PATH, width=64)
        
    lang = ui_lang()
    st.title(t(lang,"title"))
    st.caption(t(lang,"caption"))
    
    
    config = ui_sidebar(lang)
    df = load_data()

    # Layout
    kpi_cards(df, config, lang)
    risk_alerts(df, config, lang)
    progress_vs_targets(df, config, lang)
    charts(df, lang)

    st.divider()
    df = input_form(df, lang)
    downloads(df, lang)

if __name__ == "__main__":
    main()
