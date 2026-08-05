import streamlit as st
from httpx import HTTPStatusError, RequestError

from expenses_ai_agent.streamlit.api_client import ExpenseAPIClient


# streamlit/views/expenses.py
def render(api_client: ExpenseAPIClient, user_id: int) -> None:
    st.header("Expenses")
    try:
        expenses = api_client.get_expenses(user_id)
    except HTTPStatusError as err:
        if err.response.status_code == 404:
            st.warning("No expenses found. Add some expenses first!")
        else:
            st.error(f"API error: {err.response.status_code}")
    except RequestError:
        st.error("Cannot connect to API. Is the backend running?")
    else:
        if expenses:
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
