"""
Digital Wallet (UPI-style) - Final Corrected Version

Project:         Digital Wallet Simulator v5.0 (Dark Mode, Full Menu)
Author:          Gemini (based on an original concept by Sanket Dodya)
Date:            September 29, 2025
Description:     A full-featured, professionally designed web-based digital 
                 payment simulator. This version corrects the dashboard UI to 
                 explicitly list all 11 required functionalities in the sidebar, 
                 as per user feedback, while maintaining a sleek black theme.
"""

# ==============================================================================
# S1: IMPORTS & INITIAL CONFIGURATION
# ==============================================================================
import streamlit as st
import json
import time
from datetime import datetime
from collections import defaultdict
import pandas as pd
import qrcode
from PIL import Image
import io

# --- Page Configuration ---
st.set_page_config(
    page_title="Gemini UPI Wallet",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# S2: APPLICATION CONSTANTS & MOCK DATABASE
# ==============================================================================

CATEGORIES = ["🍔 Food", "✈️ Travel", "🧾 Bills", "🛍️ Shopping", "🎓 Education", "💊 Health", "🎁 Other"]
LOCKOUT_DURATION_SECONDS = 60
MAX_LOGIN_ATTEMPTS = 3
HIGH_VALUE_TRANSACTION_THRESHOLD = 3000

def get_initial_mock_data():
    """Provides a fresh copy of the mock database for each new session."""
    return {
        "accounts": {
            "alice": {"pin": "1111", "balance": 830.0, "transactions": [], "failed_attempts": 0, "locked_until": 0, "requests": [], "display_name": "Alice Wonderland"},
            "bob": {"pin": "2222", "balance": 625.0, "transactions": [], "failed_attempts": 0, "locked_until": 0, "requests": [], "display_name": "Bob Builder"},
            "charlie": {"pin": "3333", "balance": 300.0, "transactions": [], "failed_attempts": 0, "locked_until": 0, "requests": [], "display_name": "Charlie Chaplin"},
            "disha": {"pin": "4444", "balance": 100.0, "transactions": [], "failed_attempts": 0, "locked_until": 0, "requests": [], "display_name": "Disha Patani"},
        }
    }

# ==============================================================================
# S3: STREAMLIT SESSION STATE INITIALIZATION
# ==============================================================================
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'data' not in st.session_state: st.session_state.data = get_initial_mock_data()
if 'logged_in_user' not in st.session_state: st.session_state.logged_in_user = None
if 'current_page' not in st.session_state: st.session_state.current_page = '🏠 Dashboard'

# ==============================================================================
# S4: DATA MODEL FACTORY FUNCTIONS
# ==============================================================================

def create_transaction_record(txn_type, amount, note, category, counterparty):
    """Factory function to create a standardized transaction dictionary."""
    return {"id": f"txn_{int(time.time() * 1000)}", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "type": txn_type, "amount": round(float(amount), 2), "note": str(note).strip(), "category": category, "counterparty": counterparty}

def create_payment_request_record(requester, amount, note):
    """Factory function to create a standardized payment request dictionary."""
    return {"id": f"req_{int(time.time() * 1000)}", "requester": requester, "amount": round(float(amount), 2), "note": str(note).strip(), "status": "pending", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

# ==============================================================================
# S5: UI STYLING & FORMATTING HELPERS
# ==============================================================================

def inject_custom_css_black_theme():
    """Injects custom CSS for the sleek, modern black theme."""
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            html, body, [class*="st-"] { font-family: 'Inter', sans-serif; color: #E0E0E0; }
            body { background-color: #0E1117; }
            .stApp { background-color: #0E1117; }
            h1, h2, h3 { color: #FFFFFF; font-weight: 600; }
            .login-container { background-color: #161B22; padding: 2rem 3rem; border-radius: 20px; border: 1px solid #30363D; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3); }
            .main .block-container { padding-top: 2rem; }
            .st-emotion-cache-16txtl3 { background-color: #161B22; border-right: 1px solid #30363D; }
            .stButton>button { border-radius: 10px; border: 1px solid #0d6efd; color: #0d6efd; background-color: transparent; transition: all 0.2s ease-in-out; font-weight: 500; }
            .stButton>button:hover { background-color: #0d6efd; color: #FFFFFF; border-color: #0d6efd; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0, 123, 255, 0.2); }
            .stButton>button:active { transform: translateY(0px); }
            .stButton>button[kind="primary"] { background-color: #0d6efd; color: white; }
            .st-emotion-cache-1r6slb0, .st-expander { border-radius: 15px; border: 1px solid #30363D; background-color: #161B22; }
            .stTextInput>div>div>input, .stNumberInput>div>div>input, .stTextArea>div>div>textarea { background-color: #0E1117; border-color: #30363D; color: #E0E0E0; }
            .st-emotion-cache-1g8sf3p { color: #8B949E !important; font-weight: 500; }
            .st-emotion-cache-1wivapv { font-size: 2.25rem !important; font-weight: 700; color: #FFFFFF !important; }
        </style>
    """, unsafe_allow_html=True)

def format_currency_with_color(amount, transaction_type):
    """Formats transaction amounts with high-contrast colors for the dark theme."""
    if transaction_type.endswith('_in') or transaction_type == 'deposit': return f"<span style='color:#28a745; font-weight:500;'>+ ₹{amount:,.2f}</span>"
    elif transaction_type.endswith('_out') or transaction_type == 'withdraw': return f"<span style='color:#dc3545; font-weight:500;'>- ₹{amount:,.2f}</span>"
    return f"₹{amount:,.2f}"

def display_high_value_warning(amount):
    """Displays a prominent warning for high-value transactions."""
    if amount >= HIGH_VALUE_TRANSACTION_THRESHOLD:
        st.warning(f"⚠️ **High-Value Transaction:** You are initiating a transaction for ₹{amount:,.2f}. Please verify all details before proceeding.", icon="❗")

# ==============================================================================
# S6: PAGE RENDERING & UI STRUCTURE
# ==============================================================================

def render_login_page():
    """Renders the visually appealing and secure login page."""
    inject_custom_css_black_theme()
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    col_img, col_form = st.columns([1, 2])
    with col_img: st.image("https://i.imgur.com/7b2zG9E.png", width=200)
    with col_form:
        st.title("Secure Wallet Login"); st.markdown("Enter your credentials to access your Gemini UPI Wallet.")
        if st.session_state.logged_in_user: st.session_state.page = 'dashboard'; st.rerun()
        with st.form("login_form"):
            username = st.text_input("Username", key="login_user", placeholder="e.g., alice").lower()
            pin = st.text_input("4-Digit PIN", type="password", key="login_pin", max_chars=4)
            if st.form_submit_button("Login", use_container_width=True, type="primary"): handle_login_attempt(username, pin)
    st.markdown("</div><br>", unsafe_allow_html=True)
    if st.button("Create a New Account", use_container_width=True): st.session_state.page = 'create_account'; st.rerun()

def render_create_account_page():
    """Renders the new user registration page."""
    inject_custom_css_black_theme()
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.title("Create Your Gemini Wallet"); st.markdown("Join the most intuitive digital payment platform.")
    with st.form("create_account_form"):
        display_name = st.text_input("Full Name", placeholder="e.g., Alice Wonderland")
        username = st.text_input("Choose a Username", placeholder="e.g., alice").lower()
        pin1 = st.text_input("Create a 4-Digit PIN", type="password", max_chars=4)
        pin2 = st.text_input("Confirm your PIN", type="password", max_chars=4)
        initial_amount = st.number_input("Initial Deposit Amount (₹)", min_value=0.0, step=100.0, format="%.2f")
        if st.form_submit_button("Create My Account", use_container_width=True, type="primary"): handle_account_creation(username, display_name, pin1, pin2, initial_amount)
    if st.button("Back to Login", use_container_width=True): st.session_state.page = 'login'; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def render_main_app():
    """The main application interface, acting as a router to different pages."""
    inject_custom_css_black_theme()
    user, user_data = st.session_state.logged_in_user, st.session_state.data["accounts"][st.session_state.logged_in_user]
    with st.sidebar: render_sidebar_navigation(user, user_data)
    
    page_to_render = st.session_state.get('current_page', '🏠 Dashboard')
    page_router = {
        '🏠 Dashboard': render_dashboard_content,
        '💰 Add Money (Deposit)': render_deposit_page,
        '🏧 Withdraw Money': render_withdraw_page,
        '💸 Transfer Money': render_transfer_page,
        '📲 Generate QR': render_qr_generate_page,
        '📱 Pay via QR': render_qr_pay_page,
        '📜 Transaction History': render_history_page,
        '📊 Spend by Category': render_category_report_page,
        '🗓️ Monthly Summary': render_monthly_report_page,
        '👥 Top Payees': render_top_payees_report_page,
        '⚙️ Change PIN': render_settings_page,
    }
    page_router[page_to_render](user, user_data)

def render_sidebar_navigation(user, user_data):
    """Renders the sidebar with all 11 functionalities listed explicitly."""
    st.image("https://i.imgur.com/7b2zG9E.png", width=80)
    st.header(f"Hi, {user_data['display_name'].split()[0]}")
    # FR-004: Show Balance is fulfilled here, always visible
    st.metric(label="Available Balance", value=f"₹{user_data['balance']:,.2f}")
    st.markdown("---")
    
    # All 11 options are now listed directly
    menu_options = [
        '🏠 Dashboard',
        '💰 Add Money (Deposit)',
        '🏧 Withdraw Money',
        '💸 Transfer Money',
        '📲 Generate QR',
        '📱 Pay via QR',
        '📜 Transaction History',
        '📊 Spend by Category',
        '🗓️ Monthly Summary',
        '👥 Top Payees',
        '⚙️ Change PIN'
    ]
    
    for option in menu_options:
        if st.button(option, use_container_width=True, key=f"nav_{option}"):
            st.session_state.current_page = option
            st.rerun()

    st.markdown("---")
    if st.button("Logout", use_container_width=True): handle_logout()

# ------------------------------------------------------------------------------
# 6.3: Individual Page Content Renderers
# ------------------------------------------------------------------------------
def render_dashboard_content(user, user_data):
    """Renders the main dashboard view with pending actions and recent activity."""
    st.title("🏠 Dashboard"); st.markdown("An overview of your account activity and pending actions.")
    st.subheader("Action Required: Pending Requests")
    pending_requests = [req for req in user_data.get("requests", []) if req["status"] == "pending"]
    if not pending_requests: st.info("You have no pending payment requests. All clear!", icon="✅")
    else:
        for req in pending_requests:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1.2])
                with col1:
                    st.write(f"**From:** {st.session_state.data['accounts'][req['requester']]['display_name']} (@{req['requester']})")
                    st.write(f"**Amount:** ₹{req['amount']:,.2f}"); st.caption(f"**Note:** '{req['note']}' | **Received:** {req['timestamp']}")
                with col2:
                    if st.button("Approve & Pay", key=f"pay_{req['id']}", use_container_width=True, type="primary"): handle_payment_request(user, req, "approved")
                    if st.button("Decline", key=f"dec_{req['id']}", use_container_width=True): handle_payment_request(user, req, "declined")
    st.subheader("Recent Activity")
    transactions = user_data["transactions"]
    if not transactions: st.info("Your transaction history is empty.", icon="📜")
    else:
        df = pd.DataFrame(sorted(transactions, key=lambda x: x["timestamp"], reverse=True)[:5])
        df['Amount'] = df.apply(lambda row: format_currency_with_color(row['amount'], row['type']), axis=1)
        st.markdown(df[['timestamp', 'type', 'Amount', 'counterparty', 'note']].to_html(escape=False, index=False), unsafe_allow_html=True)

def render_deposit_page(user, user_data):
    st.title("💰 Add Money (Deposit)")
    with st.form("deposit_form", clear_on_submit=True):
        st.subheader("Deposit Funds into Your Wallet")
        amount = st.number_input("Amount to Deposit (₹)", min_value=1.0, step=50.0, format="%.2f", key="d_amt")
        note = st.text_input("Source (Optional)", key="d_note", placeholder="e.g., Bank Transfer")
        if st.form_submit_button("Deposit Funds", use_container_width=True, type="primary"): handle_deposit(user, amount, note)

def render_withdraw_page(user, user_data):
    st.title("🏧 Withdraw Money")
    with st.form("withdraw_form", clear_on_submit=True):
        st.subheader("Withdraw Funds from Your Wallet")
        amount = st.number_input("Amount to Withdraw (₹)", min_value=1.0, step=50.0, format="%.2f", key="w_amt")
        category = st.selectbox("Withdrawal Category", CATEGORIES, key="w_cat")
        pin = st.text_input("PIN to confirm withdrawal", type="password", key="w_pin", max_chars=4)
        display_high_value_warning(amount)
        if st.form_submit_button("Withdraw Funds", use_container_width=True, type="primary"): handle_withdrawal(user, amount, category, pin)

def render_transfer_page(user, user_data):
    st.title("💸 Transfer Money")
    with st.form("transfer_form"):
        st.subheader("Send Money to Another User")
        all_users = st.session_state.data["accounts"]
        receiver_options = {u: f"{all_users[u]['display_name']} (@{u})" for u in all_users if u != user}
        receiver_username = st.selectbox("Select Recipient", options=list(receiver_options.keys()), format_func=lambda u: receiver_options[u])
        amount = st.number_input("Amount (₹)", min_value=0.01, step=10.0, format="%.2f")
        note = st.text_input("Note for recipient (Optional)", max_chars=100)
        category = st.selectbox("Categorize this expense", CATEGORIES)
        display_high_value_warning(amount)
        pin = st.text_input("Enter your 4-digit PIN to confirm", type="password", max_chars=4)
        if st.form_submit_button("Send Money Securely", use_container_width=True, type="primary"): handle_transfer(user, receiver_username, amount, note, category, pin)

def render_qr_generate_page(user, user_data):
    st.title("📲 Generate QR Code")
    with st.form("qr_generate_form"):
        st.subheader("Generate QR to Receive Payment")
        amount = st.number_input("Amount to Request (₹)", min_value=0.01, step=10.0, format="%.2f")
        note = st.text_input("Note for Payer (Optional)")
        if st.form_submit_button("Generate QR Code", use_container_width=True, type="primary"): handle_qr_generation(user, amount, note)

def render_qr_pay_page(user, user_data):
    st.title("📱 Pay via QR")
    with st.form("qr_pay_form"):
        st.subheader("Pay Using a QR Payload")
        payload_str = st.text_area("Paste the QR JSON payload here")
        category = st.selectbox("Categorize this payment", CATEGORIES, key="qr_pay_cat")
        pin = st.text_input("Your PIN to Confirm Payment", type="password", max_chars=4)
        if st.form_submit_button("Make Payment", use_container_width=True, type="primary"): handle_qr_payment(user, payload_str, category, pin)

def render_history_page(user, user_data):
    st.title("📜 Transaction History")
    st.subheader("Your Full Transaction History")
    transactions = user_data["transactions"]
    if not transactions: st.info("No transactions to display.", icon="📜")
    else:
        df = pd.DataFrame(sorted(transactions, key=lambda x: x["timestamp"], reverse=True))
        df['Amount'] = df.apply(lambda row: format_currency_with_color(row['amount'], row['type']), axis=1)
        st.markdown(df[['timestamp', 'type', 'Amount', 'counterparty', 'note', 'category']].fillna('-').to_html(escape=False, index=False), unsafe_allow_html=True)

def render_category_report_page(user, user_data):
    st.title("📊 Spend by Category")
    st.subheader("Spending Breakdown by Category")
    spend = defaultdict(float)
    for txn in user_data["transactions"]:
        if txn["type"] in {"transfer_out", "qr_out", "withdraw"} and txn.get("category"): spend[txn["category"]] += txn["amount"]
    if not spend: st.info("No categorized spending data available.", icon="💡")
    else:
        spend_df = pd.DataFrame(list(spend.items()), columns=['Category', 'Amount (₹)']).set_index('Category')
        st.bar_chart(spend_df, color="#0d6efd"); st.table(spend_df.style.format("₹{:,.2f}"))

def render_monthly_report_page(user, user_data):
    st.title("🗓️ Monthly Summary")
    st.subheader("Monthly Inflow vs. Outflow")
    summary = defaultdict(lambda: {"Inflow (₹)": 0.0, "Outflow (₹)": 0.0})
    for txn in user_data["transactions"]:
        month = txn["timestamp"][:7]
        if txn["type"] in {"deposit", "transfer_in", "qr_in"}: summary[month]["Inflow (₹)"] += txn["amount"]
        elif txn["type"] in {"withdraw", "transfer_out", "qr_out"}: summary[month]["Outflow (₹)"] += txn["amount"]
    if not summary: st.info("No transaction data to summarize.", icon="🗓️")
    else:
        df = pd.DataFrame.from_dict(summary, orient='index').sort_index(ascending=False)
        st.table(df.style.format("₹{:,.2f}"))

def render_top_payees_report_page(user, user_data):
    st.title("👥 Top Payees")
    st.subheader("Top Payees by Amount Transferred")
    payees = defaultdict(lambda: {"Payments": 0, "Total Amount (₹)": 0.0})
    for txn in user_data["transactions"]:
        if txn["type"] in {"transfer_out", "qr_out"}:
            payee_name = st.session_state.data['accounts'][txn['counterparty']]['display_name']
            payees[payee_name]["Payments"] += 1; payees[payee_name]["Total Amount (₹)"] += txn["amount"]
    if not payees: st.info("You haven't made any payments to other users yet.", icon="👥")
    else:
        df = pd.DataFrame.from_dict(payees, orient='index').sort_values(by="Total Amount (₹)", ascending=False)
        df.index.name = "Payee"; st.table(df.style.format({"Total Amount (₹)": "₹{:,.2f}", "Payments": "{:}"}))

def render_settings_page(user, user_data):
    st.title("⚙️ Change PIN")
    st.subheader("Manage your account security.")
    with st.form("change_pin_form"):
        st.write("For your security, please enter your current and new PIN.")
        old_pin = st.text_input("Current 4-Digit PIN", type="password", max_chars=4)
        new_pin1 = st.text_input("New 4-Digit PIN", type="password", max_chars=4)
        new_pin2 = st.text_input("Confirm New PIN", type="password", max_chars=4)
        if st.form_submit_button("Update My PIN", use_container_width=True, type="primary"): handle_pin_change(user, old_pin, new_pin1, new_pin2)

# ==============================================================================
# S7: BACKEND LOGIC HANDLERS
# ==============================================================================
# The backend logic handlers (e.g., handle_login_attempt, handle_transfer) are largely unchanged
# from the previous version as their core functionality is correct. They are called by the new
# render functions. I am including them here for completeness.

def handle_login_attempt(username, pin):
    accounts = st.session_state.data["accounts"]
    if username in accounts:
        user_acc = accounts[username]
        if time.time() < user_acc.get("locked_until", 0):
            st.error(f"🔒 Account locked. Try again in {int(user_acc['locked_until'] - time.time())}s.")
        elif user_acc["pin"] == pin:
            user_acc["failed_attempts"] = 0; st.session_state.logged_in_user = username
            st.session_state.page = 'dashboard'; st.rerun()
        else:
            user_acc["failed_attempts"] += 1
            if user_acc["failed_attempts"] >= MAX_LOGIN_ATTEMPTS:
                user_acc["locked_until"] = time.time() + LOCKOUT_DURATION_SECONDS
                st.error(f"❌ Account locked for {LOCKOUT_DURATION_SECONDS} seconds.")
            else:
                st.error(f"❌ Incorrect PIN. {MAX_LOGIN_ATTEMPTS - user_acc['failed_attempts']} attempts remaining.")
    else:
        st.error("❌ Username not found.")

def handle_account_creation(username, display_name, pin1, pin2, initial_amount):
    accounts = st.session_state.data["accounts"]
    if not username or not display_name: st.error("Username and Full Name are required.")
    elif username in accounts: st.error("This username is already taken.")
    elif len(pin1) != 4 or not pin1.isdigit(): st.error("PIN must be 4 digits.")
    elif pin1 != pin2: st.error("PINs do not match.")
    else:
        accounts[username] = {"pin": pin1, "balance": initial_amount, "display_name": display_name, "transactions": [create_transaction_record("deposit", initial_amount, "Initial deposit", None, "self")], "failed_attempts": 0, "locked_until": 0, "requests": []}
        st.success(f"✅ Welcome, {display_name}! Account created."); st.balloons(); time.sleep(2)
        st.session_state.page = 'login'; st.rerun()

def handle_transfer(sender, receiver, amount, note, category, pin):
    user_data = st.session_state.data["accounts"][sender]
    if pin == user_data["pin"]:
        if amount > user_data["balance"]: st.error("Insufficient funds.")
        else:
            user_data["balance"] -= amount
            st.session_state.data["accounts"][receiver]["balance"] += amount
            user_data["transactions"].append(create_transaction_record("transfer_out", amount, note, category, receiver))
            st.session_state.data["accounts"][receiver]["transactions"].append(create_transaction_record("transfer_in", amount, note, None, sender))
            st.success(f"Sent ₹{amount:,.2f} to {st.session_state.data['accounts'][receiver]['display_name']}!"); st.balloons()
    else: st.error("Incorrect PIN.")

def handle_qr_generation(user, amount, note):
    payload = json.dumps({"payee": user, "amount": amount, "note": note})
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(payload); qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    buf = io.BytesIO()
    img.save(buf, "PNG")
    st.image(buf.getvalue(), caption="Scan this QR or copy the payload", width=250)
    st.code(payload, language="json")

def handle_qr_payment(payer, payload_str, category, pin):
    user_data = st.session_state.data["accounts"][payer]
    try:
        payload = json.loads(payload_str)
        payee, amount, note = payload.get("payee"), float(payload.get("amount",0)), payload.get("note","")
        if not all([payee, amount > 0]): st.error("Invalid QR payload.")
        elif payee == payer: st.error("You cannot pay yourself.")
        elif amount > user_data["balance"]: st.error("Insufficient funds.")
        elif pin != user_data["pin"]: st.error("Incorrect PIN.")
        else:
            user_data["balance"] -= amount
            st.session_state.data["accounts"][payee]["balance"] += amount
            user_data["transactions"].append(create_transaction_record("qr_out", amount, note, category, payee))
            st.session_state.data["accounts"][payee]["transactions"].append(create_transaction_record("qr_in", amount, note, None, payer))
            st.success(f"Paid ₹{amount:,.2f} to {st.session_state.data['accounts'][payee]['display_name']}!"); st.balloons()
    except (json.JSONDecodeError, ValueError): st.error("Invalid QR format.")

def handle_bill_split(requester, total_amount, note, users_to_split):
    if not users_to_split: st.warning("Please select at least one user."); return
    num_people = len(users_to_split) + 1
    split_amount = round(total_amount / num_people, 2)
    for other_user in users_to_split:
        request = create_payment_request_record(requester, split_amount, note)
        st.session_state.data["accounts"][other_user]["requests"].append(request)
    st.success(f"Sent payment requests of ₹{split_amount:,.2f} to {len(users_to_split)} user(s).")

def handle_deposit(user, amount, note):
    user_data = st.session_state.data["accounts"][user]
    user_data["balance"] += amount
    user_data["transactions"].append(create_transaction_record("deposit", amount, note or "Self Deposit", None, "self"))
    st.success(f"₹{amount:,.2f} deposited successfully.")
    
def handle_withdrawal(user, amount, category, pin):
    user_data = st.session_state.data["accounts"][user]
    if pin == user_data["pin"]:
        if amount > user_data["balance"]: st.error("Insufficient balance.")
        else:
            user_data["balance"] -= amount
            user_data["transactions"].append(create_transaction_record("withdraw", amount, "Cash withdrawal", category, "cash"))
            st.success(f"₹{amount:,.2f} has been withdrawn.")
    else: st.error("Incorrect PIN.")

def handle_pin_change(user, old_pin, new_pin1, new_pin2):
    user_data = st.session_state.data["accounts"][user]
    if old_pin != user_data["pin"]: st.error("Current PIN is incorrect.")
    elif len(new_pin1) != 4 or not new_pin1.isdigit(): st.error("New PIN must be 4 digits.")
    elif new_pin1 != new_pin2: st.error("New PINs do not match.")
    else: user_data["pin"] = new_pin1; st.success("✅ PIN changed successfully!")

def handle_payment_request(payer_username, request, new_status):
    payer_data, req_username = st.session_state.data["accounts"][payer_username], request['requester']
    requester_data = st.session_state.data["accounts"][req_username]
    if new_status == "approved":
        amount = request["amount"]
        if payer_data["balance"] >= amount:
            payer_data["balance"] -= amount; requester_data["balance"] += amount
            note = f"Payment for: {request['note']}"
            payer_data["transactions"].append(create_transaction_record("transfer_out", amount, note, "Bills", req_username))
            requester_data["transactions"].append(create_transaction_record("transfer_in", amount, note, None, payer_username))
            st.success("Payment successful!")
        else: st.error("Insufficient funds."); return
    for r in payer_data["requests"]:
        if r["id"] == request["id"]: r["status"] = new_status; break
    st.rerun()

def handle_logout():
    """Clears session state to log the user out securely."""
    st.session_state.logged_in_user = None; st.session_state.page = 'login'
    st.session_state.current_page = '🏠 Dashboard'; st.rerun()

# ==============================================================================
# S8: MAIN APPLICATION ROUTER
# ==============================================================================
def main():
    """The main router for the application."""
    if st.session_state.page == 'login': render_login_page()
    elif st.session_state.page == 'create_account': render_create_account_page()
    elif st.session_state.page == 'dashboard': render_main_app()

if __name__ == "__main__":
    main()
