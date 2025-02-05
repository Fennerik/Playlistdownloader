import os
import shutil
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, unquote
from datetime import datetime
import mimetypes

def log_entry(log_file, message):
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
                print(f"Error parsing XML: {e}")
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
            print("Unknown playlist format. Only .wpl and .m3u are supported.")
            return None
    except FileNotFoundError:
        print(f"Playlist file not found: {file_path}")
        return None
    except Exception as e:
        print(f"Error reading playlist: {e}")
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
                        print(f"Skipped (already exists): {file_path}")
                        log_entry(log_file, f"Skipped: {file_path}")
                        continue
                    shutil.copy2(file_path, destination_path)
                    print(f"Copied: {file_path}")
                    log_entry(log_file, f"Copied: {file_path}")
                else:
                    print(f"Skipped (not an audio file): {file_path}")
                    log_entry(log_file, f"Skipped (not an audio file): {file_path}")
            else:
                print(f"File not found: {file_path}")
                log_entry(log_file, f"Error: File not found - {file_path}")
        except Exception as e:
            print(f"Error copying file: {file_path}: {e}")
            log_entry(log_file, f"Error copying file: {file_path} - {e}")

if __name__ == "__main__":
    print("Program to extract music files from a playlist.")
    playlist_path = input("Path to playlist file (.wpl or .m3u): ").strip()
    if not os.path.isfile(playlist_path):
        print("Playlist file not found.")
        exit()
    
    files = read_playlist(playlist_path)
    if not files:
        print("The playlist does not contain any valid entries.")
        exit()
    
    destination_folder = input("Path to target directory: ").strip()
    os.makedirs(destination_folder, exist_ok=True)
    copy_files(files, destination_folder)
    print("Finished.")
