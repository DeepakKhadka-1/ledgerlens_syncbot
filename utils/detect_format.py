import os

def detect_file_format(file_path):
    filename = os.path.basename(file_path).lower()

    if filename.endswith('.pdf'):
        file_type = 'pdf'
    elif filename.endswith('.csv'):
        file_type = 'csv'
    elif filename.endswith('.xlsx') or filename.endswith('.xls'):
        file_type = 'excel'
    else:
        file_type = 'unknown'

    if 'sbi' in filename:
        bank_name = 'sbi'
    elif 'hdfc' in filename:
        bank_name = 'hdfc'
    elif 'icici' in filename:
        bank_name = 'icici'
    else:
        bank_name = 'unknown'

    return {
        'file_type': file_type,
        'bank_name': bank_name
    }
