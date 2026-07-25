import streamlit as st

from expenses_ai_agent.streamlit.api_client import ExpenseAPIClient
from expenses_ai_agent.streamlit.views import add_expense, dashboard, expenses

st.set_page_config(page_title="Expense Tracker", layout="wide")

client = ExpenseAPIClient(base_url="http://localhost:8000/api/v1")

with st.sidebar:
    st.title("Expense Tracker")
    user_id_input = st.text_input("User ID", value="12345", key="sidebar_user_id")
    user_id = int(user_id_input) if user_id_input.strip().isdigit() else None
    page = st.radio("Navigate", ["Dashboard", "Expenses", "Add Expense"])

if page == "Dashboard":
    dashboard.render(client, user_id)
elif page == "Expenses":
    expenses.render(client, user_id)
elif page == "Add Expense":
    add_expense.render(client, user_id)
