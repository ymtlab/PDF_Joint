# -*- coding: utf-8 -*-
import subprocess
import sys
import os
from mainwindow import Ui_MainWindow
from model import Model, Delegate
from item import Item
from PyQt5 import QtWidgets, QtCore
from pathlib import Path

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, app):
        super().__init__()
        
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.pdfunite_path = os.getcwd() + '/' + 'poppler-0.68.0/bin/pdfunite.exe'
        self.pdfinfo_path = os.getcwd() + '/' + 'poppler-0.68.0/bin/pdfinfo.exe'
        self.model = Model(self, Item(QtCore.QModelIndex()))
        self.model.insertColumns(0, ['Name', 'Page size', 'height', 'width'])
        self.ui.tableView.setModel(self.model)
        self.ui.tableView.setItemDelegate(Delegate())
        self.ui.tableView.setColumnWidth(1, 200)
        self.setAcceptDrops(True)

    def fileopen(self):
        filenames = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open PDF file', '', 'PDF File (*.pdf)')
        if not filenames[0]:
            return
        paths = [ Path(filename) for filename in filenames[0] ]
        self.pdfs_to_items(paths)

    def filesave(self):
        savefolder = QtWidgets.QFileDialog.getExistingDirectory(self, 'Open PDF file', '')
        if not savefolder:
            return
        items = self.model.root_item.children()
        sizes = set([item.data('Page size') for item in items])
        pdfs = { size:[] for size in sizes }
        for item in items:
            pdfs[item.data('Page size')].append( item.data('Path') )
        for n, key in enumerate(pdfs):
            cmd = [self.pdfunite_path]
            cmd.extend(pdfs[key])
            cmd.append(savefolder + '/' + str(n) + '.pdf')
            self.subprocess_popen(cmd)
    
    def clear_item(self):
        self.model.removeRows(0, self.model.rowCount())
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
    
    def dropEvent(self, event):
        event.accept()
        paths = [ Path(url.toLocalFile()) for url in event.mimeData().urls() ]
        self.pdfs_to_items(paths)

    def execContextMenu(self, point):
        self.menu = QtWidgets.QMenu(self)
        self.menu.addAction('Clear', self.clear_item)
        self.menu.exec( self.focusWidget().mapToGlobal(point) )
        
    def pdfs_to_items(self, pdf_paths):
        self.model.removeRows(0, self.model.rowCount())
        paths = [ Path(pdf_path) for pdf_path in pdf_paths ]
        self.model.insertRows(0, len(paths))
        for row, path in enumerate(paths):
            item = self.model.index( row, 0, QtCore.QModelIndex() ).internalPointer()
            stdout, stderr = self.subprocess_popen( [self.pdfinfo_path, str(path)] )
            if not stderr == '':
                continue
            lines = [ line.split(':') for line in stdout.splitlines() ]
            d = { line[0].strip() : line[1].strip() for line in lines }
            s = d['Page size'].split()
            d2 = { 'Name':str(path.name), 'Path':str(path), 'height':s[0], 'width':s[2] }
            d.update(d2)
            item.set_dict(d)

    def subprocess_popen(self, cmd):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        proc = subprocess.Popen(cmd, encoding='cp932', stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
        stdout, stderr = proc.communicate(timeout=50)
        self.ui.textBrowser.setText( ' '.join(cmd) + '\n' + stderr + '\n' + stdout + '\n' + self.ui.textBrowser.toPlainText() )
        return stdout, stderr

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(app)
    window.show()
    app.exec()
 
if __name__ == '__main__':
    main()
