import matplotlib.pyplot as plt
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
    totals = year_df.groupby("direction")["gwh"].sum()

    if totals.sum() == 0:
        st.info("No flow data for this connection and year.")
    else:
        # Pie of the total amount in and out of Norway for the chosen connection and year
        fig, ax = plt.subplots()
        ax.pie(
            totals,
            labels=[f"{DIRECTION_LABELS[d]}\n{v:,.0f} GWh" for d, v in totals.items()],
            autopct="%1.0f%%",
        )
        ax.set_title(f"{connection}, {year}")
        st.pyplot(fig)

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

        fig, ax = plt.subplots()
        for direction in wide.columns:
            ax.plot(wide.index, wide[direction], label=DIRECTION_LABELS[direction])
        ax.set_xlabel("Date")
        ax.set_ylabel("GWh per day")
        ax.set_title(f"{connection}, {year}")
        ax.legend()
        fig.autofmt_xdate()
        st.pyplot(fig)

with st.expander("Data source"):
    st.write(
        "Physical cross-border flows from the ENTSO-E Transparency Platform "
        "(Cross-Border Physical Flow [12.1.G], document type A11), for 2024 and 2025. "
        "The flows are given per bidding zone border, as average MW per hour or 15 minutes. "
        "In the notebook they were stored in Cassandra, summed to GWh per day with Spark "
        "and inserted into MongoDB (database ind320, collection flows_daily), which this page reads from. "
        "Times are in UTC."
    )
