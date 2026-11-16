import plotly.express as px
import streamlit as st
from data import load_flows

st.title("Transfers")

# Daily flows from MongoDB, prepared in the notebook
df = load_flows()

# Direction names in the database are seen from Norway
DIRECTION_LABELS = {"import": "Into Norway", "export": "Out of Norway"}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

left, right = st.columns(2)

with left:
    connection = st.radio("Connection", sorted(df["connection"].unique()))
    year = st.selectbox("Year", sorted(df["date"].dt.year.unique()))

    year_df = df[(df["connection"] == connection) & (df["date"].dt.year == year)]
    totals = year_df.groupby("direction")["gwh"].sum().reset_index()
    totals["direction"] = totals["direction"].map(DIRECTION_LABELS)

    if totals["gwh"].sum() == 0:
        st.info("No flow data for this connection and year.")
    else:
        # Pie of the total amount in and out of Norway for the chosen connection and year
        # color= makes Plotly express use the theme colours for the two directions
        fig = px.pie(totals, names="direction", values="gwh", color="direction", title=f"{connection}, {year}")
        fig.update_traces(texttemplate="%{value:,.0f} GWh<br>%{percent}")
        st.plotly_chart(fig)

with right:
    chosen_months = st.pills("Months", MONTHS, selection_mode="multi", default=["Jan"])

    if not chosen_months:
        st.info("Choose at least one month.")
    else:
        month_numbers = [MONTHS.index(m) + 1 for m in chosen_months]
        month_df = year_df[year_df["date"].dt.month.isin(month_numbers)]

        # One column per direction. asfreq("D") adds empty days between months that are not chosen,
        # so the line has a gap there instead of a straight line across
        wide = month_df.pivot(index="date", columns="direction", values="gwh").asfreq("D")
        wide = wide.rename(columns=DIRECTION_LABELS)

        fig = px.line(wide, title=f"{connection}, {year}")
        fig.update_xaxes(title="Date")
        fig.update_yaxes(title="GWh per day")
        fig.update_layout(legend_title_text="Direction")
        st.plotly_chart(fig)

with st.expander("Data source"):
    st.write(
        "Physical cross-border flows from the ENTSO-E Transparency Platform "
        "(Cross-Border Physical Flow [12.1.G], document type A11), for 2024 and 2025. "
        "The flows are given per bidding zone border, as average MW per hour or 15 minutes. "
        "In the notebook they were stored in Cassandra, summed to GWh per day with Spark "
        "and inserted into MongoDB (database ind320, collection flows_daily), which this page reads from. "
        "Times are in UTC."
    )
