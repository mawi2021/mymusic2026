import os
from functools            import partial
from PyQt6                import QtWidgets
from PyQt6.QtCore         import Qt, QUrl, QSize
from PyQt6.QtGui          import QAction, QIcon
from PyQt6.QtMultimedia   import QMediaPlayer, QAudioOutput
from PyQt6.QtWidgets      import QWidget, QHBoxLayout, QSplitter, QTableWidget, QMenuBar, QPushButton, \
                                 QTextBrowser, QTableWidgetItem, QAbstractItemView, QVBoxLayout, \
                                 QScrollArea, QFormLayout, QLabel, QLineEdit, QTextEdit, QComboBox, \
                                 QSlider

class MainWidget(QWidget):
    def __init__(self, main, db):
        super().__init__()
        self.main           = main
        self.db             = db
        self.criteria       = QTextBrowser()
        self.table          = QTableWidget()
        self.details        = QScrollArea()
        self.buttons        = QWidget()
        self.slider         = QSlider(Qt.Orientation.Horizontal)
        self.slider_label   = QLabel("--:--")
        self.combo_own      = None

        self.player         = QMediaPlayer()
        self.audio          = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.player.mediaStatusChanged.connect(self.on_song_finished)
        self.slider_is_user_dragging = False
        self.play_artist_title = ""

        self.detail_values  = {}
        self.detail_widgets = []
        self.detail_fields  = ["file_id", "filename_long", "dauer", "tracknumber", "album", "artist", 
                              "title", "date", "genre", "language", "others"]
        self.languages      = ["", "Englisch", "Deutsch", "Französisch", "Italienisch", "Latein", "Spanisch", "Yolngu", "Andere Sprache"]
        self.vote_list      = []
        self.init_UI()

    def calc_time(self, ms):
        dauer = int(ms/1000)
        sec = str(dauer % 60)
        return str(int(dauer/60)) + ":" + str(sec.zfill(2))
    def create_button(self, filename, action, size=64):
        btn = QPushButton()
        btn.setIcon(QIcon("icons" + os.sep + filename)) 
        btn.clicked.connect(action)
        btn.setFixedSize(size, size)
        btn.setIconSize(QSize(size, size))
        return btn
    def fill_details(self):
        for i in range(0, 5):
            if i < self.detail_values["vote"]:
                self.vote_list[i].setIcon(QIcon("icons" + os.sep + "star2.png"))
            else:
                self.vote_list[i].setIcon(QIcon("icons" + os.sep + "star3.png"))

        self.detail_widgets[0].setText(self.detail_values["file_id"])
        self.detail_widgets[1].setText(self.detail_values["filename_long"])
        self.detail_widgets[2].setText(self.detail_values["dauer"])
        self.detail_widgets[3].setText(self.detail_values["tracknumber"])
        self.detail_widgets[4].setText(self.detail_values["album"])
        self.detail_widgets[5].setText(self.detail_values["artist"])
        self.detail_widgets[6].setText(self.detail_values["title"])
        self.detail_widgets[7].setText(self.detail_values["date"])
        self.detail_widgets[8].setText(self.detail_values["genre"])

        self.detail_widgets[9].setCurrentIndex(self.languages.index(self.detail_values["language"]))
        self.detail_widgets[10].setPlainText(self.detail_values["others"])
    def fill_table_lines(self, arr):
        self.table.clearContents()
        self.table.setRowCount(len(arr))
        cnt = -1
        for row in arr:
            cnt = cnt + 1
            file_id = row[0]
            self.table.setItem(cnt, 6, QTableWidgetItem(str(file_id)))

            tags = self.db.get_tags_of_file(file_id)
            for line in tags:
                if line[0] == "tracknumber":
                    self.table.setItem(cnt, 1, QTableWidgetItem(line[1]))
                elif line[0] == "album":
                    self.table.setItem(cnt, 0, QTableWidgetItem(line[1]))
                elif line[0] == "artist":
                    self.table.setItem(cnt, 2, QTableWidgetItem(line[1]))
                elif line[0] == "title":
                    self.table.setItem(cnt, 3, QTableWidgetItem(line[1]))
                elif line[0] == "date":
                    self.table.setItem(cnt, 4, QTableWidgetItem(line[1]))
                elif line[0] == "genre":
                    self.table.setItem(cnt, 5, QTableWidgetItem(line[1]))
                
        self.table.resizeColumnsToContents()      
    def init_UI(self):
        # Create parts of the page #
        self.init_UI_buttons()
        self.init_UI_criteria()
        self.init_UI_details()
        self.init_UI_table()

        # Splitter C ↔ D (horizontal)
        CDSplit = QSplitter(Qt.Orientation.Horizontal)
        CDSplit.addWidget(self.table)
        CDSplit.addWidget(self.details)
        CDSplit.setSizes([80, 40])     # Startgrößen C/D

        # Splitter B ↔ (C+D) (vertical)
        BSplit = QSplitter(Qt.Orientation.Vertical)
        BSplit.addWidget(self.buttons)
        BSplit.addWidget(CDSplit)
        BSplit.setSizes([80, 500])       # B 80px, Rest C+D

        # Splitter A ↔ (B + C + D) (horizontal)
        MainSplit = QSplitter(Qt.Orientation.Horizontal)
        MainSplit.addWidget(self.criteria)
        MainSplit.addWidget(BSplit)
        MainSplit.setSizes([240, 1000])   # A 100px, Rest rechts

        # Gesamtlayout
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(MainSplit)      
        self.setLayout(self.layout)

        self.setStyleSheet("""
            QPushButton {
                margin:  0;
                padding: 0;
                border:  0; 
            }
        """)
    def init_UI_buttons(self):          # Top: Buttons #
        self.buttons.setFixedHeight(75)       # feste Starthöhe
        btn_layout = QHBoxLayout(self.buttons)
        btn_layout.addWidget(self.create_button("first7.png", self.on_first))
        btn_layout.addWidget(self.create_button("back7.png", self.on_back))
        btn_layout.addWidget(self.create_button("play9.png", self.on_play))
        btn_layout.addWidget(self.create_button("pause7.png", self.on_pause))
        btn_layout.addWidget(self.create_button("stop7.png", self.on_stop))
        btn_layout.addWidget(self.create_button("next7.png", self.on_next))
        btn_layout.addWidget(self.create_button("last7.png", self.on_last))

        btn_layout.addStretch(1)

        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setValue(50)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(10)
        self.slider.setSingleStep(1000)  # 1s in ms
        self.slider.valueChanged.connect(self.on_slider_change)       
        self.slider.sliderMoved.connect(self.on_slider_moved)
        self.slider.sliderPressed.connect(self.on_slider_pressed)
        self.slider.sliderReleased.connect(self.on_slider_released)
        btn_layout.addWidget(self.slider_label)
        btn_layout.addWidget(self.slider)

        btn_layout.addStretch(1)

        btn_layout.addWidget(self.create_button("rotate8.png", self.on_rotate))    
        btn_layout.addWidget(self.create_button("shuffle10.png", self.on_shuffle))       
        btn_layout.addWidget(self.create_button("volume5.png", self.on_mute))       

        self.player.durationChanged.connect(self.on_player_duration_changed)
        self.player.positionChanged.connect(self.on_player_position_changed)
        # self.player.mediaStatusChanged.connect(self.on_player_media_status)
        # self.player.playbackStateChanged.connect(self.on_player_playback_state)
        # self.player.errorOccurred.connect(self.on_player_error)

        self.buttons.setStyleSheet("""
            background-color: #e5ffe3;
            padding:          0px;
            margin:           0px;
        """)
    def init_UI_criteria(self):         # Left: Lists #
        self.criteria.setOpenLinks(False)
        self.criteria.anchorClicked.connect(self.on_criteria_clicked)
        self.criteria.setMinimumWidth(240)       # feste Startbreite 
        self.criteria.document().setBaseUrl(QUrl.fromLocalFile(os.getcwd() + os.sep))
        # Styles
        self.criteria.setStyleSheet("background: #a1fc9a;")
        self.criteria.document().setDefaultStyleSheet("a { color: #000; text-decoration: none; }")
    def init_UI_details(self):          # Rechts: Formular mit Details #
        self.details.setWidgetResizable(True)
        content = QWidget()
        form_layout = QFormLayout(content)
        form_layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # First row: stars for voting and DropDown for own lists #
        btn_layout = QHBoxLayout()
        # btn_layout.addStretch(1)
        for i in range(1, 6):
            btn = self.create_button("star3.png", partial(self.on_vote, i), 32)
            self.vote_list.append(btn)
            btn_layout.addWidget(btn)
        btn_layout.addStretch(1)

        self.combo_own = QComboBox()
        own_lists = self.db.get_own_lists()
        self.combo_own.addItems(own_lists)
        self.combo_own.currentTextChanged.connect(self.db.add_song_to_list)
        btn_layout.addWidget(QLabel("Füge Lied zur Liste hinzu"))
        btn_layout.addWidget(self.combo_own)

        form_layout.addRow(btn_layout)

        # Other rows #
        labels = ["ID", "Pfad und Dateiname", "Dauer", "Nummer im Album", "Album", "Artist", 
                  "Titel", "Jahr", "Genre", "Sprache"]
        cnt = -1
        for text in labels: # create fields
            cnt = cnt + 1

            # Label (clickable!)
            label = QLabel('<a href="action:listsame_' + str(cnt) + '" style="color:#000;text-decoration:none;">' + text + ":</a>")
            label.setOpenExternalLinks(False)  # wir fangen das selbst ab
            label.linkActivated.connect(self.on_label_clicked)

            if cnt in (0, 1, 2):
                self.detail_widgets.append(QLabel())
                self.detail_widgets[cnt].setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            elif cnt == 9:
                combo = QComboBox()
                combo.addItems(self.languages)
                combo.currentTextChanged.connect(self.on_language_change)
                self.detail_widgets.append(combo)
            else:
                self.detail_widgets.append(QLineEdit())
                self.detail_widgets[cnt].editingFinished.connect(partial(self.on_field_change, cnt))
                if cnt in (5, 6):                 # Artist and Title in bold font  
                    font = self.detail_widgets[cnt].font()
                    font.setBold(True)
                    self.detail_widgets[cnt].setFont(font)
            form_layout.addRow(label, self.detail_widgets[cnt])

        label = QLabel("Weitere:")
        self.detail_widgets.append(QTextEdit())
        form_layout.addRow(label, self.detail_widgets[cnt+1])

        self.details.setWidget(content)
        self.details.setStyleSheet("background-color: #e5ffe3;")
    def init_UI_table(self):            # Center: Table #
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSortIndicatorShown( True )
        self.table.setRowCount(0)
        fields = ["Album", "Nummer", "Artist", "Titel", "Jahr", "Genre", "Datei ID"]
        self.table.setColumnCount(len(fields))
        cnt = 0
        for obj in fields:
            headerItem = QTableWidgetItem(obj)
            self.table.setHorizontalHeaderItem(cnt,headerItem)
            cnt += 1
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows) # selection of the whole line 
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # not editable
        self.table.cellClicked.connect(self.on_table_clicked)

        self.table.setStyleSheet("background-color: #e5ffe3;")
    def on_back(self):
        row = self.table.currentRow() - 1
        if row < 0:
            row == 0
        if self.table.rowCount() > row:
            self.table.selectRow(row)
            self.on_table_clicked(row, 0)
            self.on_play()
    def on_criteria_clicked(self, url):
        el_str = url.toString()
        section, listname = el_str.split("_", 2)
        if section == "criterium": 
            self.db.toggle_fold(listname)
            self.main.update_criteria()
        else:
            arr = self.db.get_file_ids_for_criteria(section, listname)
            self.fill_table_lines(arr)
    def on_field_change(self, cnt):
        if cnt == 8: # Genres
            return

        file_id   = self.detail_widgets[0].text()
        new_value = self.detail_widgets[cnt].text()
        old_value = self.detail_values[self.detail_fields[cnt]]

        if new_value != old_value:
            self.detail_values[self.detail_fields[cnt]] = new_value
            self.db.set_tag(file_id, cnt, new_value, self.detail_fields)
            self.update_table(file_id, cnt, new_value)
    def on_first(self):
        row = 0
        if self.table.rowCount() > row:
            self.table.selectRow(row)
            self.on_table_clicked(row, 0)
            self.on_play()
    def on_last(self):
        row = self.table.rowCount() - 1
        if row < 0:
            return
        self.table.selectRow(row)
        self.on_table_clicked(row, 0)
        self.on_play()
    def on_label_clicked(self, link):
        _, cnt = link.split("_", 2)
        field = self.detail_fields[int(cnt)]
        value = self.detail_values[field]
        obj = type("X", (), {})()  # Umweg über obj, damit obj.toString() den gebastelten String zurückgibt
        obj.toString = lambda: field + "_" + value
        self.on_criteria_clicked(obj)
    def on_language_change(self, new_value):
        file_id   = self.detail_widgets[0].text()
        old_value = self.detail_values["language"]

        if new_value != old_value:
            self.detail_values["language"] = new_value
            self.db.set_tag(file_id, 9, new_value, self.detail_fields)
    def on_mute(self):
        pass
    def on_next(self):
        row = self.table.currentRow() + 1
        if self.table.rowCount() > row:
            self.table.selectRow(row)
            self.on_table_clicked(row, 0)
            self.on_play()
    def on_pause(self):
        self.player.pause()
    def on_play(self):
        state = self.player.playbackState()
        if state == QMediaPlayer.PlaybackState.PausedState: # Comes from Pause
            self.player.play()
        else:
            row = self.table.currentRow()
            if row == -1:
                return
            filename = self.detail_widgets[1].text()
            self.slider_label.setText(self.detail_widgets[5].text() + " - " + self.detail_widgets[6].text())
            self.on_slider_change(0)
            self.play_artist_title = self.detail_values["artist"] + " - " + self.detail_values["title"] + " - "
            self.file_url = QUrl.fromLocalFile(filename)
            self.player.setSource(self.file_url)
            self.player.play()
    def on_player_duration_changed(self, duration_ms):
        self.slider.setRange(0, duration_ms if duration_ms > 0 else 0)
        self.slider_label.setText(self.play_artist_title + self.calc_time(duration_ms))
    def on_player_position_changed(self, value):
        if not self.slider_is_user_dragging:
            self.slider.setValue(value)
        self.slider_label.setText(self.play_artist_title + self.calc_time(value))
    def on_rotate(self):
        pass
    def on_shuffle(self):
        pass
    def on_slider_change(self, value):
        self.slider_label.setText(self.play_artist_title + self.calc_time(value))
    def on_slider_moved(self, value):
        self.slider_label.setText(self.play_artist_title + self.calc_time(value))
    def on_slider_pressed(self):
        self.slider_is_user_dragging = True
        value = self.slider.value()
        self.slider_label.setText(self.play_artist_title + self.calc_time(value))
    def on_slider_released(self):
        self.slider_is_user_dragging = False
        value = self.slider.value()
        self.slider_label.setText(self.play_artist_title + self.calc_time(value))
        self.player.setPosition(value)
    def on_song_finished(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.on_next()
    def on_stop(self):
        self.player.stop()
    def on_table_clicked(self, row, col):
        filename_long = ""
        try:
            item = self.table.item(row, 6)
            if item == None:
                return
            file_id = item.text()  # column with file_id
            filename_long, _ = self.db.get_filename(file_id)
            self.detail_values = self.db.get_details(file_id)
            self.fill_details()
        except Exception as e:
            print("ERROR in on_table_clicked()" + str(e) + " => " + filename_long)
    def on_vote(self, vote):
        self.db.set_vote(self.detail_widgets[0].text(), vote)

        for i in range(0, 5):
            if i < vote:
                self.vote_list[i].setIcon(QIcon("icons" + os.sep + "star2.png"))
            else:
                self.vote_list[i].setIcon(QIcon("icons" + os.sep + "star3.png"))
    def set_criteria_html(self, html):
        self.criteria.setHtml(html)
    def update_table(self, file_id, cnt, value):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 6)
            if item is not None and item.text() == str(file_id):
                # Get column number in table
                tags_detail = ["", "", "", "tracknumber", "album", "artist", "title", "date"]  # Position cnt in array
                tags_table  = {"album":0, "tracknumber":1, "artist":2, "title":3, "date":4, "genre":5, "file_id":6}
                word = tags_detail[cnt]
                col  = tags_table[word]
                self.table.setItem(row, col, QTableWidgetItem(value)) # Change table cell
                break

