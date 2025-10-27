import pandas as pd

def parse_generic_file(file_path):
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)

    df.columns = [col.strip().lower() for col in df.columns]

    column_map = {
        'date': 'Date',
        'description': 'Description',
        'amount': 'Amount',
        'type': 'Type',
        'balance': 'Balance',
        'sender': 'Sender',
        'reference': 'Reference'
    }

    for raw, std in column_map.items():
        for col in df.columns:
            if raw in col:
                df.rename(columns={col: std}, inplace=True)

    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    if 'Amount' in df.columns:
        df['Amount'] = df['Amount'].astype(str).str.replace(',', '').astype(float)

    for col in column_map.values():
        if col not in df.columns:
            df[col] = None

    return df[column_map.values()]
