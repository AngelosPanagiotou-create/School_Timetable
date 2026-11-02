# -*- coding: utf-8 -*-
"""Ωρολόγιο — έκδοση εφαρμογής (διπλό κλικ).
Ανοίγει το Ωρολόγιο.html σε δικό του παράθυρο, αποθηκεύει στα Έγγραφα\\Ωρολόγιο
και λύνει το πρόγραμμα με Google OR-Tools.
Την πρώτη φορά εγκαθιστά μόνο του τις βιβλιοθήκες που χρειάζεται."""
import json
import os
import subprocess
import sys
import threading

APP_DIR = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(APP_DIR, 'Ωρολόγιο.html')
VERSION = '2.2'
NEEDED = ['PySide6', 'ortools']


# ---------------------------------------------------------------- γλώσσα
def documents_dir():
    if os.name == 'nt':
        try:
            import ctypes
            buf = ctypes.create_unicode_buffer(260)
            if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf) == 0 and buf.value:
                return buf.value
        except Exception:
            pass
    return os.path.join(os.path.expanduser('~'), 'Documents')


LANG_FILE = os.path.join(documents_dir(), 'Ωρολόγιο', 'lang.txt')
LANGS = ('el', 'en', 'fr', 'de', 'es')


def saved_lang():
    try:
        with open(LANG_FILE, encoding='utf-8') as f:
            v = f.read().strip()
        return v if v in LANGS else None
    except Exception:
        return None


def system_lang():
    try:
        if os.name == 'nt':
            import ctypes
            prim = ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF
            return {0x08: 'el', 0x09: 'en', 0x0C: 'fr', 0x07: 'de', 0x0A: 'es'}.get(prim, 'en')
        import locale
        code = (locale.getlocale()[0] or 'en')[:2].lower()
        return code if code in LANGS else 'en'
    except Exception:
        return 'en'