class MainWindowMenu(QMenuBar):
    def __init__(self, main, db):
        super().__init__()
        self.main = main
        self.db   = db

        # ----- D A T A B A S E ----------------------------------------------------------------- #
        self.db_menu = self.addMenu("Datenbank")

        self.db_read_files_action = QAction("Dateien einlesen", self)
        self.db_read_files_action.triggered.connect(self.db.scan_files)
        self.db_menu.addAction(self.db_read_files_action)

        self.db_duplicate_action = QAction("Lösche doppelte Einträge", self)
        self.db_duplicate_action.triggered.connect(self.db.delete_duplicate_entries_in_db)
        self.db_menu.addAction(self.db_duplicate_action)

        self.db_no_file_action = QAction("Lösche Einträge ohne Datei", self)
        self.db_no_file_action.triggered.connect(self.db.list_entries_in_db_without_file)
        self.db_menu.addAction(self.db_no_file_action)

        # ----- L I S T S ----------------------------------------------------------------------- #
        self.listMenu = self.addMenu("Listen")

        self.createListAction = QAction("Neu", self)
        self.createListAction.triggered.connect(self.db.create_list)
        self.listMenu.addAction(self.createListAction)

        # ----- V I E W ------------------------------------------------------------------------- #
        self.view_menu = self.addMenu("Ansicht")

        self.view_action = QAction("Aktulalisieren", self)
        self.view_action.triggered.connect(self.main.update_criteria)
        self.view_menu.addAction(self.view_action)

        # ----- P R O P E R T I E S ------------------------------------------------------------- #
        self.prop_menu = self.addMenu("Einstellungen")

        self.prop_www_action = QAction("Abfragen im Internet", self)
        self.prop_www_action.triggered.connect(self.main.set_internet_properties)
        self.prop_menu.addAction(self.prop_www_action)

        # Styles #
        self.setStyleSheet(
        """
            QMenuBar {
                background: #a1fc9a;
                font-size:   14px;
                font-weight: bold;
                min-height:  40px;
            }
            QMenuBar::item {
                color:       black;
            }
            QMenuBar::item:selected {      
                color:       orange;
            }
        """)
