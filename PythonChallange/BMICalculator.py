import streamlit as st

st.set_page_config(page_title="BMI Calculator", page_icon="🏋️", layout="centered")

# --- Initialize Session State ---
if "height" not in st.session_state:
    st.session_state.height = ""
if "weight" not in st.session_state:
    st.session_state.weight = ""
if "result" not in st.session_state:
    st.session_state.result = None
if "message" not in st.session_state:
    st.session_state.message = ""

# --- Callbacks ---
def clear_fields():
    st.session_state.height = ""
    st.session_state.weight = ""
    st.session_state.result = None
    st.session_state.message = ""

def calculate_bmi():
    h = st.session_state.height
    w = st.session_state.weight
    try:
        h_val = float(h)
        w_val = float(w)
        h_m = h_val / 100
        bmi = w_val / (h_m * h_m)
        st.session_state.result = round(bmi, 2)

        if bmi < 18.5:
            st.session_state.message = "Underweight"
        elif bmi < 25:
            st.session_state.message = "Healthy"
        elif bmi < 30:
            st.session_state.message = "Overweight"
        else:
            st.session_state.message = "Obese"
    except:
        st.session_state.result = None
        st.session_state.message = "Please enter valid numbers."

# --- Sporty Styling ---
st.markdown("""
<style>
    .sporty-box {
        background: #f0f6ff;
        padding: 30px;
        border-radius: 16px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.08);
    }
    .title {
        font-size: 32px;
        font-weight: 800;
        color: #004aad;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .subtitle {
        color: #256abf;
        font-weight: 500;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- UI Layout ---
st.markdown("<div class='sporty-box'>", unsafe_allow_html=True)

st.markdown("<div class='title'>🏃‍♂️ Sporty BMI Calculator</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Warm form — enter your height & weight</div>", unsafe_allow_html=True)

# Center the form nicely
center = st.container()
with center:
    height = st.text_input("Enter Height (cm)", key="height", placeholder="e.g. 170")
    weight = st.text_input("Enter Weight (kg)", key="weight", placeholder="e.g. 65")

    # Buttons aligned horizontally and centered
    btn_col1, btn_col2, btn_col3 = st.columns([1,1,1])
    with btn_col1:
        pass
    with btn_col2:
        st.button("Calculate BMI", on_click=calculate_bmi, use_container_width=True)
        st.button("Clear", on_click=clear_fields, use_container_width=True)
    with btn_col3:
        pass

# ---- Output ----
if st.session_state.result is not None:
    st.success(f"Your BMI is **{st.session_state.result}**")
    msg = st.session_state.message
    if msg == "Healthy":
        st.success("Category: Healthy — great job! 💪")
    elif msg == "Underweight":
        st.info("Category: Underweight")
    elif msg == "Overweight":
        st.warning("Category: Overweight")
    else:
        st.error("Category: Obese")
elif st.session_state.message:
    st.error(st.session_state.message)

st.markdown("</div>", unsafe_allow_html=True)

st.caption("Tip: Use cm and kg. I can add imperial units if you want.")
