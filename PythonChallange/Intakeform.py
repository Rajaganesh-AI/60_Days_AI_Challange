# intake_form.py
# Racket Sports Academy intake form — multiple sports, BMI, styled header, side-by-side layout
# Run: pip install streamlit
#      streamlit run intake_form.py

import streamlit as st
import datetime
import html

# -------------------------
# Page config & top header bar (nice look)
# -------------------------
st.set_page_config(page_title="Racket Sports Academy Intake", layout="wide")

# Inline CSS for a top header bar
st.markdown(
    """
    <style>
    .top-bar {
        background: linear-gradient(90deg, #0f172a, #0369a1);
        color: white;
        padding: 18px 24px;
        border-radius: 8px;
        box-shadow: 0 6px 18px rgba(3, 105, 161, 0.15);
        margin-bottom: 18px;
    }
    .top-bar h1 {
        margin: 0;
        font-size: 28px;
        letter-spacing: 0.4px;
    }
    .top-bar p {
        margin: 4px 0 0 0;
        opacity: 0.9;
        font-size: 14px;
    }
    </style>
    <div class="top-bar">
        <h1>Racket Sports Academy Intake Form</h1>
        <p>Register to join coaching & training sessions — tennis, badminton, table tennis, pickleball and more.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("Fill out the form on the left. A personalized banner & summary will appear on the right after submission.")

# -------------------------
# Layout: left form, right results
# -------------------------
col_left, col_right = st.columns([1.1, 1])

# -------------------------
# Left column: Form
# -------------------------
with col_left:
    with st.form(key="intake_form"):
        name = st.text_input("1) Full name", placeholder="Enter full name")

        age = st.slider("2) Age", min_value=4, max_value=100, value=16, step=1)

        # Keep as text inputs (as requested previously), validated later.
        height_text = st.text_input("3) Height (centimeter)", placeholder="e.g. 170")
        weight_text = st.text_input("4) Weight (kilogram)", placeholder="e.g. 65")

        dob = st.date_input(
            "5) Date of birth",
            value=datetime.date(2008, 1, 1),
            min_value=datetime.date(1900, 1, 1),
            max_value=datetime.date.today(),
        )

        # MULTI-SELECT for sports (multiple sports allowed)
        sports_options = ["Tennis", "Badminton", "Table Tennis", "Pickle Ball"]
        sports_selected = st.multiselect(
            "6) Sports interested in (select one or more)",
            options=sports_options
        )

        # Gender radio (horizontal if supported)
        gender = st.radio("7) Gender", options=["Male", "Female"], horizontal=True)

        submitted = st.form_submit_button("Submit intake form")

# -------------------------
# Helper functions
# -------------------------
def try_parse_float(text):
    try:
        return float(text)
    except Exception:
        return None

def calculate_bmi(weight_kg: float, height_cm: float):
    """Return BMI (float) given weight in kg and height in cm, or None if invalid."""
    if weight_kg is None or height_cm is None or height_cm <= 0:
        return None
    h_m = height_cm / 100.0
    bmi = weight_kg / (h_m * h_m)
    return bmi

def bmi_category(bmi: float):
    if bmi is None:
        return "Unknown"
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal weight"
    if bmi < 30:
        return "Overweight"
    return "Obese"

# -------------------------
# Right column: Results (banner + summary)
# -------------------------
with col_right:
    if submitted:
        # Basic validations
        errors = []
        if not name.strip():
            errors.append("Please enter a name.")

        h = try_parse_float(height_text)
        if h is None or h <= 0:
            errors.append("Please enter a valid numeric height in centimeters (e.g. 170).")

        w = try_parse_float(weight_text)
        if w is None or w <= 0:
            errors.append("Please enter a valid numeric weight in kilograms (e.g. 65).")

        if not sports_selected:
            errors.append("Please select at least one sport you're interested in.")

        if errors:
            st.error("Please fix the following issues:")
            for e in errors:
                st.write("- " + e)
        else:
            # Age cross-check from DOB
            today = datetime.date.today()
            dob_age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            age_note = ""
            if dob_age != age:
                age_note = f" (DOB indicates age ≈ {dob_age})"

            # Compute BMI and category
            bmi_value = calculate_bmi(w, h)
            bmi_cat = bmi_category(bmi_value)
            bmi_text = f"{bmi_value:.1f} ({bmi_cat})" if bmi_value is not None else "N/A"

            # Format sports list
            sports_joined = ", ".join(sports_selected)

            # Banner HTML (polished)
            banner_html = f"""
            <div style="
                border-radius:12px;
                padding:18px;
                background: linear-gradient(90deg, #0ea5e9, #0369a1);
                color: white;
                box-shadow: 0 8px 24px rgba(3,105,161,0.18);
                margin-bottom: 12px;
            ">
                <h3 style="margin:0 0 8px 0;">🏆 Welcome to Racket Sports Academy, {html.escape(name)}! 🏆</h3>
                <p style="margin:0 0 10px 0; font-size:14px;">
                    Excited to have you for: <strong>{html.escape(sports_joined)}</strong>
                </p>
                <div style="display:flex; flex-direction:column; gap:6px; font-size:13px;">
                    <span><strong>Age:</strong> {age}{age_note}</span>
                    <span><strong>DOB:</strong> {dob.strftime('%d %b %Y')}</span>
                    <span><strong>Gender:</strong> {gender}</span>
                    <span><strong>Height:</strong> {h:.1f} cm</span>
                    <span><strong>Weight:</strong> {w:.1f} kg</span>
                    <span><strong>BMI:</strong> {bmi_text}</span>
                </div>
                <p style="margin-top:12px; font-size:13px;">
                    📅 We'll contact you soon with trial session slots and membership details.
                </p>
            </div>
            """
            st.markdown(banner_html, unsafe_allow_html=True)

            # Summary card
           # st.subheader("📋 Registration Summary")
           # st.write(f"**Name:** {name}")
           # st.write(f"**Sports interested:** {sports_joined}")
           # st.write(f"**Age:** {age} ({dob.strftime('%Y-%m-%d')})")
           # st.write(f"**Gender:** {gender}")
           # st.write(f"**Height:** {h:.1f} cm")
           # st.write(f"**Weight:** {w:.1f} kg")
           # if bmi_value is not None:
           #     st.write(f"**BMI:** {bmi_value:.1f} — *{bmi_cat}*")
           # else:
           #     st.write("**BMI:** N/A")
           # st.success("✅ Intake form submitted successfully!")
    else:
        # Placeholder message before submission
        st.info("Submit the form on the left to see your personalized banner & summary here.")

# -------------------------
# Optional: Footer / tips
# -------------------------
st.markdown("---")
st.markdown(
    "<small>Tip: Use the multi-select to choose more than one sport. Height and weight must be numeric to compute BMI.</small>",
    unsafe_allow_html=True,
)
