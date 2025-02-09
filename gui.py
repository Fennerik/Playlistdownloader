import tkinter as tk
from tkinter import filedialog
import os
import shutil
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, unquote
from datetime import datetime
import mimetypes
import threading

root = tk.Tk()
root.title("Playlistextractor Stable 2.0")


# Variable to save the file path
playpath = tk.StringVar(value="Playlist file path: None")  # Debugging
destination_folder = tk.StringVar(value="Output folder: None")  # Debugging

def openfile():
    file_path = filedialog.askopenfilename(
        initialdir="/",
        title="Select playlist file",
        filetypes=[("Playlist files", "*.wpl *.m3u")]  # Nur .wpl und .m3u erlaubt
    )
    if file_path:  # Nur aktualisieren, wenn eine Datei gewählt wurde
        playpath.set(f"File path: {file_path}")

def select_output_folder():
    folderpath = filedialog.askdirectory(
        initialdir="/",
        title="Select output folder"
    )
    if folderpath:  # Nur aktualisieren, wenn ein Ordner gewählt wurde
        destination_folder.set(f"Output folder: {folderpath}")

def start_extraction():
    logpreview.config(state=tk.NORMAL)  # Ermöglicht das Hinzufügen von Text
    logpreview.insert(tk.END, playpath.get() + "\n" + destination_folder.get() + "\n")
    playlist_path = playpath.get().replace("File path: ", "")  # Den Pfad ohne "File path: " verwenden
    if not os.path.isfile(playlist_path):
        log_to_both(f"Playlist file not found: {playlist_path}\n")
        return
    
    files = read_playlist(playlist_path)
    if not files:
        log_to_both(f"The playlist does not contain any valid entries: {playlist_path}\n")
        return

    os.makedirs(destination_folder.get().replace("Output folder: ", ""), exist_ok=True)  # Den Ordnerpfad bereinigen
    # Starten der Extraktionsoperation im Hintergrund
    extraction_thread = threading.Thread(target=extract_files, args=(files, destination_folder.get().replace("Output folder: ", "")))
    extraction_thread.start()

def log_to_both(message):
    # Loggt sowohl in das Textfeld als auch in die Logdatei
    logpreview.insert(tk.END, message)
    logpreview.yview(tk.END)  # Scrollt immer zum neuesten Eintrag im Textfeld
    log_file = os.path.join(destination_folder.get().replace("Output folder: ", ""), "latestlog.log")
    with open(log_file, "a", encoding="utf-8") as log:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.write(f"[{timestamp}] {message}\n")

def read_playlist(file_path):
    file_paths = []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        
        # Prüfen, ob es eine WPL-Playlist ist (XML-Struktur mit <smil>)
        if "<smil>" in content.lower():
            try:
                tree = ET.fromstring(content)
                for media in tree.findall(".//media"):  # Ohne Namespace
                    path = media.get("src")
                    if path:
                        file_paths.append(path)
            except ET.ParseError as e:
                log_to_both(f"Error parsing XML: {e}\n")
                return None
        
        # Prüfen, ob es eine M3U-Playlist ist
        elif "#EXTM3U" in content or file_path.endswith(".m3u"):
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and not line.lower().startswith("<"):
                    if line.startswith("file:///"):
                        parsed = urlparse(line)
                        path = unquote(parsed.path).lstrip("/")
                        file_paths.append(path)
                    else:
                        file_paths.append(line)
        else:
            log_to_both(f"Unknown playlist format. Only .wpl and .m3u are supported.\n")
            return None
    except FileNotFoundError:
        log_to_both(f"Playlist file not found: {file_path}\n")
        return None
    except Exception as e:
        log_to_both(f"Error reading playlist: {e}\n")
        return None
    return file_paths

def extract_files(file_paths, destination_folder):
    for file_path in file_paths:
        try:
            if os.path.isfile(file_path):
                mime_type, _ = mimetypes.guess_type(file_path)
                if mime_type and mime_type.startswith("audio/"):
                    destination_path = os.path.join(destination_folder, os.path.basename(file_path))
                    if os.path.exists(destination_path):
                        log_to_both(f"Skipped (already exists): {file_path}\n")
                        continue
                    shutil.copy2(file_path, destination_path)
                    log_to_both(f"Copied: {file_path}\n")
                else:
                    log_to_both(f"Skipped (not an audio file): {file_path}\n")
            else:
                log_to_both(f"File not found: {file_path}\n")
        except Exception as e:
            log_to_both(f"Error copying file: {file_path} - {e}\n")
    log_to_both(f"Finished \n")
    logpreview.config(state=tk.DISABLED)  # Textfeld wieder schreibgeschützt machen

# GUI-Elemente erstellen
Header = tk.Label(root, text="Playlistextractor Stable 2.0", font=("Gill Sans", 24))
Header.grid(row=0, column=0, columnspan=2, pady=10)

# Datei-Pfad und Button nebeneinander
pathshow = tk.Label(root, textvariable=playpath, font=("Gill Sans", 12), anchor="w", width=50)
pathshow.grid(row=1, column=0, padx=10, pady=5, sticky="w")

buttonopen = tk.Button(root, text="Select playlist file", command=openfile, height=1, width=15)
buttonopen.grid(row=1, column=1, padx=10, pady=5)

# Ordner-Pfad und Button nebeneinander
outshow = tk.Label(root, textvariable=destination_folder, font=("Gill Sans", 12), anchor="w", width=50)
outshow.grid(row=2, column=0, padx=10, pady=5, sticky="w")

buttonout = tk.Button(root, text="Select output folder", command=select_output_folder, height=1, width=15)
buttonout.grid(row=2, column=1, padx=10, pady=5)

buttonstart = tk.Button(root, command=start_extraction, text="Start extraction", height=2, width=30)
buttonstart.grid(row=3, column=0, columnspan=2, pady=10)

logpreview = tk.Text(root, height=10, width=90, font=("Gill Sans", 12))
logpreview.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

logpreview.config(state=tk.DISABLED)  # Textfeld initial auf read-only setzen

# Setze die Spaltenbreiten, damit Buttons nicht verschoben werden
root.grid_columnconfigure(0, weight=1)  # Linke Spalte wächst mit
root.grid_columnconfigure(1, weight=0)  # Rechte Spalte (Buttons) bleibt fix

root.mainloop()
