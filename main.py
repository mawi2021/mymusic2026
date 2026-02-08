import sys
from PyQt6.QtWidgets      import QApplication, QMainWindow, QStyleFactory, QTableWidgetItem
from classes.MainWidget   import MainWidget, MainWindowMenu
from classes.Db           import Db

# NEXT:
# - Kriterium: Anker in der Seite bei jedem Kriterium, dass beim Folding nicht immemr oben startet

# ToDo:
# - Kriterium: Eigene Listen füllen (wie?)
# - Kriterium: Suche
# - Kriterium: Checkboxen bei den (ausgeklappten) Kriterien
# - Tabelle: Anzeige, was man ausgewählt hat (Welche Liste)
# - Tabelle: Massenänderungen
# - Buttons: Muten / unmuten + Zustand speichern und mit Icon kenntlich machen
# - Buttons: Zufällige Reihenfolge + Zustand speichern und mit Icon kenntlich machen
# - Buttons: Endlosschleife + Zustand speichern und mit Icon kenntlich machen
# - Details: in änderbaren Feldern Tags in MP3-Datei wegschreiben
# - Details: Bei Änderungen an Genres Speichern in DB
# - Details: Eigene Tags erstellen, vorhandene Tags ändern, die nur in "Weitere" enthalten sind
# - Details: Sprache-Widget Schrift teilweise weiß
# - Details: Eigenen Kommentar schreiben
# - Datenbank: Verschieben und Umbenennen von Ordnern mit Datenbank synchronisieren
# - Datenbank: Backup erstellen
# - Datenbank: Tags aus der Datenbank in Datei schreiben
# - Konfiguration: Auswahl, aktuelles Lied und self.folded für nächsten Start speichern
# - Konfiguration: An- und Abschalten, Infos aus dem Web zu holen (Zeitfresser)

class Main(QMainWindow):

    def __init__(self, parent=None):
        super(Main, self).__init__(parent)
        self.db        = Db(self)
        self.widget    = MainWidget(self, self.db)
        self.menu      = MainWindowMenu(self, self.db)

        self.setCentralWidget(self.widget)
        self.setMenuBar(self.menu)
        self.setWindowTitle("MyMusic")  
        self.setGeometry(200, 40, 1500, 800)

        self.update_criteria()

    def set_internet_properties(self):
        pass
    def update_criteria(self):
        html = self.db.get_html()
        self.widget.set_criteria_html(html)

def main():
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    ex = Main()
    ex.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()


# Icons: 
# Place the attribution on the app's credits page and on the description page on the app store.
# <a href="https://www.flaticon.com/free-icons/backward" title="backward icons">Backward icons created by riajulislam - Flaticon</a>
# e.g. https://cdn-icons-png.flaticon.com/128/14458/14458360.png
# https://www.flaticon.com/de/kostenloses-icon/star_3675298 => Star for voting (filled)
# https://www.flaticon.com/de/packs/hardware-18080019 => Sammlung hardware von riajulislam
#   https://cdn-icons-png.flaticon.com/128/18080/18080114.png => first (orange)
#   https://cdn-icons-png.flaticon.com/128/18080/18080164.png => back (orange)
#   https://cdn-icons-png.flaticon.com/128/18080/18080252.png => next (orange)
#   https://cdn-icons-png.flaticon.com/128/18080/18080119.png => last (orange)
# https://www.flaticon.com/de/packs/web-user-interface-17878514 => collection Web user interface from riajulislam
#   https://cdn-icons-png.flaticon.com/128/17878/17878541.png => play (pink)
#   https://cdn-icons-png.flaticon.com/128/17878/17878655.png => repeat (pink)
#   https://cdn-icons-png.flaticon.com/128/17878/17878991.png => pause (blue)
#   https://cdn-icons-png.flaticon.com/128/17878/17878568.png => volume (blue)
# https://www.flaticon.com/de/packs/music-and-instruments-14457980 => collection Music from riajulislam
#   https://cdn-icons-png.flaticon.com/128/14458/14458352.png => rotate (yellow)
#   https://cdn-icons-png.flaticon.com/128/14458/14458344.png => rotate (pink)
# https://cdn-icons-png.flaticon.com/128/18210/18210344.png => Shuffle
# https://cdn-icons-png.flaticon.com/128/149/149222.png => Star for voting (not filled)

