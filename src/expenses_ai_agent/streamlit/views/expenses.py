"""
Build expenses.py with a render(client, user_id: int) function that fetches
client.get_expenses(user_id) and renders a row per expense using st.columns:
* Call st.header("Expenses") first, before the try block
* Left column: category, amount, currency, description
* Right column: st.button("Delete", key=f"del_{item['id']}") that calls
  client.delete_expense(item["id"]) then st.rerun() to refresh the list
* Show st.info(...) when the list is empty
* Wrap in try/except RequestError and include "Cannot connect" in the
  st.error(...) message — the test asserts on that substring
* uv run pytest tests/unit/test_week5_streamlit_views.py::TestExpensesView (5 tests)
"""

import streamlit as st
from httpx import HTTPStatusError, RequestError

from expenses_ai_agent.streamlit.api_client import ExpenseAPIClient


# streamlit/views/expenses.py
def render(api_client: ExpenseAPIClient, user_id: int) -> None:
    st.header("Expenses")
    try:
        if expenses := api_client.get_expenses(user_id):
            # Display table...
            cat_col, amt_col, curr_col, desc_col, del_col = st.columns(5)
            for expense in expenses:
                with cat_col:
                    st.header("Expense")
                    st.write(expense["category"])
                with amt_col:
                    st.header("Amount")
                    st.write(expense["amount"])
                with curr_col:
                    st.header("Currency")
                    st.write(expense["currency"])
                with desc_col:
                    st.header("Description")
                    st.write(expense["description"])
                with del_col:
                    st.header("Delete")
                    if st.button(
                        "Delete",
                        key=f"del_{expense['id']}",
                        on_click=api_client.delete_expense,
                        args=[expense["id"]],
                    ):
                        st.rerun()
        else:
            st.info("No expenses found. Add some expenses first!")
    except HTTPStatusError as err:
        if err.response.status_code == 404:
            st.warning("No expenses found. Add some expenses first!")
        else:
            st.error(f"API error: {err.response.status_code}")
    except RequestError:
        st.error("Cannot connect to API. Is the backend running?")
