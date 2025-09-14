# aydi_ops_guardrail.py
# Streamlit app: AYDI Ops Guardrail — daily KPI tracker, budgets, and risk alerts.
# EN/AR localization, Google Sheets backend (optional), monthly Budget vs Burn card.

import os
import io
from datetime import date
import pandas as pd
import streamlit as st

# ----------- App constants (do not change unless the business asks) -----------
APP_TITLE_EN = "AYDI Ops Guardrail — KPI & Risk Tracker"
APP_TITLE_AR = "حارس عمليات أيدي — مؤشرات الأداء والمخاطر"

DATA_PATH = "daily_metrics.csv"  # CSV fallback path
LOGO_PATH = "assets/aydi_logo.png"

# Targets (initial)
DEFAULT_TARGETS = {
    "annual_gmv_products": 482_125.0,    # OMR — products GMV only
    "annual_units_products": 20_555,     # units — products
    "annual_deliveries": 14_550,         # handovers to last-mile (not POD)
    "annual_vendors": 118,               # vendors onboarded
}

# Finance assumptions
DEFAULT_FINANCE = {
    "commission_rate": 0.15,             # 15% platform commission
    "delivery_fee_per_order": 0.50,      # OMR — coordination fee per delivery (recognized on handover)
    "annual_marketing_budget": 6_000.0,  # OMR
    "annual_admin_general": 58_487.0,    # OMR
    "working_capital": 85_487.0,         # OMR
}

# Alert thresholds
DEFAULT_THRESHOLDS = {
    "min_conversion": 0.015,   # 1.5%
    "max_cac": 8.0,            # OMR
    "min_otd": 0.95,           # 95%
    "max_returns_rate": 0.07,  # 7%
    "min_aov": 20.0,           # OMR
}

