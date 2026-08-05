import plotly.express as px
import streamlit as st
from httpx import HTTPStatusError, RequestError

from expenses_ai_agent.streamlit.api_client import ExpenseAPIClient


def render(api_client: ExpenseAPIClient, user_id: int) -> None:
    """Render the dashboard view"""
    st.header("Dashboard")
    try:
        summary = api_client.get_summary(user_id)
    except HTTPStatusError as err:
        if err.response.status_code == 404:
            st.warning("No expenses found. Add some expenses first!")
        else:
            st.error(f"API error: {err.response.status_code}")
    except RequestError:
        st.error("Cannot connect to API. Is the backend running?")
    else:
        # Display charts...
        # Pie chart for category breakdown
        if category_totals := summary["category_totals"]:  # {"Food": "100.00", ...}
            fig = px.pie(
                names=list(category_totals.keys()),
                values=[float(v) for v in category_totals.values()],
                title="Spending by Category",
            )
            # Per tests, use_contrainer_width deprecated, replace True outcome
            # with width='stretch':
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No expenses found. Add some expenses first!")

        # Bar chart for monthly totals
        if monthly_totals := summary["monthly_totals"]:  # {"2024-01": "150.00", ...}
            fig = px.bar(
                x=list(monthly_totals.keys()),
                y=[float(v) for v in monthly_totals.values()],
                labels={"x": "Month", "y": "Total"},
                title="Monthly Spending",
            )
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No expenses found. Add some expenses first!")
