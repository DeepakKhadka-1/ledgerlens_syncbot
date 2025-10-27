import pandas as pd
import os

def write_to_sheets(df, output_dir='output'):
    os.makedirs(output_dir, exist_ok=True)

    master_path = os.path.join(output_dir, 'All_Transactions.xlsx')
    if os.path.exists(master_path):
        existing = pd.read_excel(master_path)
        df = pd.concat([existing, df], ignore_index=True)
    df.to_excel(master_path, index=False)

    df['Month'] = df['Date'].dt.strftime('%Y_%m')
    for month, group in df.groupby('Month'):
        month_path = os.path.join(output_dir, f'Bank_Statement_{month}.xlsx')
        group.drop(columns='Month').to_excel(month_path, index=False)
