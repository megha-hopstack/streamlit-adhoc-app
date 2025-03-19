import streamlit as st
import datetime
from vault_albader_io import generate_outbound_report, generate_inbound_report

st.title("ALBADER (JMI Client) Warehouse Report")
st.write("Generate IN/OUT reports with lot for the warehouse by selecting the desired date range.")

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", value=datetime.date(2025, 1, 30))
with col2:
    end_date = st.date_input("End Date", value=datetime.date(2025, 2, 19))

# Check if report data is already in session_state
if "reports_generated" not in st.session_state:
    st.session_state.reports_generated = False

if start_date and end_date:
    if start_date > end_date:
        st.error("Start date must be before end date.")
    else:
        if st.button("Generate Report") or st.session_state.reports_generated:
            # If the reports haven't been generated yet, generate them and store in session_state
            if not st.session_state.reports_generated:
                start_dt = datetime.datetime.combine(start_date, datetime.time.min)
                end_dt = datetime.datetime.combine(end_date, datetime.time.min)

                with st.spinner("Generating outbound report..."):
                    outbound_bytes, outbound_df = generate_outbound_report(start_dt, end_dt)
                with st.spinner("Generating inbound report..."):
                    inbound_bytes, inbound_df = generate_inbound_report(start_dt, end_dt)

                st.session_state.outbound_bytes = outbound_bytes
                st.session_state.outbound_df = outbound_df
                st.session_state.inbound_bytes = inbound_bytes
                st.session_state.inbound_df = inbound_df
                st.session_state.reports_generated = True

            st.success("Reports generated successfully!")

            # Download buttons using data from session_state
            st.download_button(
                label="Download Outbound Report",
                data=st.session_state.outbound_bytes,
                file_name="vault-outbound.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.download_button(
                label="Download Inbound Report",
                data=st.session_state.inbound_bytes,
                file_name="vault-inbound.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # Optionally display a preview of the DataFrames
            st.subheader("Outbound Report Preview")
            st.dataframe(st.session_state.outbound_df)
            st.subheader("Inbound Report Preview")
            st.dataframe(st.session_state.inbound_df)
