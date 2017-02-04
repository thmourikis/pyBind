import sys
import os
import stat
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QMessageBox, QApplication, QDesktopWidget, QFileDialog
import subprocess
import math
from os.path import expanduser
import time

class MyWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        uic.loadUi('mainwindow.ui', self)
        self.inputPath = None
        self.outPath = None
        self.initUI()

    def initUI(self):

        self.inputFile.clicked.connect(self.Browse)

        ## Set HLA alleles
        self.inputHLACategory.activated.connect(self.get_HLA_alleles)

        #self.inputHLAallele.itemSelectionChanged.connect(self.get_selected_alleles)
        self.runbtn.clicked.connect(self.runNetMHCpan)

    def runNetMHCpan(self):

        ##Print a message that the run stated

        home = expanduser("~")
        hlas = self.inputHLAallele.selectedItems()
        hlas = [x.text() for x in hlas]
        print(hlas)
        mers = self.inputMers.selectedItems()
        mers = [x.text() for x in mers]
        print(mers)
        seq = self.inputText.toPlainText()
        print(seq)


        ## After taking all parameters I need to update the configuration script of netMHCpan
        netConfigFile = os.getcwd() + "/resources/netMHCpan-3.0/netMHCpan"
        new_config = os.getcwd() + "/resources/netMHCpan-3.0/netMHCpan_new"

        if not os.path.exists(home+"/scratch"):
            os.makedirs(home+"/scratch")

        with open(new_config, 'w') as new_file:
            with open(netConfigFile) as old_file:
                for line in old_file:
                    if "setenv NMHOME" in line:
                        line = "setenv NMHOME " + os.getcwd() + "/resources/netMHCpan-3.0\n"
                        new_file.write(line)
                    elif "setenv TMPDIR" in line:
                        line = "\tsetenv TMPDIR " + home + "/scratch\n"
                        new_file.write(line)
                    else:
                        new_file.write(line)
        ## Clean up
        os.remove(netConfigFile)
        os.rename(new_config, new_config[:-4])
        ## And make it executable
        st = os.stat(new_config[:-4])
        os.chmod(new_config[:-4], st.st_mode | stat.S_IEXEC)

        ## run job in chunks - pseudo-parallel
        threads=3
        chunk_cut = 2
        chunks = math.ceil(len(hlas)/chunk_cut)

        pids = []
        completed_output_handles = []
        commands = []
        for i in range(0, chunks):
            hlasToRun = ",".join(hlas[(i*chunk_cut):(i*chunk_cut)+chunk_cut])
            cmd = '{} -p {} -a {}'.format(
                netConfigFile, os.getcwd() + "/resources/netMHCpan-3.0/test/test.pep",
                               hlasToRun)
            command = cmd.split()
            output_fn = 'netMHCpan.myout' + str(i)
            commands.append((command, output_fn))

        for i in range(0, threads):
            if len(commands) != 0:  ## still stuff left to execute:
                new_command, new_output_fn = commands.pop(0)
                new_output_handle = open(new_output_fn, 'w')
                new_pid = subprocess.Popen(new_command, stdout=new_output_handle, stderr=subprocess.PIPE)
                pids.append((new_pid, new_output_handle))

        while len(pids) != 0:
            time.sleep(1)
            for (pid, output_handle) in pids:  ## check running processes
                pid_return = pid.poll()
                ## poll returns None until the process finishes, then it returns the exit code
                if (pid_return != 0 and pid_return != None):
                    exit("Error: exonerate failed (code %d): %s" % (pid_return, pid.stderr))
                elif pid_return == 0:  ## Successful completion
                    output_handle.close()
                    completed_output_handles.append(output_handle)
                    pids.remove((pid, output_handle))
                    if len(commands) != 0:  ## still stuff left to execute:
                        new_command, new_output_fn = commands.pop(0)
                        new_output_handle = open(new_output_fn, 'w')
                        new_pid = subprocess.Popen(new_command, stdout=new_output_handle, stderr=subprocess.PIPE)
                        pids.append((new_pid, new_output_handle))

        assert (len(completed_output_handles) == chunks)

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