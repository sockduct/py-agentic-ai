import streamlit as st
from httpx import HTTPStatusError, RequestError

from expenses_ai_agent.streamlit.api_client import ExpenseAPIClient


# streamlit/views/add_expense.py
def render(api_client: ExpenseAPIClient, user_id: int) -> None:
    st.header("Add Expense")
    # Handle form...
    with st.form(key="add_expense_form", clear_on_submit=True):
        description = st.text_input("Expense Description")
        if _ := st.form_submit_button("Submit"):
            description = description.strip()
            if not description:
                st.warning("Expense description cannot be empty or whitespace")
                return
            try:
                with st.spinner(text="Classifying expense...", show_time=True):
                    expense = api_client.classify_expense(
                        description=description, user_id=user_id
                    )
            except HTTPStatusError as err:
                if err.response.status_code == 404:
                    st.warning("No expenses found. Add some expenses first!")
                else:
                    st.error(f"API error: {err.response.status_code}")
            except RequestError:
                st.error("Cannot connect to API. Is the backend running?")

            else:
                if expense:
                    st.success(f'Expense classified as "{expense["category"]}"')
                    amt_col, cat_col, conf_col = st.columns(3)
                    amt_col.metric(
                        label="Total Amount", value=float(expense["total_amount"])
                    )
                    cat_col.metric(label="Category", value=str(expense["category"]))
                    conf_col.metric(
                        label="Confidence",
                        value=float(expense["confidence"] * 100),
                    )

                    if comments := expense.get("comments"):
                        st.info(comments)
                else:
                    st.warning("No expense classified. Try again.")
