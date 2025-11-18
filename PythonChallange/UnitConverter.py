# streamlit_unit_converter.py
# Polished Streamlit Unit Converter (fixed CSS injection and layout order)
# - Currency (INR <-> USD) — real-time via multiple providers
# - Temperature (°C <-> °F)
# - Length (cm <-> inch)
# - Weight (kg <-> lb)

import streamlit as st
import requests
from decimal import Decimal, ROUND_HALF_UP
import time

st.set_page_config(page_title="Fancy Unit Converter", layout="wide", initial_sidebar_state="expanded")

# ---- Inject CSS safely (must be BEFORE layout) ----
st.markdown("""
<style>
/* Page background */
.stApp { background: linear-gradient(180deg, #f7f9fc 0%, #ffffff 40%); }

/* Card */
.card {
  background: white;
  border-radius: 12px;
  padding: 18px;
  box-shadow: 0 6px 18px rgba(35, 50, 90, 0.06);
  margin-bottom: 18px;
}

/* Header */
.header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 8px;
}
.logo-circle {
  width:56px; height:56px; border-radius:12px; background:linear-gradient(135deg,#5eead4,#60a5fa); display:flex; align-items:center; justify-content:center; font-weight:700; color:#042b6b; font-size:20px;
}

.muted { color: #6b7280; }
.small { font-size:12px; }

/* Make controls a bit tighter */
.stButton>button { border-radius:8px; }
.stNumberInput>div>div>input { padding: 8px 10px; }

/* sidebar extras */
.block-container .sidebar .stSelectbox, .block-container .sidebar .stRadio { padding-top: 8px; }
</style>
""", unsafe_allow_html=True)

# ----- Helpers -----
@st.cache_data(ttl=300)
def get_conversion_rate(from_currency: str, to_currency: str, retries: int = 2, backoff: float = 0.6):
    """Try multiple free providers and return (rate, date, error_msg, raw_exc, resp_snip)."""
    providers = []

    providers.append({
        "name": "exchangerate.host",
        "url": f"https://api.exchangerate.host/latest?base={from_currency}&symbols={to_currency}",
        "parser": lambda data: (data.get("rates", {}).get(to_currency), data.get("date")) if isinstance(data, dict) else (None, None)
    })

    providers.append({
        "name": "frankfurter",
        "url": f"https://api.frankfurter.app/latest?from={from_currency}&to={to_currency}",
        "parser": lambda data: (data.get("rates", {}).get(to_currency), data.get("date")) if isinstance(data, dict) else (None, None)
    })

    providers.append({
        "name": "open_er_api",
        "url": f"https://open.er-api.com/v6/latest/{from_currency}",
        "parser": lambda data: (data.get("rates", {}).get(to_currency), data.get("time_last_update_utc") or data.get("date")) if isinstance(data, dict) else (None, None)
    })

    last_exc = None
    resp_snip = None

    for prov in providers:
        url = prov["url"]
        for attempt in range(1, retries + 1):
            try:
                resp = requests.get(url, timeout=8)
                resp.raise_for_status()
                resp_text = resp.text
                resp_snip = resp_text[:1000]
                try:
                    data = resp.json()
                except Exception as je:
                    last_exc = f"{prov['name']} JSONDecodeError: {je}"
                    time.sleep(backoff * (2 ** (attempt - 1)))
                    continue

                if isinstance(data, dict) and data.get("success") is False and data.get("error"):
                    last_exc = f"{prov['name']} error: {data.get('error')}"
                    break

                rate, date = prov["parser"](data)
                if rate is not None:
                    st.session_state.setdefault("_last_rates", {})[(from_currency, to_currency)] = (rate, date)
                    return rate, date, None, None, resp_snip

                last_exc = f"{prov['name']} returned no rate"
                time.sleep(backoff * (2 ** (attempt - 1)))
            except Exception as e:
                last_exc = f"{prov['name']} {type(e).__name__}: {e}"
                time.sleep(backoff * (2 ** (attempt - 1)))

    cached = st.session_state.get("_last_rates", {}).get((from_currency, to_currency))
    if cached:
        return cached[0], cached[1], f"Used cached rate after failures ({last_exc})", last_exc, resp_snip

    return None, None, f"Failed to fetch rate from all providers ({last_exc})", last_exc, resp_snip


def format_number(x, ndigits=6):
    try:
        d = Decimal(str(x))
        quant = Decimal(1).scaleb(-ndigits)
        return str(d.quantize(quant, rounding=ROUND_HALF_UP))
    except Exception:
        return str(x)

# ----- Layout -----
menu_col, work_col = st.columns([1, 3])

