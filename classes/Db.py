import os
import requests
import sqlite3
from mutagen              import MutagenError
from mutagen.easyid3      import EasyID3
from mutagen.id3          import ID3
from mutagen.mp3          import MP3
from PyQt6.QtWidgets      import QInputDialog, QFileDialog

class Db():
    def __init__(self, main):
        self.main      = main
        self.dir       = os.getcwd() + os.sep + "db" + os.sep
        self.conn      = None
        self.cursor    = None
        self.names     = {"genre"    :"Genres", 
                          "album"    :"Alben", 
                          "artist"   :"Künstler", 
                          "language" :"Sprache", 
                          "date"     :"Jahr"}

        self.check_database()

        self.folded    = self.init_folded()

    def add_song_to_list(self, list):
        if list == "":
            return
        file_id = self.main.widget.detail_widgets[0].text()

        self.cursor.execute('SELECT id FROM LISTS WHERE name = "' + list + '"')
        list_id = self.cursor.fetchone()[0]

        self.cursor.execute('SELECT COUNT(*) FROM LIST_CONTENT WHERE list_id="' + str(list_id) + \
                            '" AND file_id="' + str(file_id) + '"')
        exists = self.cursor.fetchone()[0] > 0
        if not exists:
            self.cursor.execute('INSERT INTO LIST_CONTENT (list_id, file_id) VALUES ("' + \
                                str(list_id) + '","' + str(file_id) + '")')
            self.conn.commit()            
    def check_database(self):
        if not os.path.isdir(self.dir):
            os.makedirs(self.dir)

        db_file = self.dir + "mymusic.db"
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS FILES (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                vote      INTEGER NOT NULL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS TAGS (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id   INTEGER NOT NULL,
                tag_key   TEXT NOT NULL,
                tag_value TEXT,
                FOREIGN KEY (file_id) REFERENCES FILES(id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS LISTS (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                name      TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS LIST_CONTENT (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                list_id     INTEGER NOT NULL,
                file_id     INTEGER NOT NULL,
                FOREIGN KEY (file_id) REFERENCES FILES(id),
                FOREIGN KEY (list_id) REFERENCES LISTS(id)
            )
        """)
        self.conn.commit()
    def create_list(self):
        name, ok = QInputDialog.getText(self.main, \
                                            "Neuer Listenname", \
                                            "Bitte geben Sie den Namen der neuen Liste ein" \
                                            )
        if ok:
            self.cursor.execute("SELECT COUNT(*) FROM LISTS WHERE name = '" + name + "'") 
            exists = self.cursor.fetchone()[0] > 0
            if exists:
                print("Dieser Listenname existiert bereits.")
            else:
                self.cursor.execute("INSERT INTO LISTS (name) VALUES ('" + name + "')")
                self.conn.commit()
        self.main.update_criteria()
    def delete_song_in_db(self, file_id):
        self.cursor.execute("DELETE FROM TAGS WHERE file_id = '" + str(file_id) + "'")
        self.cursor.execute("DELETE FROM FILES WHERE id = '" + str(file_id) + "'")
        self.conn.commit()
    def delete_duplicate_entries_in_db(self):
        self.cursor.execute("SELECT id, file_path, file_name, COUNT(*) FROM FILES GROUP BY file_path, file_name")
        for row in self.cursor.fetchall():
            if row[3] > 1:
                print("ID: " + str(row[0]) + ": " + row[1] + row[2])
                self.cursor.execute("DELETE FROM TAGS WHERE file_id = '" + str(row[0]) + "'")
                self.cursor.execute("DELETE FROM FILES WHERE id = '" + str(row[0]) + "'")
        self.conn.commit()
    def get_count_unassigned(self, criteria):
        self.cursor.execute('SELECT COUNT(FILES.id) FROM FILES LEFT JOIN TAGS ' + \
                            'ON FILES.id=TAGS.file_id AND TAGS.tag_key="' + criteria + \
                            '" WHERE TAGS.file_id IS NULL')
        for row in self.cursor.fetchall():
            return row[0]
    def get_details(self, file_id):
        result = {"file_id":file_id}

        result["filename_long"], result["vote"] = self.get_filename(file_id)
        if result["vote"] == None:
            result["vote"] = 0

        # Time #
        audio = MP3(result["filename_long"], ID3=ID3)
        dauer = int(audio.info.length)
        sec   = str(dauer % 60)
        result["dauer"] = str(int(dauer/60)) + ":" + str(sec.zfill(2))

        # for tag in audio.tags.values():
        #     if tag.FrameID == "APIC":  # Bild-Frame
        #         with open("tmp.jpg", "wb") as img:
        #             img.write(tag.data)
        #         print(f"Bild extrahiert: {output_image}")
        #         return True

        self.cursor.execute("SELECT tag_key, tag_value FROM TAGS WHERE file_id = '" + str(file_id) + "'") 
        result["tracknumber"] = result["album"] = result["artist"] = result["title"] = ""
        result["date"] = result["others"] = result["genre"] = result["language"] = ""
        genre_list = []
        for line in self.cursor.fetchall():
            if   line[0] == "tracknumber":  result["tracknumber"] = line[1]
            elif line[0] == "album":        result["album"]       = line[1]
            elif line[0] == "artist":       result["artist"]      = line[1]
            elif line[0] == "title":        result["title"]       = line[1]
            elif line[0] == "date":         result["date"]        = line[1]
            elif line[0] == "language":     result["language"]    = line[1]
            elif line[0] == "genre":        
                genre_list.append(line[1])
                if result["genre"] == "":
                    result["genre"] = line[1]
                else:
                    result["genre"] = result["genre"] + ", " + line[1]
            else:                           
                    result["others"] = result["others"] + line[0] + " => " + line[1] + "\n"
        
        # Get genres from internet #
        if result["genre"] == "":
            genre_web = []
            try:
                query      = "artist:" + result["artist"] + " AND recording:" + result["title"]
                url        = "https://musicbrainz.org/ws/2/recording/"
                params     = {"query": query, "fmt": "json"}
                headers    = {"User-Agent": "MyMusicTagger/1.0 (info@em-wee.de)"}
                resp       = requests.get(url, params=params, headers=headers)
                data       = resp.json()
                first      = data["recordings"][0]
                mbid       = first["id"]
            
                url        = f"https://musicbrainz.org/ws/2/recording/" + mbid
                params     = {"inc": "genres", "fmt": "json"}
                rec        = requests.get(url, params=params, headers=headers).json()
                genre_web  = [g["name"] for g in rec.get("genres", [])]
            except Exception as e:
                pass

            # Update Genre in Database from Internet-DB #
            for genre in genre_web:
                if result["genre"] == "":
                    result["genre"] = genre
                else:
                    result["genre"] = result["genre"] + ", " + genre
                self.cursor.execute("INSERT INTO TAGS (file_id, tag_key, tag_value) VALUES('" 
                                    + str(file_id) + "', 'genre', '" + genre + "')")
                self.conn.commit()

        return result    
    def get_filename(self, file_id):
        self.cursor.execute("SELECT file_path, file_name, vote FROM FILES WHERE id = '" + str(file_id) + "'")
        res = self.cursor.fetchall()
        return res[0][0] + os.sep + res[0][1], res[0][2]
    def get_file_ids_for_criteria(self, section, listname):
        arr = []
        if section == "own":
            self.cursor.execute('SELECT LIST_CONTENT.file_id FROM LIST_CONTENT JOIN LISTS ' + \
                                'ON LISTS.id=LIST_CONTENT.list_id AND LISTS.name = "' + listname + \
                                '" ORDER BY LIST_CONTENT.id')
            arr = self.cursor.fetchall()

        elif section == "vote":
            if listname == 'NULL':
                self.cursor.execute("SELECT id FROM FILES WHERE vote IS NULL ORDER BY RANDOM() LIMIT 100")
            else:
                self.cursor.execute("SELECT id FROM FILES WHERE vote = " + listname)
            arr = self.cursor.fetchall()
            # self.widget.fill_table_lines(arr)

        else:
            if listname == 'NULL':
                self.cursor.execute('SELECT FILES.id FROM FILES LEFT JOIN TAGS ' + \
                                    'ON FILES.id=TAGS.file_id AND TAGS.tag_key="' + section + \
                                    '" WHERE TAGS.file_id IS NULL ORDER BY FILES.id LIMIT 100')
                                    # '" WHERE TAGS.file_id IS NULL ORDER BY RANDOM() LIMIT 100')
            else:
                self.cursor.execute('SELECT file_id FROM TAGS WHERE tag_key = "' + section + '" AND tag_value LIKE "%' + listname + '%"') 
            arr = self.cursor.fetchall()
        return arr
    def get_fold_sign(self, status):
        if status == "is_open":
            sign = "ᐃ"
        else:
            sign = "ᐁ"
        return "<font color='gray'>" + sign + "</font>"
    def get_html(self):
        html = "<!DOCTYPE html><html><head></head><body>"     # Page Intro #

        html = html + "<p><a href='criterium_own'> " + self.get_fold_sign(self.folded["own"]) \
               + " <b>Eigene Listen</b></a>"                                                         # OWN #
        if self.folded["own"] == "is_open":
            self.cursor.execute("SELECT name FROM LISTS ORDER BY name")
            cnt = 0
            for row in self.cursor.fetchall():
                cnt = cnt + 1
                html = html + '<br><a href="own_' + row[0] + '">' + row[0] + "</a>"

        html = html + "<p><a href='criterium_vote'> " + self.get_fold_sign(self.folded["vote"]) \
               + " <b>Nach Berwertungen</b></a>"                                                     # VOTE # 
        if self.folded["vote"] == "is_open":
            self.cursor.execute("SELECT vote, COUNT(vote) FROM FILES GROUP BY vote ORDER BY vote DESC")
            cnt = 0
            for row in self.cursor.fetchall():
                if row[0] != None:
                    cnt = cnt + 1
                    html = html + '<br><a href="vote_' + str(row[0]) + '">' + str(row[0]) + " Sterne (" + str(row[1]) + ")</a>"
            html = html + '<br><a href="vote_NULL">Unbewertete (max. 100)</a>'

        name = ""
        for key in self.folded:                                                                     # TAG-criteria #
            if key in ("own", "vote"): continue
            if name == "Jahr": # last round was date, now draw a line
                html = html + "<hr>"
            name = self.names[key] if key in self.names else key
            ret = "<p><a href='criterium_" + key + "'> " + self.get_fold_sign(self.folded[key]) \
                  + " <b>" + name + "</b></a>"
            if self.folded[key] == "is_open":
                self.cursor.execute("SELECT tag_value, COUNT(*) FROM TAGS WHERE tag_key = '" + key + \
                                    "' GROUP BY tag_value ORDER BY tag_value")
                for row in self.cursor.fetchall():
                    ret = ret + '<br><a href="' + key + '_' + row[0] + '">' + row[0] + " (" + str(row[1]) + ")</a>"
                num = self.get_count_unassigned(key)
                ret = ret + '<br><a href="' + key + '_NULL">Ohne Zuordnung (max. 100 von ' + str(num) + ')</a>'
            html = html + ret

        html = html + "</body></html>"                         # Page Extro #
        return html
    def get_own_lists(self):
        self.cursor.execute("SELECT name FROM LISTS ORDER BY name") 
        ret = [""]
        for row in self.cursor.fetchall():
            ret.append(row[0])
        return ret
    def get_tags_of_file(self, file_id):
        self.cursor.execute("SELECT tag_key, tag_value FROM TAGS WHERE file_id = '" + str(file_id) + "'") 
        return self.cursor.fetchall()
    def init_folded(self):
        # Default Criteria #
        folded = {"own":"is_folded", "vote":"is_open", "genre":"is_folded", "album":"is_folded", 
                  "artist":"is_folded", "language":"is_folded", "date":"is_folded"}
        # Individual or tag-depending Criteria #
        self.cursor.execute("SELECT tag_key FROM TAGS GROUP BY tag_key ORDER BY tag_key")
        for row in self.cursor.fetchall():
            if row[0] not in (None, "genre", "album", "artist", "language", "title", "tracknumber", "date"):
                folded[row[0]] = "is_folded"
        return folded
    def list_entries_in_db_without_file(self):
        self.cursor.execute("SELECT id, file_path, file_name FROM FILES")
        for row in self.cursor.fetchall():
            filename_long = row[1] + os.sep + row[2]
            if not os.path.exists(filename_long):
                print(filename_long)
                self.delete_song_in_db(row[0])
    def scan_files(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Bitte einen Startordner auswählen",
            "",
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )

        if not os.path.isdir(directory):
            print("Das Verzeichnis existiert nicht >> Abbruch")
            return
        
        for path, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(".mp3"):
                    filename_long = os.path.join(path, file)
                    print(f"Verarbeite: {filename_long}")

                    # Check, if file already processed #
                    with_apostroph = path.find("'") > -1 or file.find("'") > -1 
                    if with_apostroph:
                        self.cursor.execute('SELECT COUNT(*) FROM FILES WHERE file_path = "' + path + '" AND file_name = "' + file + '"')
                    else:
                        self.cursor.execute("SELECT COUNT(*) FROM FILES WHERE file_path = '" + path + "' AND file_name = '" + file + "'")
                    exists = self.cursor.fetchone()[0] > 0
                    if exists:
                        print("⚠️  Datei bereits gelesen >> kein Neuscan")
                        continue

                    # Store Data in FILES-Table #
                    if with_apostroph:
                        self.cursor.execute('INSERT INTO FILES (file_path, file_name) VALUES ("' + path + '", "' + file + '")')
                    else:
                        self.cursor.execute("INSERT INTO FILES (file_path, file_name) VALUES ('" + path + "', '" + file + "')")
                    file_id = self.cursor.lastrowid

                    # Read Metadata and store in TAGS-Table #
                    try:
                        audio = EasyID3(filename_long)
                        for key, value in audio.items():
                            if key == "genre":
                                continue
                            self.cursor.execute("""INSERT INTO TAGS (file_id, tag_key, tag_value) VALUES (?, ?, ?)""",
                                (file_id, key, ", ".join(value)))
                    except MutagenError:
                        print(f"⚠️  Keine ID3-Tags lesbar: {filename_long}")
                    except Exception as e:
                        print(f"⚠️  Fehler bei {filename_long}: {e}")

                    self.conn.commit()
    def set_tag(self, file_id, cnt, value, tags):
        self.cursor.execute('SELECT id FROM TAGS WHERE file_id = "' + str(file_id) + '" AND tag_key = "' + tags[cnt] + '"') 
        rows = self.cursor.fetchall()
        if len(rows) > 0:  # entry exists => UPDATE
            self.cursor.execute('UPDATE TAGS SET tag_value = "' + value + '" WHERE id = ' + str(rows[0][0]))
        else:              # no entry so far => INSERT
            query = 'INSERT INTO TAGS (file_id, tag_key, tag_value) VALUES ("' + str(file_id) \
                + '", "' + tags[cnt] + '", "' + value + '")'
            self.cursor.execute(query)  
        self.conn.commit()
    def set_vote(self, file_id, vote):
        self.cursor.execute("UPDATE FILES SET vote='" + str(vote) + "' WHERE id = '" + str(file_id) + "'") 
        self.conn.commit()
    def toggle_fold(self, listname):
        if self.folded[listname] == "is_folded":
            self.folded[listname] = "is_open"
        else:
            self.folded[listname] = "is_folded"
