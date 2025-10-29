import streamlit as st
import pandas as pd
import os
import glob
from datetime import datetime
import plotly.express as px
from io import BytesIO

from utils.detect_format import detect_file_format
from parser.sbi_parser import parse_sbi_pdf
from parser.generic_parser import parse_generic_file
from replicator.sheet_writer import write_to_sheets
from analytics.generate_analysis import generate_fresh_analysis  # ✅ NEW

st.set_page_config(page_title="LedgerLens SyncBot", layout="wide")
st.title("📊 LedgerLens SyncBot")

st.markdown("""
Welcome to **LedgerLens SyncBot** – your intelligent assistant for parsing and visualizing bank statements.

📁 Upload any statement (PDF, CSV, Excel)  
🔍 Auto-detect format and parse transactions  
📊 View monthly breakdowns and trends  
📤 Export cleaned data for analysis

---

👨‍💻 Built by [Deepak Khadka](https://www.linkedin.com/in/deepak-khadka-78869a221) – passionate about data analytics, modular design, and recruiter-ready polish.
""")

# 📁 Upload section
uploaded_file = st.file_uploader("📁 Upload a statement", type=["pdf", "csv", "xlsx"])

if uploaded_file:
    file_bytes = BytesIO(uploaded_file.getbuffer())
    st.success(f"Uploaded: {uploaded_file.name}")

    info = detect_file_format(uploaded_file.name)
    st.write("📄 Detected format:", info)

    try:
        if info['file_type'] == 'pdf':
            df = parse_sbi_pdf(file_bytes)
        elif info['file_type'] in ['csv', 'excel']:
            df = parse_generic_file(file_bytes)
        else:
            st.error("Unsupported file format.")
            st.stop()
    except Exception as e:
        st.error(f"Parsing failed: {e}")
        st.stop()

    # ✅ Normalize and deduplicate
    df["Description"] = df["Description"].astype(str).str.strip().str.lower()
    df["Sender"] = df["Sender"].astype(str).str.strip().str.upper()
    df.drop_duplicates(subset=["Date", "Amount", "Sender", "Reference", "Description"], inplace=True)

    st.subheader("✅ Parsed Transactions")
    st.dataframe(df)

    write_to_sheets(df)
    st.success("Written to master and monthly sheets.")

    # 🧼 Fresh analysis generation
    month_str = df['Date'].dt.strftime('%Y_%m').iloc[0]
    analysis_file = os.path.join("output", f"Analysis_{month_str}.xlsx")
    if os.path.exists(analysis_file):
        os.remove(analysis_file)

    generate_fresh_analysis(df, month_str)
    st.success(f"Monthly analysis complete for {month_str}")

# 📅 Month selector
st.markdown("### 📅 View Past Month")
month_files = sorted(glob.glob("output/Bank_Statement_*.xlsx"), reverse=True)
month_options = [os.path.basename(f).replace("Bank_Statement_", "").replace(".xlsx", "") for f in month_files]
selected_month = st.selectbox("Select a month to view", month_options)

if selected_month:
    month_path = f"output/Bank_Statement_{selected_month}.xlsx"
    try:
        df = pd.read_excel(month_path)

        df["Description"] = df["Description"].astype(str).str.strip().str.lower()
        df["Sender"] = df["Sender"].astype(str).str.strip().str.upper()
        df.drop_duplicates(subset=["Date", "Amount", "Sender", "Reference", "Description"], inplace=True)

        st.subheader(f"📄 Transactions for {selected_month}")
        st.dataframe(df)
    except Exception as e:
        st.error(f"Failed to load month: {e}")
        st.stop()

    # 🔄 Manual Analysis Trigger
    if st.button(f"🔄 Run Fresh Analysis for {selected_month}"):
        try:
            analysis_file = os.path.join("output", f"Analysis_{selected_month}.xlsx")
            if os.path.exists(analysis_file):
                os.remove(analysis_file)
            generate_fresh_analysis(df, selected_month)
            st.success(f"✅ Fresh analysis generated for {selected_month}")
        except Exception as e:
            st.error(f"Failed to generate analysis: {e}")

    # 🔍 Filters
    st.markdown("### 🔍 Filter Transactions")
    senders = sorted(df['Sender'].dropna().unique())
    selected_sender = st.selectbox("Filter by Sender", ["All"] + senders)
    txn_types = ["All", "CR", "DR"]
    selected_type = st.selectbox("Filter by Type", txn_types)
    keyword = st.text_input("Search by keyword (e.g., UPI, ATM, Newtonda)")

    filtered_df = df.copy()
    if selected_sender != "All":
        filtered_df = filtered_df[filtered_df['Sender'] == selected_sender]
    if selected_type != "All":
        filtered_df = filtered_df[filtered_df['Type'] == selected_type]
    if keyword:
        filtered_df = filtered_df[filtered_df['Description'].str.contains(keyword, case=False, na=False)]

    st.subheader("🔎 Filtered Results")
    st.dataframe(filtered_df)

    # 🧠 Summary
    st.markdown("### 🧠 Summary Insights")
    total_credit = filtered_df[filtered_df.Amount > 0]['Amount'].sum()
    total_debit = filtered_df[filtered_df.Amount < 0]['Amount'].sum()
    top_sender = filtered_df['Sender'].value_counts().idxmax() if filtered_df['Sender'].notna().any() else "N/A"
    largest_txn = filtered_df.loc[filtered_df['Amount'].abs().idxmax()] if not filtered_df.empty else None

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Credit", f"₹{total_credit:,.2f}")
    col2.metric("Total Debit", f"₹{total_debit:,.2f}")
    col3.metric("Top Sender", top_sender)

    if largest_txn is not None:
        st.markdown(f"**📌 Largest Transaction:** ₹{largest_txn['Amount']:,.2f} on {largest_txn['Date'].date()} — {largest_txn['Description']}")

    # 📊 Charts
    st.markdown("### 📊 Transaction Trends")

    if not filtered_df.empty:
        daily = filtered_df.groupby(filtered_df['Date'].dt.date)['Amount'].sum().reset_index()
        fig1 = px.bar(daily, x='Date', y='Amount', title='Daily Net Transactions')
        st.plotly_chart(fig1, use_container_width=True)

        balance_trend = filtered_df[['Date', 'Balance']].dropna()
        fig2 = px.line(balance_trend, x='Date', y='Balance', title='Balance Over Time')
        st.plotly_chart(fig2, use_container_width=True)

        txn_types = filtered_df['Description'].str.extract(r'(UPI|NEFT|ATM)', expand=False).value_counts()
        if not txn_types.empty:
            fig3 = px.pie(txn_types, names=txn_types.index, values=txn_types.values, title='Transaction Type Breakdown')
            st.plotly_chart(fig3, use_container_width=True)

    # 📥 Downloads
    st.markdown("### 📥 Download Outputs")
    if os.path.exists(month_path):
        with open(month_path, "rb") as f:
            st.download_button(f"Download {selected_month} Statement", f, file_name=f"Bank_Statement_{selected_month}.xlsx")
    else:
        st.warning(f"Statement file for {selected_month} not found.")

    analysis_file = os.path.join("output", f"Analysis_{selected_month}.xlsx")
    if os.path.exists(analysis_file):
        with open(analysis_file, "rb") as f:
            st.download_button(f"Download {selected_month} Analysis", f, file_name=f"Analysis_{selected_month}.xlsx")
    else:
        st.warning(f"Analysis file for {selected_month} not found.")