with menu_col:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="header"><div class="logo-circle">UC</div><div><h3 style="margin:0">Unit Converter</h3><div class="muted small">Quick, accurate conversions</div></div></div>', unsafe_allow_html=True)

    converter = st.radio("", ("Currency Converter", "Temperature Converter", "Length Converter", "Weight Converter"), index=0)
    st.markdown("---")
    st.markdown("#### Settings")
    with st.expander("Currency options", expanded=False):
        st.write("Base/Target currently: INR <-> USD. Use manual override for other currencies or enable advanced mode.")
    st.markdown("---")
    if st.button("Reset all"):
        st.session_state.clear()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with work_col:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    # Header area
    st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center'><div><h2 style='margin:0'>{converter}</h2><div class='muted small'>Choose inputs on the left, results appear here</div></div><div><span class='muted small'>Built with Streamlit</span></div></div>", unsafe_allow_html=True)
    st.markdown("---")

    # Currency block
    if converter == "Currency Converter":
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("Live Currency Convertor")
            st.write("Fast, multiple-provider rates with a manual override if needed.")

            direction = st.selectbox("Direction", ("INR → USD", "USD → INR"))
            amount = st.number_input("Amount", min_value=0.0, format="%f", value=1.0)

            manual_override = st.checkbox("Use manual rate / override", value=False)
            manual_rate = None
            if manual_override:
                manual_rate = st.number_input("Manual rate (1 UNIT of base = ? of target)", format="%f", value=0.0)

            show_debug = st.checkbox("Show debugging info", value=False)

            if st.button("Convert"):
                if direction == "INR → USD":
                    from_c, to_c = "INR", "USD"
                else:
                    from_c, to_c = "USD", "INR"

                if manual_override and manual_rate and manual_rate > 0:
                    rate = manual_rate
                    date = "manual"
                    error_msg = None
                    raw_exc = None
                    resp_snip = None
                else:
                    rate, date, error_msg, raw_exc, resp_snip = get_conversion_rate(from_c, to_c)

                if rate is None:
                    st.error("Could not fetch live rate.")
                    if error_msg:
                        st.caption(error_msg)
                    if show_debug:
                        st.write("Raw exception / fetch error:")
                        st.text(raw_exc or "None")
                        st.write("Response snippet (truncated):")
                        st.code(resp_snip or "None")
                    st.warning("Enable 'Use manual rate' to enter a fallback rate, or check network/proxy settings.")
                else:
                    converted = amount * rate
                    label = " (manual)" if manual_override and manual_rate else ""
                    st.success(f"{format_number(amount,4)} {from_c} = {format_number(converted,4)} {to_c}{label}")
                    if error_msg:
                        st.caption(error_msg)
                    else:
                        st.caption(f"Rate: 1 {from_c} = {format_number(rate,6)} {to_c} (date: {date})")

        with col2:
            st.markdown('<div style="padding-left:12px">', unsafe_allow_html=True)
            st.markdown("### Quick conversions & tips")
            preview_rate, preview_date, preview_err, _, _ = get_conversion_rate("INR", "USD")
            if preview_rate:
                st.metric(label="1 INR → USD", value=f"{format_number(preview_rate,6)}", delta=f"as of {preview_date}")
                st.write("Common conversions:")
                for a in (1, 10, 100, 1000):
                    st.write(f"{a} → {format_number(a * preview_rate, 4)} USD")
            else:
                st.info("Quick conversions unavailable (no live or cached rate).")
                if preview_err:
                    st.caption(preview_err)
            st.markdown('</div>', unsafe_allow_html=True)

    # Temperature
    elif converter == "Temperature Converter":
        col1, col2 = st.columns([2,1])
        with col1:
            st.subheader("Temperature Converter")
            direction = st.selectbox("Direction", ("°C → °F", "°F → °C"))
            temp = st.number_input("Temperature", value=25.0, format="%f")
            if st.button("Convert"):
                if direction == "°C → °F":
                    res = (temp * 9/5) + 32
                    st.success(f"{format_number(temp,3)} °C = {format_number(res,3)} °F")
                else:
                    res = (temp - 32) * 5/9
                    st.success(f"{format_number(temp,3)} °F = {format_number(res,3)} °C")
        with col2:
            st.markdown("### Examples")
            st.write("0°C = 32°F")
            st.write("100°C = 212°F")

    # Length
    elif converter == "Length Converter":
        col1, col2 = st.columns([2,1])
        with col1:
            st.subheader("Length Converter")
            direction = st.selectbox("Direction", ("cm → inch", "inch → cm"))
            length = st.number_input("Length", value=100.0, format="%f")
            if st.button("Convert"):
                if direction == "cm → inch":
                    res = length / 2.54
                    st.success(f"{format_number(length,3)} cm = {format_number(res,3)} inch")
                else:
                    res = length * 2.54
                    st.success(f"{format_number(length,3)} inch = {format_number(res,3)} cm")
        with col2:
            st.markdown("### Examples")
            st.write("1 inch = 2.54 cm")
            st.write("30 cm ≈ 11.811 inch")

    # Weight
    elif converter == "Weight Converter":
        col1, col2 = st.columns([2,1])
        with col1:
            st.subheader("Weight Converter")
            direction = st.selectbox("Direction", ("kg → lb", "lb → kg"))
            weight = st.number_input("Weight", value=1.0, format="%f")
            if st.button("Convert"):
                if direction == "kg → lb":
                    res = weight * 2.2046226218
                    st.success(f"{format_number(weight,4)} kg = {format_number(res,4)} lb")
                else:
                    res = weight / 2.2046226218
                    st.success(f"{format_number(weight,4)} lb = {format_number(res,4)} kg")
        with col2:
            st.markdown("### Examples")
            st.write("1 kg = 2.2046226218 lb")
            st.write("5 kg ≈ 11.0231 lb")

    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption("Built with Streamlit — multiple providers for currency rates; manual override available.")

# Sidebar usage
st.sidebar.markdown("---")
st.sidebar.header("About")
st.sidebar.write("This app supports live INR↔USD conversion, temperature, length and weight conversions. Use 'Show debugging info' to troubleshoot rate fetches.")
