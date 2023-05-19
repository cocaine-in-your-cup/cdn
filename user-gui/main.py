import datetime
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import json
import requests
import sys
from urllib.request import urlopen
from tqdm import tqdm
import math

def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])

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
        
        my_game.delete(*my_game.get_children())  # Clear existing items
        for item in data:            
            key = item["key"]
            last_modified = datetime.datetime.strptime(item["last_modified"], "%Y-%m-%dT%H:%M:%S.%fZ")
            size_in_bytes = int(item["size"])
            my_game.insert('', tk.END, values=(key,last_modified,convert_size(size_in_bytes)))
        log_message("Data fetched successfully.")
    except requests.exceptions.RequestException as e:
        log_message(f"Error fetching data: {e}")

def on_select(event):
    selected_item = my_game.focus()
    if selected_item:
        values = my_game.item(selected_item)['values']
        if values:
            text_output.delete("1.0", tk.END)  # Clear existing text
            text_output.insert(tk.END, f"URL: {entry.get()}/{values[0]}")

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

root = tk.Tk(className="CDN Download CLient")


url_label = tk.Label(root, text="CDN-URL:")
url_label.pack(pady=10)

entry = tk.Entry(root,width=100)
entry.insert(0, "http://127.0.0.1:8080/")
entry.pack(pady=10)

fetch_button = tk.Button(root, text="Fetch", command=fetch_data)
fetch_button.pack()


# Create a label for column headers
my_game = ttk.Treeview(root, columns=('Name', 'TimeStamp', 'Size'))
my_game.pack(pady=10)

for col in my_game['columns']:
    my_game.heading(col, text=col)
    my_game.column(col, width=400)

my_game.bind('<<TreeviewSelect>>', on_select)

text_output = tk.Text(root, height=5, width=40)
text_output.pack(pady=10)

download_button = tk.Button(root, text="Download", command=download_file)
download_button.pack(pady=10)

progress_bar = ttk.Progressbar(root, orient='horizontal', length=400, mode='determinate')
progress_bar.pack(pady=10)

console_output = tk.Text(root, height=10)
console_output.pack(pady=10)

# Redirect stdout and stderr to the console output
sys.stdout = TextRedirector(console_output)
sys.stderr = TextRedirector(console_output)

root.mainloop()
