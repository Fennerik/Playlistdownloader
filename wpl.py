import os
import shutil
from urllib.parse import urlparse, unquote
import xml.etree.ElementTree as ET
import mimetypes
import re
from datetime import datetime

# Funktion zum Hinzufügen eines Log-Eintrags
def log_entry(log_file, message):
    with open(log_file, "a", encoding="utf-8") as log:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.write(f"[{timestamp}] {message}\n")

def read_playlist(file_path):
    file_paths = []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        content = re.sub(r"^\s+", "", content, flags=re.MULTILINE)

        if "<smil>" in content.lower():
            try:
                tree = ET.fromstring(content)
                print("XML-Baum successfully parsed.")
                for media in tree.findall(".//media"):  # Ohne Namespace
                    path = media.get("src")
                    if path:
                        print(f"Gefundener Pfad: {path}")
                        file_paths.append(path)
                    else:
                        print("found <media>-element without 'src'-attribute.")
                if not file_paths:
                    print("No valid paths found in the  <media>-Element.")

            except ET.ParseError as e:
                print(f"Error parsing the XML (after Whitespace-removing): {e}")
                print("Content after whitespace-removing:")
                print(content)
                return None

#        elif "#EXTM3U" in content:
#            print("M3U-Playlist erkannt.")
        else:
            print("Unbekanntes Playlist-Format. Nur .wpl wird unterstützt unterstützt.")
            return None

    except FileNotFoundError:
        print(f"Playlist file not found: {file_path}")
        return None
    except Exception as e:
        print(f"Error while reading the playlist file: {e}")
        return None
    return file_paths

def copy_files(file_paths, destination_folder):
    if not file_paths:
        return

    log_file = os.path.join(destination_folder, "latestlog.log")

    for file_path in file_paths:
        try:
            if os.path.isfile(file_path):
                mime_type, _ = mimetypes.guess_type(file_path)
                if mime_type and mime_type.startswith("audio/"):
                    destination_path = os.path.join(destination_folder, os.path.basename(file_path))
                    if os.path.exists(destination_path):
                        print(f"File already exits in target directory: {os.path.basename(file_path)}, is skipped.")
                        log_entry(log_file, f"Skipped: {file_path} - File already exist in target directory.")
                        continue
                    shutil.copy2(file_path, destination_path)
                    print(f"Copied: {file_path}")
                    log_entry(log_file, f"Copied successfully: {file_path}")
                else:
                    print(f"File is no audio file or unknown MIME-Type: {file_path}")
                    log_entry(log_file, f"Error: File is no audio file or unknown MIME-Typ - {file_path}")
            else:
                print(f"File not found {file_path}")
                log_entry(log_file, f"Error: File not found - {file_path}")
        except Exception as e:
            print(f"Error while copying the file {file_path}: {e}")
            log_entry(log_file, f"Error while copying the file: {file_path} - {e}")

if __name__ == "__main__":
    print("Program to extract music files from a playlist.")

    try:
        playlist_path = input("Path to playlist file (.wpl): ").strip()
        print(f"Given playlist path: {playlist_path}")

        files = read_playlist(playlist_path)

        if files is None:
            print("Error while reading the playlist.")
            exit()
        elif not files:
            print("The playlist does not contain any valid entries.")
            exit()

        destination_folder = input("Path to target directory: ").strip()
        print(f"Given target directory: {destination_folder}")
        os.makedirs(destination_folder, exist_ok=True)

        copy_files(files, destination_folder)
        print("Finihsed.")

    except Exception as e:
        print(f"An unexpected error occurred.: {e}")

