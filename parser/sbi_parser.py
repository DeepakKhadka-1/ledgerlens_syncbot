import pdfplumber
import pandas as pd
import re
from datetime import datetime

def parse_sbi_pdf(pdf_path):
    transactions = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_tables()
            for tbl in table:
                for row in tbl:
                    if len(row) != 6:
                        continue

                    date_raw, details, ref, debit, credit, balance = row

                    if not date_raw or "Date" in date_raw:
                        continue

                    try:
                        date = datetime.strptime(date_raw.strip(), "%d %b %Y")
                    except ValueError:
                        continue

                    debit = float(debit.replace(",", "")) if debit and debit != "-" else 0.0
                    credit = float(credit.replace(",", "")) if credit and credit != "-" else 0.0
                    amount = credit if credit > 0 else -debit

                    try:
                        balance = float(balance.replace(",", ""))
                    except:
                        balance = None

                    transactions.append({
                        "Date": date,
                        "Description": details.strip(),
                        "Amount": amount,
                        "Type": "CR" if amount > 0 else "DR",
                        "Balance": balance,
                        "Sender": extract_sender(details),
                        "Reference": extract_reference(details, ref)
                    })

    df = pd.DataFrame(transactions)

    # ✅ Normalize fields to catch hidden duplicates
    df["Description"] = df["Description"].str.strip().str.lower()
    df["Sender"] = df["Sender"].astype(str).str.strip().str.upper()

    # ✅ Deduplicate using expanded key
    df.drop_duplicates(subset=["Date", "Amount", "Sender", "Reference", "Description"], inplace=True)

    return df

def extract_sender(description):
    parts = description.split('/')
    for i in range(len(parts)):
        if re.match(r'\d{9,}', parts[i]):  # UPI reference number
            if i + 1 < len(parts):
                return parts[i + 1].strip()
    return None

def extract_reference(description, ref_field):
    match = re.search(r'UPI/(CR|DR)/(\d+)', description)
    if match:
        return match.group(2)
    elif ref_field and ref_field.strip().isdigit():
        return ref_field.strip()
    return None
