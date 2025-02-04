import os
import shutil
from urllib.parse import urlparse, unquote
from datetime import datetime

# Funktion zum Einlesen der Dateipfade aus einer Playlist (WPL oder M3U)
def read_playlist(file_path):
    file_paths = []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                # WPL- und M3U-spezifische Anpassungen
                line = line.strip()
                if line and not line.startswith("#") and not line.lower().startswith("<"):  # Überspringe Kommentare und XML-Tags
                    # URLs in Dateipfade umwandeln, falls nötig
                    if line.startswith("file:///"):
                        parsed = urlparse(line)
                        path = unquote(parsed.path)  # URL-encoded Zeichen wie %20 zu Leerzeichen umwandeln
                        file_paths.append(path.lstrip("/"))  # Entferne führenden Slash bei Windows-Pfaden
                    else:
                        file_paths.append(line)
    except Exception as e:
        print(f"Error while reading the playlist: {e}")
    return file_paths

# Funktion zum Hinzufügen eines Log-Eintrags
def log_entry(log_file, message):
    with open(log_file, "a", encoding="utf-8") as log:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.write(f"[{timestamp}] {message}\n")

# Funktion zum Kopieren von Dateien in das Zielverzeichnis
def copy_files(file_paths, destination_folder):
    log_file = os.path.join(destination_folder, "latestlog.log")
    for file_path in file_paths:
        try:
            # Überprüfen, ob die Datei existiert
            if os.path.isfile(file_path):
                # Datei in das Zielverzeichnis kopieren
                shutil.copy(file_path, destination_folder)
                print(f"Copied: {file_path}")
                log_entry(log_file, f"Copied successfully: {file_path}")
            else:
                print(f"File not found: {file_path}")
                log_entry(log_file, f"Error: File not found - {file_path}")
        except Exception as e:
            print(f"Error while copying the file: {file_path}: {e}")
            log_entry(log_file, f"Error while copying the file: {file_path} - {e}")

if __name__ == "__main__":
    print("Program to extract music files from a playlist.")
    # Eingabe der Quell-Playlist
    playlist_path = input("Path to playlist file (.m3u): ").strip()
    if not os.path.isfile(playlist_path):
        print("Playlist file not found: {playlist_path}")
        exit()

    # Eingabe des Zielverzeichnisses
    destination_folder = input("Path to target directory: ").strip()
    if not os.path.exists(destination_folder):
        try:
            os.makedirs(destination_folder)
        except Exception as e:
            print(f"Error while creating target directory: {e}")
            exit()

    # Playlist einlesen und Dateien kopieren
    files = read_playlist(playlist_path)
    if not files:
        print("The playlist does not contain any valid entries.")
    else:
        copy_files(files, destination_folder)

    print("Finished.")
