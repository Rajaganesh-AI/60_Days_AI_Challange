import streamlit as st

# Page configuration
st.set_page_config(
    page_title="💱 Currency Converter",
    page_icon="💱",
    layout="wide"
)

# Custom CSS for flashy UI
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .converter-box {
        background: rgba(255, 255, 255, 0.95);
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
    }
    .result-box {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    .info-box {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    h1 {
        color: white !important;
        text-align: center;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }
    .stSelectbox label, .stNumberInput label {
        color: white !important;
        font-weight: bold;
    }
    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Currency information
CURRENCY_INFO = {
    "INR": {"name": "Indian Rupee", "country": "🇮🇳 India", "symbol": "₹"},
    "USD": {"name": "US Dollar", "country": "🇺🇸 United States", "symbol": "$"},
    "EUR": {"name": "Euro", "country": "🇪🇺 European Union", "symbol": "€"},
    "GBP": {"name": "British Pound", "country": "🇬🇧 United Kingdom", "symbol": "£"}
}

# Static exchange rates (base: 1 USD)
EXCHANGE_RATES = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "INR": 83.12
}

def convert_currency(amount, from_currency, to_currency):
    """Convert amount from one currency to another"""
    if from_currency == to_currency:
        return amount
    
    # Convert to USD first, then to target currency
    amount_in_usd = amount / EXCHANGE_RATES[from_currency]
    converted_amount = amount_in_usd * EXCHANGE_RATES[to_currency]
    return converted_amount

# Initialize session state
if 'amount' not in st.session_state:
    st.session_state.amount = 100.0
if 'from_currency' not in st.session_state:
    st.session_state.from_currency = "USD"
if 'to_currency' not in st.session_state:
    st.session_state.to_currency = "INR"

# Title
st.markdown("<h1>💱 Currency Converter</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: white; font-size: 18px;'>Convert between major world currencies instantly!</p>", unsafe_allow_html=True)

# Main container
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("<div class='converter-box'>", unsafe_allow_html=True)
    
    # Amount input
    amount = st.number_input(
        "💰 Enter Amount",
        min_value=0.01,
        value=st.session_state.amount,
        step=0.01,
        format="%.2f"
    )
    
    # From currency
    from_currency = st.selectbox(
        "From Currency",
        options=list(CURRENCY_INFO.keys()),
        index=list(CURRENCY_INFO.keys()).index(st.session_state.from_currency)
    )
    
    # Display from currency info
    st.markdown(f"""
        <div class='info-box'>
            <strong>{CURRENCY_INFO[from_currency]['symbol']} {CURRENCY_INFO[from_currency]['name']}</strong><br>
            {CURRENCY_INFO[from_currency]['country']}
        </div>
    """, unsafe_allow_html=True)
    
    # To currency
    to_currency = st.selectbox(
        "To Currency",
        options=list(CURRENCY_INFO.keys()),
        index=list(CURRENCY_INFO.keys()).index(st.session_state.to_currency)
    )
    
    # Display to currency info
    st.markdown(f"""
        <div class='info-box'>
            <strong>{CURRENCY_INFO[to_currency]['symbol']} {CURRENCY_INFO[to_currency]['name']}</strong><br>
            {CURRENCY_INFO[to_currency]['country']}
        </div>
    """, unsafe_allow_html=True)
    
    # Swap button
    col_swap1, col_swap2, col_swap3 = st.columns([1, 1, 1])
    with col_swap2:
        if st.button("🔄 Swap", use_container_width=True):
            # Swap the currencies
            temp = st.session_state.from_currency
            st.session_state.from_currency = st.session_state.to_currency
            st.session_state.to_currency = temp
            st.rerun()
    
    # Update session state
    st.session_state.amount = amount
    st.session_state.from_currency = from_currency
    st.session_state.to_currency = to_currency
    
    # Convert
    converted_amount = convert_currency(amount, from_currency, to_currency)
    
    # Display result
    st.markdown(f"""
        <div class='result-box'>
            {CURRENCY_INFO[from_currency]['symbol']}{amount:,.2f} = {CURRENCY_INFO[to_currency]['symbol']}{converted_amount:,.2f}
        </div>
    """, unsafe_allow_html=True)
    
    # Exchange rate info
    rate = EXCHANGE_RATES[to_currency] / EXCHANGE_RATES[from_currency]
    st.markdown(f"<p style='text-align: center; color: #333; font-size: 14px;'>Exchange Rate: 1 {from_currency} = {rate:.4f} {to_currency}</p>", unsafe_allow_html=True)
    
    # Reset button
    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.amount = 100.0
        st.session_state.from_currency = "USD"
        st.session_state.to_currency = "INR"
        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("<br><p style='text-align: center; color: white; font-size: 12px;'>⚡ Static exchange rates for demonstration purposes</p>", unsafe_allow_html=True)