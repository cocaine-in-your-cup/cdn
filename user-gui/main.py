import datetime
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import json
import requests
import sys
from urllib.request import urlopen
from tqdm import tqdm

class TextRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)  # Auto-scroll to the end

def fetch_data():
    url = entry.get()
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        listbox.delete(0, tk.END)
        
        header_text = "{:<15} {:<20} {:<10}".format("Key", "Last Modified", "Size")
        listbox.insert(tk.END, header_text)

        for item in data:
            key = item["key"]
            last_modified = datetime.datetime.strptime(item["last_modified"], "%Y-%m-%dT%H:%M:%S.%fZ")
            size_in_bytes = int(item["size"])
            
            formatted_item = "{:<15} {:<20} {:<10}".format(item["key"], item["last_modified"], item["size"])
            listbox.insert(tk.END, formatted_item)
            # listbox.insert(tk.END, f"{key}          /          {last_modified}          /          {size_in_bytes} Bytes")
        log_message("Data fetched successfully.")
    except requests.exceptions.RequestException as e:
        log_message(f"Error fetching data: {e}")

def download_file():
    url = entry.get()
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
    if file_path:
        with urlopen(url) as response, open(file_path, 'wb') as file:
            total_size = int(response.info().get('Content-Length', 0))
            block_size = 1024
            progress_bar['maximum'] = total_size
            with tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    file.write(buffer)
                    progress_bar['value'] += len(buffer)
                    pbar.update(len(buffer))
            log_message("File downloaded successfully.")

def log_message(message):
    console_output.insert(tk.END, message + "\n")
    console_output.see(tk.END)  # Auto-scroll to the end

root = tk.Tk()


url_label = tk.Label(root, text="CDN-URL:")
url_label.pack(pady=10)

entry = tk.Entry(root,width=100)
entry.insert(0, "http://127.0.0.1:8080/")
entry.pack(pady=10)

fetch_button = tk.Button(root, text="Fetch", command=fetch_data)
fetch_button.pack()


# Create a label for column headers
my_game = ttk.Treeview(root, columns=('player_id', 'player_name', 'player_Rank', 'player_states', 'player_city'))
my_game.pack(pady=10)

listbox = tk.Listbox(root, width=150)
listbox.pack()

download_button = tk.Button(root, text="Download", command=download_file)
download_button.pack(pady=10)

progress_bar = ttk.Progressbar(root, orient='horizontal', length=200, mode='determinate')
progress_bar.pack(pady=10)

console_output = tk.Text(root, height=10)
console_output.pack(pady=10)

# Redirect stdout and stderr to the console output
sys.stdout = TextRedirector(console_output)
sys.stderr = TextRedirector(console_output)

root.mainloop()