LANG = saved_lang() or system_lang()
TXT = {
    'first_run': {'el': 'Ωρολόγιο — πρώτη εκκίνηση', 'en': 'Timetable — first start', 'fr': 'Emploi du temps — premier démarrage', 'de': 'Stundenplan — erster Start', 'es': 'Horario — primer inicio'},
    'installing': {'el': 'Εγκατάσταση όσων χρειάζεται η εφαρμογή (μόνο την πρώτη φορά).\nΜπορεί να πάρει μερικά λεπτά — χρειάζεται internet.',
                   'en': 'Installing what the app needs (first time only).\nIt may take a few minutes — internet is required.',
                   'fr': 'Installation de ce dont l’application a besoin (la première fois seulement).\nCela peut prendre quelques minutes — internet nécessaire.',
                   'de': 'Installation der benötigten Komponenten (nur beim ersten Mal).\nDas kann einige Minuten dauern — Internet erforderlich.',
                   'es': 'Instalando lo que necesita la aplicación (solo la primera vez).\nPuede tardar unos minutos; se necesita internet.'},
    'install_failed': {'el': 'Δεν ολοκληρώθηκε η εγκατάσταση.', 'en': 'The installation did not complete.', 'fr': 'L’installation n’a pas abouti.', 'de': 'Die Installation wurde nicht abgeschlossen.', 'es': 'La instalación no se completó.'},
    'try_browser': {'el': 'Έλεγξε τη σύνδεση στο internet και ξανατρέξε το Εκκίνηση.cmd.',
                    'en': 'Check your internet connection and run Start.cmd again.',
                    'fr': 'Vérifie ta connexion internet et relance Start.cmd.',
                    'de': 'Prüfe die Internetverbindung und starte Start.cmd erneut.',
                    'es': 'Comprueba la conexión a internet y vuelve a ejecutar Start.cmd.'},
    'read_fail': {'el': 'Δεν διαβάστηκε το αρχείο δεδομένων:', 'en': 'The data file could not be read:', 'fr': 'Le fichier de données n’a pas pu être lu :', 'de': 'Die Datendatei konnte nicht gelesen werden:', 'es': 'No se pudo leer el archivo de datos:'},
    'export': {'el': 'Εξαγωγή αντιγράφου', 'en': 'Export backup', 'fr': 'Exporter une sauvegarde', 'de': 'Sicherung exportieren', 'es': 'Exportar copia'},
    'import': {'el': 'Εισαγωγή από αρχείο', 'en': 'Import from file', 'fr': 'Importer depuis un fichier', 'de': 'Aus Datei importieren', 'es': 'Importar desde archivo'},
    'import_t': {'el': 'Εισαγωγή εκπαιδευτικών', 'en': 'Import teachers', 'fr': 'Importer des enseignants', 'de': 'Lehrkräfte importieren', 'es': 'Importar docentes'},
    'export_t': {'el': 'Εξαγωγή εκπαιδευτικών', 'en': 'Export teachers', 'fr': 'Exporter les enseignants', 'de': 'Lehrkräfte exportieren', 'es': 'Exportar docentes'},
    'mdtext': {'el': 'Markdown / κείμενο', 'en': 'Markdown / text', 'fr': 'Markdown / texte', 'de': 'Markdown / Text', 'es': 'Markdown / texto'},
    'or_err': {'el': 'Σφάλμα OR-Tools: ', 'en': 'OR-Tools error: ', 'fr': 'Erreur OR-Tools : ', 'de': 'OR-Tools-Fehler: ', 'es': 'Error de OR-Tools: '},
    'pdf_fail': {'el': 'Δεν δημιουργήθηκε το PDF. Ίσως είναι ήδη ανοιχτό σε άλλο πρόγραμμα — κλείσ\' το και ξαναδοκίμασε.',
                 'en': 'The PDF was not created. It may already be open in another program — close it and try again.',
                 'fr': 'Le PDF n’a pas été créé. Il est peut-être ouvert dans un autre programme — ferme-le et réessaie.',
                 'de': 'Das PDF wurde nicht erstellt. Vielleicht ist es in einem anderen Programm geöffnet — schließe es und versuche es erneut.',
                 'es': 'No se creó el PDF. Puede que esté abierto en otro programa: ciérralo y vuelve a intentarlo.'},
    'unsaved': {'el': 'Υπάρχουν αλλαγές που δεν αποθηκεύτηκαν («{0}»).', 'en': 'There are unsaved changes (“{0}”).', 'fr': 'Il y a des modifications non enregistrées (« {0} »).', 'de': 'Es gibt ungespeicherte Änderungen („{0}“).', 'es': 'Hay cambios sin guardar («{0}»).'},
    'save': {'el': 'Αποθήκευση', 'en': 'Save', 'fr': 'Enregistrer', 'de': 'Speichern', 'es': 'Guardar'},
    'nosave': {'el': 'Χωρίς αποθήκευση', 'en': 'Don’t save', 'fr': 'Ne pas enregistrer', 'de': 'Nicht speichern', 'es': 'No guardar'},
    'cancel': {'el': 'Άκυρο', 'en': 'Cancel', 'fr': 'Annuler', 'de': 'Abbrechen', 'es': 'Cancelar'},
    'no_html': {'el': 'Λείπει το αρχείο Ωρολόγιο.html.\nΠρέπει να βρίσκεται στον ίδιο φάκελο με το Ωρολόγιο.pyw.',
                'en': 'The file Ωρολόγιο.html is missing.\nIt must be in the same folder as Ωρολόγιο.pyw.',
                'fr': 'Le fichier Ωρολόγιο.html est manquant.\nIl doit être dans le même dossier que Ωρολόγιο.pyw.',
                'de': 'Die Datei Ωρολόγιο.html fehlt.\nSie muss im selben Ordner wie Ωρολόγιο.pyw liegen.',
                'es': 'Falta el archivo Ωρολόγιο.html.\nDebe estar en la misma carpeta que Ωρολόγιο.pyw.'},
    'app': {'el': 'Ωρολόγιο', 'en': 'Timetable', 'fr': 'Emploi du temps', 'de': 'Stundenplan', 'es': 'Horario'},
}


