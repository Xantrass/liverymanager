import ftplib
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime

def load_config():
    try:
        with open("config.txt", "r") as f:
            lines = f.read().splitlines()
            return lines[0], lines[1], lines[2], lines[3], lines[4]
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Laden der Konfigurationsdatei: {e}")
        return None, None, None, None, ""

def save_last_directory(directory):
    try:
        with open("config.txt", "r") as f:
            lines = f.read().splitlines()
        lines[4] = directory
        with open("config.txt", "w") as f:
            f.write("\n".join(lines))
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Speichern des lokalen Verzeichnisses: {e}")

def log_download(file_name):
    with open("download_log.txt", "a") as log_file:
        log_file.write(f"{datetime.now()} - {file_name} heruntergeladen\n")

def list_ftp_files():
    server, username, password, remote_folder, _ = load_config()
    
    if not server or not username or not password or not remote_folder:
        return
    
    try:
        with ftplib.FTP_TLS(server) as ftp:
            ftp.login(username, password)
            ftp.prot_p()
            ftp.cwd(remote_folder)
            files = ftp.nlst()
            listbox_ftp_files.delete(0, tk.END)
            for file in files:
                listbox_ftp_files.insert(tk.END, file)
    except Exception as e:
        messagebox.showerror("Fehler", str(e))

def list_local_files():
    local_path = entry_local_path.get()
    
    if not local_path:
        messagebox.showerror("Fehler", "Bitte geben Sie einen lokalen Ordner an.")
        return
    
    try:
        files = os.listdir(local_path)
        listbox_local_files.delete(0, tk.END)
        for file in files:
            listbox_local_files.insert(tk.END, file)
        save_last_directory(local_path)
    except Exception as e:
        messagebox.showerror("Fehler", str(e))

def download_selected_file():
    threading.Thread(target=download_file_thread).start()

def download_file_thread():
    server, username, password, remote_folder, _ = load_config()
    local_path = entry_local_path.get()
    selected_file = listbox_ftp_files.get(tk.ACTIVE)
    
    if not server or not username or not password or not remote_folder:
        return
    
    if not local_path:
        messagebox.showerror("Fehler", "Bitte geben Sie einen lokalen Ordner an.")
        return
    
    try:
        with ftplib.FTP_TLS(server) as ftp:
            ftp.login(username, password)
            ftp.prot_p()
            ftp.cwd(remote_folder)
            ftp.voidcmd("TYPE I")  # Wechsel in Binärmodus
            file_size = ftp.size(selected_file)
            progress_bar['maximum'] = file_size
            progress_bar['value'] = 0
            
            local_file = os.path.join(local_path, selected_file)
            
            def write_with_progress(data):
                f.write(data)
                progress_bar.step(len(data))
                root.update_idletasks()
            
            with open(local_file, "wb") as f:
                ftp.retrbinary(f"RETR {selected_file}", write_with_progress, 1024)
        
        log_download(selected_file)
        messagebox.showinfo("Erfolg", f"Datei {selected_file} erfolgreich heruntergeladen.")
        list_local_files()
        progress_bar['value'] = 0  # Reset Progress Bar nach Abschluss
    except Exception as e:
        messagebox.showerror("Fehler", str(e))


# GUI erstellen
root = tk.Tk()
root.title("FTP Downloader")

tk.Label(root, text="Lokaler Ordner:").grid(row=0, column=0, columnspan=2)
entry_local_path = tk.Entry(root)
entry_local_path.grid(row=0, column=2, columnspan=2)
_, _, _, _, last_directory = load_config()
entry_local_path.insert(0, last_directory)

tk.Button(root, text="Liste abrufen", command=lambda: [list_ftp_files(), list_local_files()]).grid(row=1, column=0, columnspan=4)

tk.Label(root, text="Lokale Dateien").grid(row=2, column=0, columnspan=2)
tk.Label(root, text="FTP Dateien").grid(row=2, column=2, columnspan=2)

listbox_local_files = tk.Listbox(root, width=50, height=10)
listbox_local_files.grid(row=3, column=0, columnspan=2)

listbox_ftp_files = tk.Listbox(root, width=50, height=10)
listbox_ftp_files.grid(row=3, column=2, columnspan=2)

tk.Button(root, text="Download", command=download_selected_file).grid(row=4, column=2, columnspan=2)

progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar.grid(row=5, column=2, columnspan=2, pady=5)

root.mainloop()