# Data schema (daily)
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
        "datastore_header": "Data store",
        "use_sheets": "Use Google Sheets (if configured)",
        "backend_active": "Active backend: Google Sheets",
        "backend_csv": "Active backend: CSV file",
        "backend_fallback": "Google Sheets not configured or unavailable — falling back to CSV.",
        "annual_gmv": "Annual GMV target (products only, OMR)",
        "annual_units": "Annual units target (products)",
        "annual_deliveries": "Annual deliveries target (handover to last-mile)",
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

        "budget_header": "Monthly Budget vs Burn",
        "budget_hint": "Budget = (Marketing + Admin/General) / 12. Burn = Marketing MTD + Admin/General monthly.",
        "budget_label": "MTD Burn {burn:.0f} / Monthly Budget {budget:.0f} OMR",
        "wc_metric": "Working capital left",
        "wc_runway": "≈ {months:.1f} months at current monthly budget",

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
        "handoff": "Delivered to customer (POD)",
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
        "datastore_header": "مخزن البيانات",
        "use_sheets": "استخدم Google Sheets (إن تم إعداده)",
        "backend_active": "المخزن الفعّال: Google Sheets",
        "backend_csv": "المخزن الفعّال: ملف CSV",
        "backend_fallback": "لم يتم إعداد Google Sheets أو غير متاح — سيتم استخدام CSV.",
        "annual_gmv": "هدف GMV السنوي (المنتجات فقط، ر.ع)",
        "annual_units": "هدف عدد الوحدات السنوي (منتجات)",
        "annual_deliveries": "هدف التوصيلات السنوي (تسليم لشركة التوصيل)",
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
        "min_aov": "أدنى متوسط السلة (ر.ع)",

        "kpi_header": "مؤشرات اليوم / الشهر / السنة",
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

        "budget_header": "ميزانية الشهر مقابل الحرق",
        "budget_hint": "الميزانية = (التسويق + الإدارة/العموميات) ÷ 12. الحرق = تسويق شهر حتى تاريخه + قسمة الإدارة/العموميات الشهرية.",
        "budget_label": "الحرق {burn:.0f} / ميزانية الشهر {budget:.0f} ر.ع",
        "wc_metric": "رأس المال العامل المتبقي",
        "wc_runway": "≈ {months:.1f} شهر على الميزانية الشهرية الحالية",

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
        "sessions": "الزيارات (Sessions)",
        "orders": "الطلبات (عدد الوحدات)",
        "gmv": "GMV (المنتجات فقط، ر.ع)",
        "marketing": "إنفاق التسويق (ر.ع)",
        "deliveries": "التوصيلات (تسليم لشركة التوصيل)",
        "returns": "المرتجعات (عدد)",
        "first_mile": "سحوبات First-mile (عدد)",
        "handoff": "تم التسليم للعميل (POD)",
        "vendors_new": "المورّدون المسجّلون (جدد)",
        "skus_added": "المنتجات المضافة (SKUs)",
        "skus_backlog": "تراكم المنتجات المفتوحة (SKU)",
        "csat": "رضا العملاء (0–100)",
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
    """Flip layout to RTL for Arabic."""
    st.markdown(
        """
        <style>
        .block-container { direction: rtl; text-align: right; }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Robust progress helper (works on older/newer Streamlit)
def progress_with_text(value: float, text: str):
    try:
        st.progress(value, text=text)
    except TypeError:
        st.progress(value)
        st.caption(text)

# -------------------- Storage backends --------------------
class CSVStore:
    """Simple CSV storage."""
    def __init__(self, path: str):
        self.path = path
        if not os.path.exists(self.path):
            pd.DataFrame(columns=COLUMNS).to_csv(self.path, index=False)

    def load(self) -> pd.DataFrame:
        df = pd.read_csv(self.path)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"]).dt.date
            for col in COLUMNS[1:]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        return df[COLUMNS] if not df.empty else df

    def save(self, df: pd.DataFrame) -> None:
        out = df.copy()
        out = out[COLUMNS]  # ensure correct ordering
        out.to_csv(self.path, index=False)

class GSheetsStore:
    """Google Sheets storage with gspread; full-sheet replace on save."""
    def __init__(self, spreadsheet_id: str, worksheet_title: str = "daily_metrics"):
        self.ready = False
        self.error = None
        try:
            import gspread
            from google.oauth2.service_account import Credentials
        except Exception as e:
            self.error = f"Missing gspread/google-auth: {e}"
            return

        # Secrets-safe: gracefully handle missing secrets or malformed files
        try:
            sa_info = st.secrets["gcp_service_account"]
            _gs = st.secrets["gsheets"]
        except Exception:
            self.error = "Secrets not found."
            return

        creds = Credentials.from_service_account_info(
            sa_info,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ],
        )
        try:
            client = gspread.authorize(creds)
            sh = client.open_by_key(spreadsheet_id)
            try:
                ws = sh.worksheet(worksheet_title)
            except Exception:
                ws = sh.add_worksheet(title=worksheet_title, rows=1000, cols=len(COLUMNS))
                ws.update([COLUMNS])
            self.client = client
            self.sheet = sh
            self.ws = ws
            self.ready = True
        except Exception as e:
            self.error = f"GSheets auth/open failed: {e}"
            self.ready = False

    def load(self) -> pd.DataFrame:
        if not self.ready:
            return pd.DataFrame(columns=COLUMNS)
        try:
            rows = self.ws.get_all_values()
            if not rows:
                self.ws.update([COLUMNS])
                return pd.DataFrame(columns=COLUMNS)
            header = rows[0]
            data = rows[1:]
            df = pd.DataFrame(data, columns=header)
            for col in COLUMNS:
                if col not in df.columns:
                    df[col] = 0
            df = df[COLUMNS]
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
                for col in COLUMNS[1:]:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            return df
        except Exception:
            return pd.DataFrame(columns=COLUMNS)

    def save(self, df: pd.DataFrame) -> None:
        if not self.ready:
            return
        out = df.copy()
        out = out[COLUMNS]
        out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
        values = [COLUMNS] + out.astype(str).values.tolist()
        self.ws.clear()
        self.ws.update(values)

# -------------------- Secrets helpers --------------------
def has_sheets_config() -> bool:
    """True if a valid Sheets config exists; safe when secrets.toml is absent."""
    try:
        gs = st.secrets.get("gsheets", None)
        sa = st.secrets.get("gcp_service_account", None)
        return bool(gs and sa and gs.get("spreadsheet_id"))
    except Exception:
        return False

def get_backend(lang: str, prefer_sheets: bool = True):
    """
    Returns (store, backend_label, fallback_msg)
    prefer_sheets=True tries Google Sheets first (if configured), else CSV.
    Secrets-safe: never raises if secrets.toml is missing.
    """
    backend_label = L[lang]["backend_csv"]
    fallback_msg = None

    gsheets_conf = None
    try:
        gsheets_conf = st.secrets.get("gsheets", None)
    except Exception:
        gsheets_conf = None

    if prefer_sheets and gsheets_conf and gsheets_conf.get("spreadsheet_id"):
        store = GSheetsStore(
            spreadsheet_id=gsheets_conf["spreadsheet_id"],
            worksheet_title=gsheets_conf.get("worksheet", "daily_metrics"),
        )
        if getattr(store, "ready", False):
            backend_label = L[lang]["backend_active"]
            return store, backend_label, None
        else:
            fallback_msg = L[lang]["backend_fallback"]

    # Default / fallback
    store = CSVStore(DATA_PATH)
    return store, backend_label, fallback_msg

# -------------------- UI helpers --------------------
def ui_lang() -> str:
    # Sidebar language selector (sticky in session state)
    lang = st.sidebar.selectbox(
        f"{L['EN']['lang_label']} / {L['AR']['lang_label']}",
        options=["EN","AR"],
        index=0 if st.session_state.get("lang","EN")=="EN" else 1,
        key="lang"
    )
    # Flip layout for Arabic
    if lang == "AR":
        rtl_css()
        st.markdown('<div dir="rtl"></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div dir="ltr"></div>', unsafe_allow_html=True)
    return lang

def t(lang, key): return L[lang][key]

def ui_sidebar(lang):
    st.sidebar.header(t(lang,"sidebar_header"))
    st.sidebar.caption(t(lang,"sidebar_caption"))

    # Data store selection
    st.sidebar.subheader(t(lang, "datastore_header"))
    default_use_sheets = has_sheets_config()
    prefer_sheets = st.sidebar.checkbox(t(lang, "use_sheets"), value=default_use_sheets)

    # Targets
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
        "prefer_sheets": prefer_sheets,
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

# -------------------- KPI / Risk / Progress --------------------
def _agg_period(dfx: pd.DataFrame, finance: dict) -> dict:
    """Aggregate KPI metrics for a given slice."""
    sessions = dfx["sessions"].sum()
    orders = dfx["orders"].sum()
    gmv = dfx["gmv_products"].sum()
    deliveries = dfx["deliveries"].sum()  # handover count
    marketing = dfx["marketing_spend"].sum()
    returns = dfx["returns"].sum()

    commission_revenue = gmv * finance["commission_rate"]
    delivery_revenue = deliveries * finance["delivery_fee"]  # recognize on handover

    aov = (gmv / orders) if orders > 0 else 0.0
    conv = (orders / sessions) if sessions > 0 else 0.0
    cac = (marketing / orders) if orders > 0 else 0.0
    returns_rate = (returns / max(orders, 1))

    otd_on_time = dfx["otd_on_time"].sum()
    otd_total = dfx["otd_total"].sum()
    otd_rate = (otd_on_time / otd_total) if otd_total > 0 else 0.0

    return {
        "sessions": sessions, "orders": orders, "gmv": gmv, "deliveries": deliveries,
        "marketing": marketing, "returns": returns, "commission_rev": commission_revenue,
        "delivery_rev": delivery_revenue, "aov": aov, "conv": conv, "cac": cac,
        "returns_rate": returns_rate, "otd_rate": otd_rate
    }

def kpi_cards(df, config, lang):
    st.subheader(t(lang,"kpi_header"))
    if df.empty:
        st.info(t(lang,"no_data_yet"))
        return

    df_sorted = df.sort_values("date")
    latest = df_sorted["date"].max()
    this_month = pd.to_datetime(latest).month
    this_year = pd.to_datetime(latest).year

    df_mtd = df_sorted[(pd.to_datetime(df_sorted["date"]).dt.month == this_month) &
                       (pd.to_datetime(df_sorted["date"]).dt.year == this_year)]
    df_ytd = df_sorted[pd.to_datetime(df_sorted["date"]).dt.year == this_year]
    today_row = df_sorted[df_sorted["date"] == latest]

    mtd = _agg_period(df_mtd, config["finance"])
    ytd = _agg_period(df_ytd, config["finance"])
    _ = _agg_period(today_row, config["finance"]) if not today_row.empty else mtd

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

def budget_vs_burn(df, config, lang):
    """Monthly budget vs MTD burn card + working-capital runway helper."""
    st.subheader(t(lang, "budget_header"))
    st.caption(t(lang, "budget_hint"))

    # Compute monthly budget
    monthly_admin = config["finance"]["admin_general"] / 12.0
    monthly_marketing_budget = config["finance"]["marketing_budget"] / 12.0
    monthly_budget_total = monthly_admin + monthly_marketing_budget

    if df.empty:
        progress_with_text(0.0, t(lang, "budget_label").format(burn=0.0, budget=monthly_budget_total))
        wc_left = config['finance']['working_capital']
        runway = (wc_left / monthly_budget_total) if monthly_budget_total > 0 else 0.0
        st.metric(t(lang, "wc_metric"), f"{wc_left:.0f}", t(lang, "wc_runway").format(months=runway))
        return

    df_sorted = df.sort_values("date")
    latest = df_sorted["date"].max()
    this_month = pd.to_datetime(latest).month
    this_year = pd.to_datetime(latest).year
    months_elapsed = this_month  # Jan=1 .. current month

    df_mtd = df_sorted[(pd.to_datetime(df_sorted["date"]).dt.month == this_month) &
                       (pd.to_datetime(df_sorted["date"]).dt.year == this_year)]
    df_ytd = df_sorted[pd.to_datetime(df_sorted["date"]).dt.year == this_year]

    marketing_mtd = df_mtd["marketing_spend"].sum()
    marketing_ytd = df_ytd["marketing_spend"].sum()

    burn_mtd = marketing_mtd + monthly_admin  # assume admin is time-based monthly expense
    pct = min(burn_mtd / monthly_budget_total, 1.0) if monthly_budget_total > 0 else 0.0
    progress_with_text(pct, t(lang, "budget_label").format(burn=burn_mtd, budget=monthly_budget_total))

    wc_spent_est = marketing_ytd + (months_elapsed * monthly_admin)
    wc_left = max(config["finance"]["working_capital"] - wc_spent_est, 0.0)
    runway = (wc_left / monthly_budget_total) if monthly_budget_total > 0 else 0.0
    st.metric(t(lang, "wc_metric"), f"{wc_left:.0f}", t(lang, "wc_runway").format(months=runway))

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

    df_tmp = df.copy()
    df_tmp["year"] = pd.to_datetime(df_tmp["date"]).dt.year
    current_year = df_tmp["year"].max()
    dfx = df_tmp[df_tmp["year"] == current_year]

    gmv = dfx["gmv_products"].sum()
    orders = dfx["orders"].sum()
    deliveries = dfx["deliveries"].sum()  # compare to annual "handover to last-mile" target
    vendors_added = dfx["vendors_new"].sum()

    c1, c2, c3, c4 = st.columns(4)
    progress_with_text(min(gmv / config["targets"]["annual_gmv"], 1.0),
                       t(lang,"progress_gmv").format(cur=gmv, tar=config["targets"]["annual_gmv"]))
    progress_with_text(min(orders / config["targets"]["annual_units"], 1.0),
                       t(lang,"progress_units").format(cur=int(orders), tar=int(config["targets"]["annual_units"])))
    progress_with_text(min(deliveries / config["targets"]["annual_deliveries"], 1.0),
                       t(lang,"progress_deliveries").format(cur=int(deliveries), tar=int(config["targets"]["annual_deliveries"])))
    progress_with_text(min(vendors_added / config["targets"]["annual_vendors"], 1.0),
                       t(lang,"progress_vendors").format(cur=int(vendors_added), tar=int(config["targets"]["annual_vendors"])))

def charts(df, lang):
    st.subheader(t(lang,"trends_header"))
    if df.empty:
        return
    df_plot = df.copy()
    df_plot["date"] = pd.to_datetime(df_plot["date"])
    df_plot = df_plot.sort_values("date")

    st.line_chart(df_plot.set_index("date")[["gmv_products","orders","deliveries","marketing_spend"]], height=260)
    st.line_chart(df_plot.set_index("date")[["otd_on_time","otd_total","returns"]], height=200)

# -------------------- Input / Export --------------------
def input_form(df, store, lang):
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
        pod = c9.number_input(t(lang,"handoff"), min_value=0, step=1)

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
                "first_mile_pickups": first_mile, "handoff_last_mile": pod, "vendors_new": vendors_new,
                "skus_added": skus_added, "skus_backlog": skus_backlog, "csat": csat,
                "otd_total": otd_total, "otd_on_time": otd_on_time
            }
            if not df.empty and (df["date"] == d).any():
                df.loc[df["date"] == d, list(row.keys())] = list(row.values())
            else:
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            store.save(df)
            st.success(t(lang,"saved"))
    # Reload from store to ensure consistency with backend
    return store.load()

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
    col_logo, col_title = st.columns([1, 9])
    with col_logo:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=64)

    lang = ui_lang()
    st.title(t(lang,"title"))
    st.caption(t(lang,"caption"))

    config = ui_sidebar(lang)
    # Backend activation
    store, backend_label, fallback_msg = get_backend(lang, prefer_sheets=config["prefer_sheets"])
    with st.sidebar:
        st.success(backend_label if "Google" in backend_label else backend_label)
        if fallback_msg:
            st.warning(fallback_msg)

    df = store.load()

    # Layout
    kpi_cards(df, config, lang)
    budget_vs_burn(df, config, lang)       # NEW monthly card
    risk_alerts(df, config, lang)
    progress_vs_targets(df, config, lang)
    charts(df, lang)

    st.divider()
    df = input_form(df, store, lang)
    downloads(df, lang)

if __name__ == "__main__":
    main()