def tr(key, *args):
    m = TXT[key]
    s = m.get(LANG) or m['el']
    for i, a in enumerate(args):
        s = s.replace('{' + str(i) + '}', str(a))
    return s


# ---------------------------------------------------------------- εγκατάσταση
def missing_packages():
    miss = []
    try:
        import PySide6.QtWebEngineWidgets  # noqa: F401
        import PySide6.QtWebChannel  # noqa: F401
    except Exception:
        miss.append('PySide6')
    try:
        import ortools.sat.python.cp_model  # noqa: F401
    except Exception:
        miss.append('ortools')
    return miss


def console_python():
    exe = sys.executable
    base = os.path.basename(exe).lower()
    if base == 'pythonw.exe':
        cand = os.path.join(os.path.dirname(exe), 'python.exe')
        if os.path.exists(cand):
            return cand
    return exe


def pip_install(packages, on_line=None):
    flags = 0x08000000 if os.name == 'nt' else 0  # χωρίς μαύρο παράθυρο
    cmd = [console_python(), '-m', 'pip', 'install', '--user', '--upgrade', '--disable-pip-version-check'] + packages
    tail = []
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', creationflags=flags)
        for line in p.stdout:
            line = line.strip()
            if line:
                tail = (tail + [line])[-6:]
                if on_line:
                    on_line(line)
        p.wait()
        return {'ok': p.returncode == 0, 'err': '\n'.join(tail)}
    except Exception as e:
        return {'ok': False, 'err': str(e)}


def install_window(packages):
    """Μικρό παράθυρο που εγκαθιστά τις βιβλιοθήκες (tkinter· αν λείπει, εγκαθιστά χωρίς παράθυρο)."""
    try:
        import tkinter as tk
        from tkinter import ttk
    except Exception:
        return pip_install(packages)
    root = tk.Tk()
    root.title(tr('first_run'))
    root.geometry('560x260')
    root.configure(bg='#F4F1E8')
    root.resizable(False, False)
    tk.Label(root, text=tr('app'), font=('Palatino Linotype', 24), bg='#F4F1E8', fg='#1B2340').pack(pady=(22, 2))
    msg = tk.StringVar(value=tr('installing'))
    tk.Label(root, textvariable=msg, font=('Segoe UI', 10), bg='#F4F1E8', fg='#1B2340', justify='center').pack(pady=6)
    bar = ttk.Progressbar(root, mode='indeterminate', length=440)
    bar.pack(pady=10)
    bar.start(12)
    detail = tk.StringVar(value='')
    tk.Label(root, textvariable=detail, font=('Segoe UI', 8), bg='#F4F1E8', fg='#6A6F80', wraplength=520).pack()
    result = {'ok': False, 'err': ''}

    def work():
        result.update(pip_install(packages, lambda line: detail.set(line[:110])))
        root.after(0, root.destroy)

    threading.Thread(target=work, daemon=True).start()
    root.mainloop()
    return result


def show_error(title, text):
    try:
        import tkinter as tk
        from tkinter import messagebox
        r = tk.Tk()
        r.withdraw()
        messagebox.showerror(title, text)
        r.destroy()
    except Exception:
        pass


def bootstrap():
    miss = missing_packages()
    if not miss:
        return True
    res = install_window(miss)
    still = missing_packages()
    if 'PySide6' in still:
        show_error(tr('app'), tr('install_failed') + '\n\n' + (res.get('err') or '') + '\n\n' + tr('try_browser'))
        return False
    # ξαναξεκινά καθαρά, ώστε να φορτωθούν οι νέες βιβλιοθήκες
    subprocess.Popen([sys.executable, os.path.abspath(__file__)], cwd=APP_DIR)
    return False


