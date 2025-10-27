import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from utils.detect_format import detect_file_format
from parser.sbi_parser import parse_sbi_pdf
from parser.generic_parser import parse_generic_file
from replicator.sheet_writer import write_to_sheets
from analytics.monthly_analysis import analyze_month

class StatementHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return

        file_path = event.src_path
        print(f"📥 New file detected: {file_path}")

        info = detect_file_format(file_path)
        file_type = info['file_type']
        bank_name = info['bank_name']

        if file_type == 'pdf' and bank_name == 'sbi':
            df = parse_sbi_pdf(file_path)
        elif file_type in ['csv', 'excel']:
            df = parse_generic_file(file_path)
        else:
            print(f"⚠️ Unsupported format or bank: {file_type}, {bank_name}")
            return

        write_to_sheets(df)
        month_str = df['Date'].dt.strftime('%Y_%m').iloc[0]
        analyze_month(month_str)

        os.remove(file_path)
        print(f"✅ Processed and removed: {file_path}")

def start_monitoring(input_dir='input'):
    event_handler = StatementHandler()
    observer = Observer()
    observer.schedule(event_handler, input_dir, recursive=False)
    observer.start()
    print(f"👀 Watching folder: {input_dir}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
