"""
Build dashboard.py with a render(client, user_id: int) function that fetches
client.get_summary(user_id) and renders two Plotly charts:
* Call st.header("Dashboard") first, before the try block
* Pie chart of summary["category_totals"] — px.pie(names=..., values=[float(v) for v in ...])
* Bar chart of summary["monthly_totals"] — px.bar(x=..., y=[float(v) for v in ...])
* Show st.info(...) for each chart section when the data dict is empty
* Wrap in try/except with separate handlers:
  except HTTPStatusError as e should include the status code (e.g. e.response.status_code)
  in the message
  except RequestError should say "Cannot connect..." — the tests assert on these substrings

Note: Decimal values come back from the API as strings, so convert with float(v) before
passing to Plotly
"""

import plotly.express as px
import streamlit as st
from httpx import HTTPStatusError, RequestError

from expenses_ai_agent.streamlit.api_client import ExpenseAPIClient


def render(api_client: ExpenseAPIClient, user_id: int) -> None:
    """Render the dashboard view"""
    st.header("Dashboard")
    try:
        summary = api_client.get_summary(user_id)
        category_totals = summary["category_totals"]  # {"Food": "100.00", ...}
        monthly_totals = summary["monthly_totals"]  # {"2024-01": "150.00", ...}
        # Display charts...
        # Pie chart for category breakdown
        if category_totals:
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
        if monthly_totals:
            fig = px.bar(
                x=list(monthly_totals.keys()),
                y=[float(v) for v in monthly_totals.values()],
                labels={"x": "Month", "y": "Total"},
                title="Monthly Spending",
            )
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No expenses found. Add some expenses first!")
    except HTTPStatusError as err:
        if err.response.status_code == 404:
            st.warning("No expenses found. Add some expenses first!")
        else:
            st.error(f"API error: {err.response.status_code}")
    except RequestError:
        st.error("Cannot connect to API. Is the backend running?")