# ---------------------------------------------------------------- εφαρμογή
def run_app():
    from PySide6.QtCore import QObject, Signal, Slot, QUrl, QFile, QIODevice, QStandardPaths, QMarginsF, QSize, Qt, QTimer
    from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QPageLayout, QPageSize, QDesktopServices
    from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEngineScript, QWebEngineSettings, QWebEnginePage
    from PySide6.QtWebChannel import QWebChannel

    try:
        sys.path.insert(0, APP_DIR)
        import orologio_cpsat
        has_ortools = True
    except Exception:
        orologio_cpsat = None
        has_ortools = False

    docs = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation) or os.path.expanduser('~')
    data_dir = os.path.join(docs, 'Ωρολόγιο')          # κοινός φάκελος της εφαρμογής
    schools_root = os.path.join(data_dir, 'σχολεία')    # ένας υποφάκελος ανά σχολείο
    registry = os.path.join(data_dir, 'σχολεία.json')   # λίστα σχολείων + ποιο είναι ανοιχτό
    os.makedirs(schools_root, exist_ok=True)
    CUR = {'id': None}

    def adopt_legacy():
        # Παλιές εκδόσεις (ένα σχολείο): Έγγραφα\Ωρολόγιο\data.json → γίνεται το πρώτο σχολείο της λίστας.
        # Τα παλιά αρχεία ΔΕΝ σβήνονται· αντιγράφονται στον φάκελο του σχολείου.
        old = os.path.join(data_dir, 'data.json')
        if os.path.exists(registry) or not os.path.exists(old):
            return
        try:
            import shutil
            with open(old, encoding='utf-8') as f:
                d = json.load(f)
            name = ((d.get('school') or {}).get('name') or '').strip() or 'Σχολείο'
            sid = 's_old'
            dst = os.path.join(schools_root, sid)
            os.makedirs(dst, exist_ok=True)
            shutil.copy2(old, os.path.join(dst, 'data.json'))
            for sub in ('αντίγραφα', 'εκτυπώσεις'):
                src = os.path.join(data_dir, sub)
                if os.path.isdir(src) and not os.path.exists(os.path.join(dst, sub)):
                    shutil.copytree(src, os.path.join(dst, sub))
            with open(registry, 'w', encoding='utf-8') as f:
                json.dump({'list': [{'id': sid, 'name': name}], 'cur': sid}, f, ensure_ascii=False, indent=1)
        except Exception:
            pass

    adopt_legacy()

    def school_dir(sid=None):
        d = os.path.join(schools_root, sid or CUR['id'] or '_')
        os.makedirs(d, exist_ok=True)
        return d

    def data_file():
        return os.path.join(school_dir(), 'data.json')

    def read_registry():
        try:
            with open(registry, encoding='utf-8') as f:
                r = json.load(f)
            if isinstance(r, dict) and isinstance(r.get('list'), list):
                return r
        except Exception:
            pass
        return {'list': [], 'cur': None}

    def write_atomic(path, text):
        tmp = path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(text)
        os.replace(tmp, path)

    def make_icon():
        pm = QPixmap(256, 256)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor('#1B2340'))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 0, 256, 256, 56, 56)
        p.setBrush(QColor('#1E5B4F'))
        p.drawRect(110, 134, 36, 28)
        pen = QPen(QColor('#F4F1E8'))
        pen.setWidth(12)
        p.setPen(pen)
        for y in (88, 128, 168):
            p.drawLine(56, y, 200, y)
        for x in (104, 152):
            p.drawLine(x, 56, x, 200)
        p.end()
        return pm

    class Bridge(QObject):
        solveProgress = Signal(str)
        solveDone = Signal(str)

        def __init__(self, win):
            super().__init__()
            self.win = win
            self._stop = False

        @Slot(result=str)
        def info(self):
            return json.dumps({'dataPath': data_dir, 'ortools': has_ortools, 'version': VERSION})

        # ---- σχολεία: το καθένα με τα δικά του δεδομένα, αντίγραφα και εκτυπώσεις
        @Slot(result=str)
        def schools(self):
            return json.dumps(read_registry())

        @Slot(str, result=str)
        def saveSchools(self, text):
            try:
                r = json.loads(text)
                write_atomic(registry, json.dumps(r, ensure_ascii=False, indent=1))
                CUR['id'] = r.get('cur') or CUR['id']
                return 'ok'
            except Exception as e:
                return str(e)

        @Slot(str, result=str)
        def setLang(self, code):
            global LANG
            try:
                if code in LANGS:
                    os.makedirs(os.path.dirname(LANG_FILE), exist_ok=True)
                    with open(LANG_FILE, 'w', encoding='utf-8') as f:
                        f.write(code)
                    LANG = code
                    self.win.set_lang_script()
                return 'ok'
            except Exception as e:
                return str(e)

        @Slot(str, result=str)
        def setCurrent(self, sid):
            CUR['id'] = sid
            school_dir()
            return 'ok'

        @Slot(str, result=str)
        def deleteSchool(self, sid):
            try:
                import shutil
                import datetime
                src = os.path.join(schools_root, sid)
                if os.path.isdir(src):
                    trash = os.path.join(data_dir, 'διαγραμμένα σχολεία')
                    os.makedirs(trash, exist_ok=True)
                    shutil.move(src, os.path.join(trash, sid + ' ' + datetime.datetime.now().strftime('%Y-%m-%d %H.%M.%S')))
                return 'ok'
            except Exception as e:
                return str(e)

        @Slot(result=str)
        def loadData(self):
            try:
                with open(data_file(), encoding='utf-8') as f:
                    return f.read()
            except FileNotFoundError:
                return ''
            except Exception as e:
                QMessageBox.warning(self.win, tr('app'), tr('read_fail') + f'\n{e}')
                return ''

        @Slot(str, result=str)
        def saveData(self, text):
            try:
                json.loads(text)
                write_atomic(data_file(), text)
                return 'ok'
            except Exception as e:
                return str(e)

        @Slot(str, str, result=str)
        def backup(self, text, name):
            try:
                safe = ''.join(ch for ch in name if ch not in '\\/:*?"<>|')
                backup_dir = os.path.join(school_dir(), 'αντίγραφα')
                os.makedirs(backup_dir, exist_ok=True)
                write_atomic(os.path.join(backup_dir, safe), text)
                files = sorted(f for f in os.listdir(backup_dir) if f.endswith('.json'))
                for old in files[:-60]:
                    os.remove(os.path.join(backup_dir, old))
                return 'ok'
            except Exception as e:
                return str(e)

        @Slot(str, str, result=str)
        def exportFile(self, text, name):
            path, _ = QFileDialog.getSaveFileName(self.win, tr('export'), os.path.join(docs, name), tr('app') + ' (*.json)')
            if not path:
                return ''
            write_atomic(path, text)
            return path

        @Slot(result=str)
        def importFile(self):
            path, _ = QFileDialog.getOpenFileName(self.win, tr('import'), docs, tr('app') + ' (*.json)')
            if not path:
                return ''
            with open(path, encoding='utf-8') as f:
                return f.read()

        @Slot(result=str)
        def openText(self):
            path, _ = QFileDialog.getOpenFileName(self.win, tr('import_t'), docs, tr('mdtext') + ' (*.md *.txt)')
            if not path:
                return ''
            with open(path, 'rb') as f:
                raw = f.read()
            for enc in ('utf-8-sig', 'cp1253', 'latin-1'):
                try:
                    return raw.decode(enc)
                except UnicodeDecodeError:
                    continue
            return ''

        @Slot(str, str, result=str)
        def saveText(self, text, name):
            path, _ = QFileDialog.getSaveFileName(self.win, tr('export_t'), os.path.join(docs, name), 'Markdown (*.md)')
            if not path:
                return ''
            write_atomic(path, text)
            return path

        @Slot()
        def openDataFolder(self):
            QDesktopServices.openUrl(QUrl.fromLocalFile(school_dir()))

        @Slot(result=str)
        def printPdf(self):
            # κάθε εκτύπωση κρατιέται: Έγγραφα\Ωρολόγιο\εκτυπώσεις\Ωρολόγιο 2026-11-01 13.20.05.pdf
            import datetime
            prints_dir = os.path.join(school_dir(), 'εκτυπώσεις')
            os.makedirs(prints_dir, exist_ok=True)
            out = os.path.join(prints_dir, 'Ωρολόγιο ' + datetime.datetime.now().strftime('%Y-%m-%d %H.%M.%S') + '.pdf')
            layout = QPageLayout(QPageSize(QPageSize.A4), QPageLayout.Landscape, QMarginsF(0, 0, 0, 0), QPageLayout.Millimeter)
            self.win.pending_pdf = out
            self.win.view.page().printToPdf(out, layout)
            return out

        @Slot(str, int, bool)
        def solve(self, text, seconds, keep):
            self._stop = False
            data = json.loads(text)

            def work():
                try:
                    res = orologio_cpsat.solve(data, seconds=seconds, keep_placed=keep,
                                               progress=lambda p: self.solveProgress.emit(json.dumps(p)),
                                               stopper=lambda: self._stop)
                except Exception as e:
                    res = {'ok': False, 'message': tr('or_err') + str(e)}
                self.solveDone.emit(json.dumps(res))
            threading.Thread(target=work, daemon=True).start()

        @Slot()
        def stopSolve(self):
            self._stop = True
            s = getattr(orologio_cpsat.solve, 'current', None) if orologio_cpsat else None
            if s is not None:
                for name in ('stop_search', 'StopSearch'):
                    if hasattr(s, name):
                        try:
                            getattr(s, name)()
                        except Exception:
                            pass
                        break

    class Window(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle(tr('app'))
            self.setWindowIcon(QIcon(make_icon()))
            self.resize(QSize(1480, 940))
            self.view = QWebEngineView(self)
            self.setCentralWidget(self.view)
            self.pending_pdf = None
            self.closing_ok = False
            st = self.view.settings()
            st.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
            st.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, False)
            # qwebchannel.js πριν από τη σελίδα
            f = QFile(':/qtwebchannel/qwebchannel.js')
            if f.open(QIODevice.ReadOnly):
                src = bytes(f.readAll()).decode('utf-8')
                f.close()
                sc = QWebEngineScript()
                sc.setName('qwebchannel')
                sc.setSourceCode(src)
                sc.setInjectionPoint(QWebEngineScript.DocumentCreation)
                sc.setWorldId(QWebEngineScript.MainWorld)
                sc.setRunsOnSubFrames(False)
                self.view.page().scripts().insert(sc)
            self.lang_script = None
            self.set_lang_script()
            self.bridge = Bridge(self)
            self.channel = QWebChannel(self.view.page())
            self.channel.registerObject('native', self.bridge)
            self.view.page().setWebChannel(self.channel)
            self.view.page().pdfPrintingFinished.connect(self.pdf_done)
            self.view.load(QUrl.fromLocalFile(HTML))

        def set_lang_script(self):
            # η γλώσσα που διάλεξε ο χρήστης (lang.txt) περνά στη σελίδα πριν φορτωθεί
            scripts = self.view.page().scripts()
            if self.lang_script is not None:
                scripts.remove(self.lang_script)
                self.lang_script = None
            code = saved_lang()
            if not code:
                return
            sc = QWebEngineScript()
            sc.setName('orologio-lang')
            sc.setSourceCode('window.__LANG_INJ = ' + json.dumps(code) + ';')
            sc.setInjectionPoint(QWebEngineScript.DocumentCreation)
            sc.setWorldId(QWebEngineScript.MainWorld)
            sc.setRunsOnSubFrames(False)
            scripts.insert(sc)
            self.lang_script = sc

        def pdf_done(self, path, ok):
            if ok:
                QDesktopServices.openUrl(QUrl.fromLocalFile(path))
            else:
                QMessageBox.warning(self, tr('app'), tr('pdf_fail'))

        def closeEvent(self, ev):
            if self.closing_ok:
                ev.accept()
                return
            ev.ignore()
            if getattr(self, 'asked_drafts', False):
                return self._save_and_close()

            def pending(name):
                self.asked_drafts = True
                if not name:
                    return self._save_and_close()
                box = QMessageBox(self)
                box.setWindowTitle(tr('app'))
                box.setText(tr('unsaved', name))
                bs = box.addButton(tr('save'), QMessageBox.AcceptRole)
                bd = box.addButton(tr('nosave'), QMessageBox.DestructiveRole)
                box.addButton(tr('cancel'), QMessageBox.RejectRole)
                box.exec()
                if box.clickedButton() is bs:
                    self.view.page().runJavaScript('window.__orologio.saveDrafts()', 0, lambda ok: self._save_and_close() if ok else setattr(self, 'asked_drafts', False))
                elif box.clickedButton() is bd:
                    self._save_and_close()
                else:
                    self.asked_drafts = False
            self.view.page().runJavaScript('window.__orologio && window.__orologio.pending ? window.__orologio.pending() : ""', 0, pending)

        def _save_and_close(self):
            def got(text):
                try:
                    if text:
                        json.loads(text)
                        if CUR['id']:
                            write_atomic(data_file(), text)
                finally:
                    self.closing_ok = True
                    QTimer.singleShot(0, self.close)
            self.view.page().runJavaScript('window.__orologio ? JSON.stringify(window.__orologio.db, null, 1) : ""', 0, got)
            QTimer.singleShot(2500, lambda: (setattr(self, 'closing_ok', True), self.close()))

    def ensure_shortcut():
        if os.name != 'nt':
            return
        flag = os.path.join(data_dir, '.shortcut')
        if os.path.exists(flag):
            return
        try:
            ico = os.path.join(data_dir, 'Ωρολόγιο.ico')
            make_icon().save(ico, 'ICO')
            exe = sys.executable
            if os.path.basename(exe).lower() == 'python.exe':
                w = os.path.join(os.path.dirname(exe), 'pythonw.exe')
                if os.path.exists(w):
                    exe = w
            desktop = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
            lnk = os.path.join(desktop, 'Ωρολόγιο.lnk')
            me = os.path.abspath(__file__)

            def q(s):
                return "'" + s.replace("'", "''") + "'"
            ps = ('$s=(New-Object -ComObject WScript.Shell).CreateShortcut(' + q(lnk) + ');'
                  '$s.TargetPath=' + q(exe) + ';$s.Arguments=' + q('"' + me + '"') + ';'
                  '$s.WorkingDirectory=' + q(APP_DIR) + ';$s.IconLocation=' + q(ico) + ';$s.Description=' + q('Ωρολόγιο πρόγραμμα') + ';$s.Save()')
            subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps], creationflags=0x08000000, timeout=30)
            with open(flag, 'w') as f:
                f.write('1')
        except Exception:
            pass

    if os.name == 'nt':
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('Orologio.Timetable')
        except Exception:
            pass
    app = QApplication(sys.argv)
    app.setApplicationName('Ωρολόγιο')
    if not os.path.exists(HTML):
        QMessageBox.critical(None, tr('app'), tr('no_html'))
        return
    win = Window()
    win.showMaximized()
    ensure_shortcut()
    sys.exit(app.exec())


if __name__ == '__main__':
    if bootstrap():
        run_app()
