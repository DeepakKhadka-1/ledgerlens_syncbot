import pandas as pd
import os

def analyze_month(month_str, output_dir='output'):
    input_path = os.path.join(output_dir, f'Bank_Statement_{month_str}.xlsx')
    output_path = os.path.join(output_dir, f'Analysis_{month_str}.xlsx')

    if not os.path.exists(input_path):
        print(f"❌ No statement found for {month_str}")
        return

    df = pd.read_excel(input_path)

    total_credit = df[df['Amount'] > 0]['Amount'].sum()
    total_debit = df[df['Amount'] < 0]['Amount'].sum()
    daily_avg = df.groupby(df['Date'].dt.date)['Amount'].sum().mean()
    top_senders = df['Sender'].value_counts().head(5)

    upi = df[df['Description'].str.contains('UPI', case=False, na=False)]
    neft = df[df['Description'].str.contains('NEFT', case=False, na=False)]
    atm = df[df['Description'].str.contains('ATM', case=False, na=False)]

    summary = pd.DataFrame({
        'Metric': ['Total Credit', 'Total Debit', 'Daily Avg', 'UPI Txns', 'NEFT Txns', 'ATM Txns'],
        'Value': [total_credit, total_debit, daily_avg, len(upi), len(neft), len(atm)]
    })

    with pd.ExcelWriter(output_path) as writer:
        summary.to_excel(writer, sheet_name='Summary', index=False)
        top_senders.to_frame(name='Count').to_excel(writer, sheet_name='Top Senders')

    print(f"✅ Analysis saved to {output_path}")
