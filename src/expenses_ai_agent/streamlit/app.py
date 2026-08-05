from typing import cast

import streamlit as st
from decouple import config

from expenses_ai_agent.streamlit.api_client import ExpenseAPIClient
from expenses_ai_agent.streamlit.views import add_expense, dashboard, expenses

API_URL = cast(str, config("API_URL", default="http://localhost:8000/api/v1", cast=str))


def main() -> None:
    st.set_page_config(page_title="Expense Tracker", layout="wide")

    client = ExpenseAPIClient(base_url=API_URL)
    default_user_id = config("USER_ID", default=12345, cast=int)

    if "user_id" not in st.session_state:
        st.session_state["user_id"] = default_user_id

    user_id = st.session_state["user_id"]

    with st.sidebar:
        st.title("Expense Tracker")
        user_id_input = st.text_input(
            "User ID",
            value=user_id,
            key="sidebar_user_id",
        )
        if user_id_input and user_id_input.strip().isdigit():
            user_id = int(user_id_input)
            st.session_state["user_id"] = user_id

        page = st.radio(
            "Navigate",
            ["Dashboard", "Expenses", "Add Expense"],
        )

    if page == "Dashboard":
        dashboard.render(client, user_id)
    elif page == "Expenses":
        expenses.render(client, user_id)
    elif page == "Add Expense":
        add_expense.render(client, user_id)


main()
