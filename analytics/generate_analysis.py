import pandas as pd
import os

def generate_fresh_analysis(parsed_df, selected_month):
    """
    Generates a fresh analysis Excel file for the selected month.
    Overwrites any existing file with the same name.
    """
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    analysis_file = os.path.join(output_dir, f"Analysis_{selected_month}.xlsx")
    parsed_df.to_excel(analysis_file, index=False)
    return analysis_file
