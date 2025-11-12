# ExpenseSplitter_v2_fixed.py
import streamlit as st
import pandas as pd
from urllib.parse import quote
from math import isclose

st.set_page_config(page_title="Expense Splitter", layout="wide")

# -----------------------
# CSS / Dark theme styling
# -----------------------
st.markdown(
    """
    <style>
    :root {
      --bg: #FFFFFF;
      --card: #0f1724;
      --muted: #9ca3af;
      --accent: #06b6d4;
      --accent-2: #0ea5a0;
      --text: #00008B;
      --input-bg: rgba(255,255,255,0.02);
      --border: rgba(255,255,255,0.04);
      --success: #10b981;
      --danger: #ef4444;
    }

    /* App background and main card */
    .stApp {
      background: linear-gradient(180deg, var(--bg), #FFFFFF);
      color: var(--text);
    }

    .card {
      background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
      padding: 14px;
      border-radius: 12px;
      border: 1px solid var(--border);
      box-shadow: 0 6px 18px rgba(2,6,23,0.6);
      margin-bottom: 12px;
    }

    h1, h2, h3, h4 {
      color: var(--text);
    }

    .muted { color: var(--muted); }
    .accent { color: var(--accent); font-weight:600; }
    .small { font-size: 0.9rem; color: var(--muted); }

    .balance-positive { color: var(--success); font-weight:700; }
    .balance-negative { color: var(--danger); font-weight:700; }

    .wa-btn, .upi-btn {
      display:inline-block;
      text-decoration:none;
      padding:8px 12px;
      border-radius:8px;
      font-weight:700;
      margin-right:8px;
      margin-top:6px;
    }

    .wa-btn { background: linear-gradient(90deg, #06b6d4, #0ea5a0); color:#041024; }
    .upi-btn { background: linear-gradient(90deg, #ffb86b, #ff7a7a); color:#041024; }

    /* Make labels and inputs clearly visible / consistent */
    label {
      color: #d1d5db !important;
      font-weight:600;
    }
    .stTextInput>div>div>input, .stTextInput>div>div>textarea, .stNumberInput>div>div>input {
      background: var(--input-bg) !important;
      color: var(--text) !important;
      border: 1px solid var(--border) !important;
      padding: 10px !important;
      border-radius: 8px !important;
    }
    .stSelectbox>div>div>div, .stMultiSelect>div>div>div {
      background: var(--input-bg) !important;
      color: var(--text) !important;
      border-radius: 8px !important;
      border: 1px solid var(--border) !important;
      padding: 6px 8px !important;
    }

    /* Table spacing */
    .rounded-table td, .rounded-table th { padding:8px 10px; }

    /* Small icon button look */
    .settings-icon {
      background: transparent;
      border: none;
      color: var(--muted);
      font-size: 18px;
      cursor: pointer;
    }

    /* Make download button subtle */
    .stDownloadButton>button {
      background: linear-gradient(90deg,#06b6d4,#0ea5a0);
      color: #041024;
      font-weight:700;
      border-radius:8px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------
# Helper functions
# -----------------------
def currency_fmt(amount, currency_symbol="₹", places=2):
    sign = "-" if amount < 0 else ""
    return f"{sign}{currency_symbol}{abs(amount):,.{places}f}"

def minimize_transactions(balances):
    debtors, creditors = [], []
    for person, bal in balances.items():
        if abs(bal) < 1e-9:
            continue
        if bal < 0:
            debtors.append([person, -bal])  # owes
        else:
            creditors.append([person, bal])  # to receive
    debtors.sort(key=lambda x: x[1])
    creditors.sort(key=lambda x: x[1], reverse=True)
    i = 0
    j = 0
    transfers = []
    while i < len(debtors) and j < len(creditors):
        d_person, d_amt = debtors[i]
        c_person, c_amt = creditors[j]
        transfer_amt = min(d_amt, c_amt)
        transfers.append((d_person, c_person, transfer_amt))
        debtors[i][1] -= transfer_amt
        creditors[j][1] -= transfer_amt
        if debtors[i][1] <= 1e-9:
            i += 1
        if creditors[j][1] <= 1e-9:
            j += 1
    return transfers

def wa_link(phone, text):
    if not phone:
        return None
    ph = "".join(c for c in phone if c.isdigit())
    return f"https://wa.me/{ph}?text={quote(text)}"

def upi_uri(pay_to_vpa, pay_to_name, amount, note="Expense settlement"):
    """
    Build a UPI deep link (common format):
    upi://pay?pa=<vpa>&pn=<name>&am=<amount>&cu=INR&tn=<note>
    Note: many UPI apps (GPay, PhonePe) accept this. On desktop this may open an app via intent handlers.
    """
    if not pay_to_vpa:
        return None
    pa = quote(pay_to_vpa)
    pn = quote(pay_to_name)
    am = f"{amount:.2f}"
    tn = quote(note)
    uri = f"upi://pay?pa={pa}&pn={pn}&am={am}&cu=INR&tn={tn}"
    return uri

# -----------------------
# Session state
# -----------------------
if "people" not in st.session_state:
    # each person: {"name","phone","upi"}
    st.session_state.people = []
if "expenses" not in st.session_state:
    st.session_state.expenses = []

def add_person(name, phone="", upi=""):
    st.session_state.people.append({"name": name.strip(), "phone": phone.strip(), "upi": upi.strip()})

def remove_person(index):
    st.session_state.people.pop(index)

def add_expense(desc, amount, paid_by_idx, split_mode="equal", custom_shares=None, included=None):
    st.session_state.expenses.append({
        "desc": desc,
        "amount": float(amount),
        "paid_by": int(paid_by_idx),
        "split_mode": split_mode,
        "custom_shares": custom_shares or {},
        "included": included or list(range(len(st.session_state.people)))
    })

def remove_expense(idx):
    st.session_state.expenses.pop(idx)

# -----------------------
# Sidebar (compact settings icon)
# -----------------------
with st.sidebar:
    # small settings header with gear icon (fixed quoting)
    cols = st.columns([8,1])
    cols[0].markdown(
        """<div style="padding:6px 0">
             <strong class="accent">Expense Splitter</strong>
             <div class="small muted">Configure trip & defaults</div>
           </div>""",
        unsafe_allow_html=True,
    )
    # icon style button (acts like a label to save space)
    if cols[1].button("⚙️", help="Settings", key="settings_icon"):
        # We don't need special behavior — it's just a compact icon placeholder
        st.info("Use the controls below to adjust tip / tax and defaults.")

    currency_symbol = st.selectbox("Currency symbol", ["₹", "$", "€", "£", "¥"], index=0, help="Currency symbol used in display.")
    tip_mode = st.selectbox("Tip mode", ["No Tip", "Tip % (applied to total)", "Tip fixed amount"], index=1)
    tip_value = 0.0
    if tip_mode == "Tip % (applied to total)":
        tip_value = st.number_input("Tip %", min_value=0.0, value=10.0, step=0.5)
    elif tip_mode == "Tip fixed amount":
        tip_value = st.number_input("Tip amount", min_value=0.0, value=0.0, step=1.0)
    tax_percent = st.number_input("Tax % (applied to total)", min_value=0.0, value=0.0, step=0.5)
    default_place = st.text_input("Trip / Place name", value="My Trip", help="A short label used in messages.")
    st.markdown("---")
    if st.button("Reset all data", key="reset_all_small"):
        st.session_state.people = []
        st.session_state.expenses = []
        st.rerun()

# -----------------------
# Main layout
# -----------------------
st.markdown(
    """<div class="card">
         <h1 class="accent">💸 Expense Splitter</h1>
         <div class="small muted">Track group expenses, auto-calc settlements, send WhatsApp & UPI links</div>
       </div>""",
    unsafe_allow_html=True,
)

col_left, col_right = st.columns([1, 2])

# -----------------------
# Left: People
# -----------------------
with col_left:
    st.markdown(
        """<div class="card">
             <h3>People</h3>
             <div class="small muted">Add travelers/friends and their contact/payment info</div>
           </div>""",
        unsafe_allow_html=True,
    )

    with st.form("add_person_form", clear_on_submit=True):
        # use compact labels & placeholders for clarity
        p_name = st.text_input("Full name", placeholder="Raja Kumar", key="name_input_v2")
        p_phone = st.text_input("Phone (with country code)", placeholder="+919876543210", key="phone_input_v2", help="Used for WhatsApp messages.")
        #p_upi = st.text_input("UPI ID (VPA) — optional", placeholder="yourname@bank / yourname@upi", key="upi_input_v2", help="Provide VPA to enable UPI payments (e.g. payee@bank).")
        submitted = st.form_submit_button("Add person")
        if submitted:
            if p_name.strip() == "":
                st.error("Please enter a name.")
            else:
                add_person(p_name, p_phone)
                st.success(f"Added {p_name}")
                st.rerun()

    if not st.session_state.people:
        st.info("No people added. Add friends to the left.")
    else:
        # neat list with remove icons
        for i, person in enumerate(st.session_state.people):
            cols = st.columns([3,2,1])
            cols[0].markdown(f"**{person['name']}**")
            cols[1].markdown(
                f"""<div class="small muted">Phone: {person['phone'] or '—'}</div>""",
                unsafe_allow_html=True,
            )
            #cols[2].markdown(f"<div class='small muted'>UPI: {person['upi'] or '—'}</div>", unsafe_allow_html=True)
            if cols[2].button("D", key=f"rem_person_v2_{i}"):
                remove_person(i)
                st.rerun()

# --------------- Right: Expenses
with col_right:
    st.markdown(
        """<div class="card">
             <h3>Expenses</h3>
             <div class="small muted">Add each bill, who paid, and how it should be shared</div>
           </div>""",
        unsafe_allow_html=True,
    )

    if not st.session_state.people:
        st.info("Add people first to record expenses.")
    else:
        with st.form("add_expense_form_v2", clear_on_submit=True):
            e_desc = st.text_input("Description (e.g., Dinner, Fuel)", value="Dinner", key="desc_v2")
            e_amount = st.number_input("Amount", min_value=0.0, value=0.0, step=10.0, key="amount_v2")
            paid_by = st.selectbox("Paid by", options=[f"{i} - {p['name']}" for i,p in enumerate(st.session_state.people)], key="paid_by_v2")
            split_mode = st.selectbox("Split mode", ["equal", "custom %", "specific persons"], key="split_mode_v2")
            custom_shares = {}
            included = list(range(len(st.session_state.people)))

            if split_mode == "custom %":
                st.markdown("Enter % shares per person (they will be normalized). Leave 0 for equal share.")
                cols = st.columns(len(st.session_state.people))
                for idx, p in enumerate(st.session_state.people):
                    val = cols[idx].number_input(f"{p['name']} %", min_value=0.0, max_value=100.0, value=0.0, key=f"share_v2_{len(st.session_state.expenses)}_{idx}")
                    if val > 0:
                        custom_shares[idx] = val
            elif split_mode == "specific persons":
                st.markdown("Select people who share this expense")
                included = []
                cols = st.columns(2)
                for idx, p in enumerate(st.session_state.people):
                    chk = cols[idx % 2].checkbox(p['name'], value=True, key=f"inc_v2_{len(st.session_state.expenses)}_{idx}")
                    if chk:
                        included.append(idx)
                if not included:
                    included = list(range(len(st.session_state.people)))

            add_sub = st.form_submit_button("Add expense")
            if add_sub:
                payer_idx = int(paid_by.split(" - ")[0])
                add_expense(e_desc, e_amount, payer_idx, split_mode, custom_shares, included)
                st.success("Expense added")
                st.rerun()

        # display existing expenses
        if not st.session_state.expenses:
            st.info("No expenses yet — add some above.")
        else:
            st.markdown(
                """<div class="card"><strong>Current expenses</strong></div>""",
                unsafe_allow_html=True,
            )
            for idx, e in enumerate(st.session_state.expenses):
                cols = st.columns([4,2,2,1])
                payer_name = st.session_state.people[e['paid_by']]['name'] if (0 <= e['paid_by'] < len(st.session_state.people)) else "Unknown"
                cols[0].markdown(
                    f"""**{e['desc']}** <div class="small muted">({payer_name} paid)</div>""",
                    unsafe_allow_html=True,
                )
                cols[1].markdown(
                    f"""<div class="small muted">{currency_fmt(e['amount'], currency_symbol)}</div>""",
                    unsafe_allow_html=True,
                )
                cols[2].markdown(
                    f"""<div class="small muted">{e['split_mode']}</div>""",
                    unsafe_allow_html=True,
                )
                if cols[3].button("🗑️", key=f"rem_exp_v2_{idx}"):
                    remove_expense(idx)
                    st.rerun()

# -----------------------
# Settlement & Calculation
# -----------------------
st.markdown("""---""")
st.markdown(
    """<div class="card">
         <h3>Settlement Summary</h3>
         <div class="small muted">Compute per-person share, suggested transfers, and send WhatsApp & UPI links</div>
       </div>""",
    unsafe_allow_html=True,
)

if st.button("Calculate settlement"):
    if not st.session_state.people or not st.session_state.expenses:
        st.warning("Add at least one person and one expense first.")
    else:
        N = len(st.session_state.people)
        per_paid = [0.0] * N
        per_share = [0.0] * N

        # process each expense
        for e in st.session_state.expenses:
            amt = float(e["amount"])
            payer = e["paid_by"]
            per_paid[payer] += amt

            if e["split_mode"] == "equal":
                participants = e.get("included", list(range(N)))
                k = len(participants) or N
                per = amt / k
                for p in participants:
                    per_share[p] += per

            elif e["split_mode"] == "custom %":
                shares = e.get("custom_shares", {})
                if not shares:
                    # fallback to equal
                    participants = e.get("included", list(range(N)))
                    k = len(participants) or N
                    per = amt / k
                    for p in participants:
                        per_share[p] += per
                else:
                    total_pct = sum(shares.values()) or 0.0
                    if isclose(total_pct, 0.0):
                        participants = e.get("included", list(range(N)))
                        k = len(participants) or N
                        per = amt / k
                        for p in participants:
                            per_share[p] += per
                    else:
                        for idx, pct in shares.items():
                            per_share[idx] += amt * (pct / total_pct)

            elif e["split_mode"] == "specific persons":
                participants = e.get("included", list(range(N)))
                k = len(participants) or N
                per = amt / k
                for p in participants:
                    per_share[p] += per

        total_base = sum(per_share)
        tip_amount = 0.0
        if tip_mode == "Tip % (applied to total)":
            tip_amount = total_base * (tip_value / 100.0)
        elif tip_mode == "Tip fixed amount":
            tip_amount = float(tip_value)
        tax_amount = total_base * (tax_percent / 100.0)
        grand_total = total_base + tip_amount + tax_amount

        # allocate tip & tax proportionally
        if total_base > 0:
            for i in range(N):
                proportion = per_share[i] / total_base
                per_share[i] += proportion * (tip_amount + tax_amount)

        # compute balances (positive => should receive, negative => owes)
        balances = {}
        for i in range(N):
            bal = per_paid[i] - per_share[i]
            balances[st.session_state.people[i]["name"]] = bal

        transfers = minimize_transactions(balances)

        # Show summary table
        st.markdown(f"**Trip / Place:** `{default_place}`")
        st.markdown(f"**Base total:** {currency_fmt(total_base, currency_symbol)}  •  **Tip:** {currency_fmt(tip_amount, currency_symbol)}  •  **Tax:** {currency_fmt(tax_amount, currency_symbol)}  •  **Grand total:** **{currency_fmt(grand_total, currency_symbol)}**")

        df = pd.DataFrame({
            "Person": [p["name"] for p in st.session_state.people],
            "Paid": [round(x,2) for x in per_paid],
            "Share (incl tip/tax)": [round(x,2) for x in per_share],
            "Net (Paid - Share)": [round(per_paid[i] - per_share[i],2) for i in range(N)],
            "Phone": [p.get("phone","") for p in st.session_state.people],
            "UPI": [p.get("upi","") for p in st.session_state.people],
        })
        # pretty display with currency formatting
        df_display = df.copy()
        df_display["Paid"] = df_display["Paid"].apply(lambda x: currency_fmt(x, currency_symbol))
        df_display["Share (incl tip/tax)"] = df_display["Share (incl tip/tax)"].apply(lambda x: currency_fmt(x, currency_symbol))
        df_display["Net (Paid - Share)"] = df_display["Net (Paid - Share)"].apply(lambda x: currency_fmt(x, currency_symbol))
        st.dataframe(df_display, use_container_width=True, height=300)

        st.markdown("### Net balances")
        col_a, col_b = st.columns([1,1])
        with col_a:
            for person, bal in balances.items():
                cls = "balance-positive" if bal > 0 else ("balance-negative" if bal < 0 else "small muted")
                st.markdown(f"""<div class="{cls}">{person}: {currency_fmt(bal, currency_symbol)}</div>""", unsafe_allow_html=True)

        with col_b:
            st.markdown("### Suggested transfers (minimized)")
            if not transfers:
                st.info("Everything is settled — no transfers needed!")
            else:
                for fr, to, amt in transfers:
                    st.markdown(f"**{fr} → {to} : {currency_fmt(amt, currency_symbol)}**")
                    # find receiver's upi
                    receiver = next((p for p in st.session_state.people if p["name"] == to), None)
                    payer = next((p for p in st.session_state.people if p["name"] == fr), None)

                    # WhatsApp for payer (prefill)
                    wa_msg = f"Hi {fr}, please pay {currency_fmt(amt, currency_symbol)} to {to} for '{default_place}'."
                    if payer and payer.get("phone"):
                        wa = wa_link(payer.get("phone"), wa_msg)
                        st.markdown(f"""<a class="wa-btn" href="{wa}" target="_blank">💬 WhatsApp (payer)</a>""", unsafe_allow_html=True)

                    # UPI link for payer to pay directly to receiver (if receiver has UPI)
                    if receiver and receiver.get("upi"):
                        upi_link = upi_uri(receiver.get("upi"), receiver.get("name"), amt, note=f"Payment to {receiver.get('name')} for {default_place}")
                        # show UPI button and also show the URI for copy
                        st.markdown(f"""<a class="upi-btn" href="{upi_link}" target="_blank">🔁 Pay via UPI</a>""", unsafe_allow_html=True)
                        st.markdown(f"""<div class="small muted">UPI URI: <code>{upi_link}</code></div>""", unsafe_allow_html=True)
                    else:
                        st.markdown(f"""<div class="small muted">Receiver has no UPI ID — ask them to add one to their profile.</div>""", unsafe_allow_html=True)

        # WhatsApp messages and UPI quick-send per person
        st.markdown("---")
        st.markdown("### WhatsApp & UPI quick actions (per person)")
        for i, p in enumerate(st.session_state.people):
            name = p["name"]
            phone = p.get("phone","")
            upi = p.get("upi","")
            net = balances.get(name, 0.0)

            cols = st.columns([3,2,3])
            with cols[0]:
                st.markdown(f"""**{name}** <div class="small muted">Net: {currency_fmt(net, currency_symbol)}</div>""", unsafe_allow_html=True)
            with cols[1]:
                # WhatsApp message describing their status
                if phone:
                    if net > 0:
                        msg = f"Hi {name}, you will receive {currency_fmt(net, currency_symbol)} for '{default_place}'."
                    elif net < 0:
                        msg = f"Hi {name}, you owe {currency_fmt(-net, currency_symbol)} for '{default_place}'."
                    else:
                        msg = f"Hi {name}, you're settled for '{default_place}'."
                    wa = wa_link(phone, msg)
                    st.markdown(f"""<a class="wa-btn" href="{wa}" target="_blank">💬 WhatsApp</a>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="small muted">No phone</div>""", unsafe_allow_html=True)

            with cols[2]:
                # If user owes (net < 0), show quick UPI pay link to pay the owed amount to a receiver (we can't decide receiver here)
                # Instead provide user's own UPI ID so others can pay them, or allow them to copy their UPI id.
                if upi:
                    st.markdown(f"""<div class="small muted">UPI: <code>{upi}</code></div>""", unsafe_allow_html=True)
                    # also provide a generic UPI link to request a payment (amount = abs(net)) if they are to receive money
                    if net > 0:
                        uri = upi_uri(upi, name, abs(net), note=f"Receive from group for {default_place}")
                        st.markdown(f"""<a class="upi-btn" href="{uri}" target="_blank">🔁 Request via UPI</a>""", unsafe_allow_html=True)
                        st.markdown(f"""<div class="small muted">Request URI: <code>{uri}</code></div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="small muted">No UPI ID</div>""", unsafe_allow_html=True)

        # CSV download
        st.markdown("---")
        csv = df.to_csv(index=False)
        st.download_button("Download breakdown CSV", csv, file_name="expense_breakdown.csv", mime="text/csv")

else:
    st.info("Click 'Calculate settlement' to compute splits, balances, and actions.")
