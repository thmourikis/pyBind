import sys
import os
import stat
from tempfile import mkstemp
from shutil import move
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QMessageBox, QApplication, QDesktopWidget, QFileDialog

class MyWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        uic.loadUi('mainwindow.ui', self)
        self.initUI()

    def initUI(self):

        self.inputFile.clicked.connect(self.Browse)

        ## Set HLA alleles
        self.inputHLACategory.activated.connect(self.get_HLA_alleles)

        #self.inputHLAallele.itemSelectionChanged.connect(self.get_selected_alleles)
        self.runbtn.clicked.connect(self.runNetMHCpan)

    def runNetMHCpan(self):
        als = self.inputHLAallele.selectedItems()
        als = [x.text() for x in als]
        print(als)
        mers = self.inputMers.selectedItems()
        mers = [x.text() for x in mers]
        print(mers)
        seq = self.inputText.toPlainText()
        print(seq)

        ## Create all different peptides around mutations of interest
        #a = 'abcdefg'
        #b = [a[i:i + 3] for i in xrange(len(a) - 2)]


        ## After taking all parameters I need to update the configuration script of netMHCpan
        netConfigFile = os.getcwd() + "/resources/netMHCpan-3.0/netMHCpan"
        new_config = os.getcwd() + "/resources/netMHCpan-3.0/netMHCpan_new"

        if not os.path.exists(os.getcwd()+"/scratch"):
            os.makedirs(os.getcwd()+"/scratch")

        with open(new_config, 'w') as new_file:
            with open(netConfigFile) as old_file:
                for line in old_file:
                    if "setenv NMHOME" in line:
                        line = "setenv NMHOME " + os.getcwd() + "/resources/netMHCpan-3.0\n"
                        new_file.write(line)
                    elif "setenv TMPDIR" in line:
                        line = "\tsetenv TMPDIR " + os.getcwd() + "/scratch\n"
                        new_file.write(line)
                    else:
                        new_file.write(line)
        ## Clean up
        os.remove(netConfigFile)
        os.rename(new_config, new_config[:-4])
        ## And make it executable
        st = os.stat(new_config[:-4])
        os.chmod(new_config[:-4], st.st_mode | stat.S_IEXEC)




    def get_HLA_alleles(self):
        hla_cat = str(self.inputHLACategory.currentText())
        own_path = os.getcwd()
        hla_alleles = [line.strip() for line in open(own_path+"/resources/hla_alleles.txt", "r")]
        ##Depending on the user's selection show HLA alleles
        if hla_cat=="All HLAs":
            self.inputHLAallele.addItems(hla_alleles)
        elif hla_cat=="HLA-A":
            hla_alleles = filter(lambda x: 'HLA-A' in x, hla_alleles)
            self.inputHLAallele.clear()
            self.inputHLAallele.addItems(hla_alleles)
        elif hla_cat=="HLA-B":
            hla_alleles = filter(lambda x: 'HLA-B' in x, hla_alleles)
            self.inputHLAallele.clear()
            self.inputHLAallele.addItems(hla_alleles)
        elif hla_cat=="HLA-C":
            hla_alleles = filter(lambda x: 'HLA-C' in x, hla_alleles)
            self.inputHLAallele.clear()
            self.inputHLAallele.addItems(hla_alleles)
        elif hla_cat=="HLA-E":
            hla_alleles = filter(lambda x: 'HLA-E' in x, hla_alleles)
            self.inputHLAallele.clear()
            self.inputHLAallele.addItems(hla_alleles)


    def Browse(self):
        fname = QFileDialog.getOpenFileName()
        print(fname)
        #self.ui.lineEdit.setText(fname)

    ## Method to center the window in the desktop screen
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    ## Print a message when user quits
    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message',
                                     "Are you sure to quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())