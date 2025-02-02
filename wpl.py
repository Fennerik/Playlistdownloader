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
                print("XML-Baum erfolgreich geparst.")
                for media in tree.findall(".//media"):  # Ohne Namespace
                    path = media.get("src")
                    if path:
                        print(f"Gefundener Pfad: {path}")
                        file_paths.append(path)
                    else:
                        print("<media>-Element ohne 'src'-Attribut gefunden.")
                if not file_paths:
                    print("Keine gültigen Pfade im <media>-Element gefunden")

            except ET.ParseError as e:
                print(f"Fehler beim Parsen des XML (nach Whitespace-Entfernung): {e}")
                print("Inhalt nach Whitespace-Entfernung:")
                print(content)
                return None

        elif "#EXTM3U" in content:
            print("M3U-Playlist erkannt.")
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("file:///"):
                    parsed = urlparse(line)
                    path = unquote(parsed.path).lstrip("/")
                elif line[0].isalpha() and line[1] == ':':
                    drive_letter = line[0]
                    path = os.path.join(drive_letter, line[2:])
                elif "://" not in line:
                    base_path = os.path.dirname(file_path)
                    absolute_path = os.path.abspath(os.path.join(base_path, line))
                    path = absolute_path
                else:
                    print(f"Ignoriere Zeile (URL oder unbekanntes Format): {line}")
                    continue #wichtig, damit kein None in file_paths landet
                print(f"Gefundener Pfad: {path}")
                file_paths.append(path)

        else:
            print("Unbekanntes Playlist-Format. Nur .wpl und .m3u werden unterstützt.")
            return None

    except FileNotFoundError:
        print(f"Playlist-Datei nicht gefunden: {file_path}")
        return None
    except Exception as e:
        print(f"Fehler beim Lesen der Playlist: {e}")
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
                        print(f"Datei existiert bereits im Ziel: {os.path.basename(file_path)}, wird übersprungen.")
                        log_entry(log_file, f"Übersprungen: {file_path} - Datei existiert bereits im Ziel.")
                        continue
                    shutil.copy2(file_path, destination_path)
                    print(f"Kopiert: {file_path}")
                    log_entry(log_file, f"Erfolgreich kopiert: {file_path}")
                else:
                    print(f"Datei ist keine Audiodatei oder MIME-Typ unbekannt: {file_path}")
                    log_entry(log_file, f"Fehler: Datei ist keine Audiodatei oder MIME-Typ unbekannt - {file_path}")
            else:
                print(f"Datei nicht gefunden: {file_path}")
                log_entry(log_file, f"Fehler: Datei nicht gefunden - {file_path}")
        except Exception as e:
            print(f"Fehler beim Kopieren der Datei {file_path}: {e}")
            log_entry(log_file, f"Fehler beim Kopieren: {file_path} - {e}")

if __name__ == "__main__":
    print("Programm zum Kopieren von Musikdateien aus einer Playlist")

    try:
        playlist_path = input("Pfad zur Playlist-Datei (WPL oder M3U): ").strip()
        print(f"Eingegebener Playlist-Pfad: {playlist_path}")

        files = read_playlist(playlist_path)

        if files is None:
            print("Fehler beim Lesen der Playlist.")
            exit()
        elif not files:
            print("Die Playlist enthält keine gültigen Einträge.")
            exit()

        destination_folder = input("Pfad zum Zielordner: ").strip()
        print(f"Eingegebener Zielordner: {destination_folder}")
        os.makedirs(destination_folder, exist_ok=True)

        copy_files(files, destination_folder)
        print("Fertig.")

    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
