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
import re
from shutil import copyfile

class MyWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        # determine if application is a script file or frozen exe
        if getattr(sys, 'frozen', False):
            self.application_path = os.path.dirname(sys.executable)
        elif __file__:
            self.application_path = os.path.dirname(__file__)
        uic.loadUi(self.application_path + '/mainwindow.ui', self)
        self.inputPath = None
        self.outPath = None
        self.initUI()

    def initUI(self):

        self.inputFile.clicked.connect(self.BrowseInput)
        self.outputFile.clicked.connect(self.BrowseOutput)

        ## Set HLA alleles
        self.inputHLACategory.activated.connect(self.get_HLA_alleles)

        #self.inputHLAallele.itemSelectionChanged.connect(self.get_selected_alleles)
        self.runbtn.clicked.connect(self.runNetMHCpan)

    def runNetMHCpan(self):

        if self.inputText.toPlainText()=="" and self.inputPath is None:
            msg = QtWidgets.QMessageBox(self)
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setWindowTitle('Input warning')
            msg.setText('Please specify input sequence')
            ok = msg.addButton(
                'OK', QtWidgets.QMessageBox.AcceptRole)
            msg.setDefaultButton(ok)
            msg.exec_()
            msg.deleteLater()
        else:
            home = expanduser("~")
            results_dir = None
            ## Input file always wins
            if self.inputPath is not None:
                if self.outPath is None:
                    if not os.path.exists(home+"/.pyBind_out"):
                        os.mkdir(home+"/.pyBind_out")
                    copyfile(self.inputPath, home+"/.pyBind_out/input.fasta")
                    results_dir = home+"/.pyBind_out"
                else:
                    if not os.path.exists(self.outPath+"/.pyBind_out"):
                        os.mkdir(self.outPath+"/.pyBind_out")
                    copyfile(self.inputPath, self.outPath+"/.pyBind_out/input.fasta")
                    results_dir = self.outPath+"/.pyBind_out"
            elif self.inputPath is None:
                if self.outPath is None:
                    if not os.path.exists(home+"/.pyBind_out"):
                        os.mkdir(home+"/.pyBind_out")
                    infile = open(home+"/.pyBind_out"+"/input.fasta", "w")
                    infile.write(self.inputText.toPlainText())
                    infile.close()
                    results_dir = home+"/.pyBind_out"
                else:
                    if not os.path.exists(self.outPath+"/.pyBind_out"):
                        os.mkdir(self.outPath+"/.pyBind_out")
                    infile = open(self.outPath+"/.pyBind_out"+"/input.fasta", "w")
                    infile.write(self.inputText.toPlainText())
                    infile.close()
                    results_dir = self.outPath+"/.pyBind_out"

            ## Get rest of parameters
            hlas = self.inputHLAallele.selectedItems()
            hlas = [x.text() for x in hlas]
            print()
            mers = self.inputMers.selectedItems()
            mers = [x.text() for x in mers]
            pattern = re.compile(r'\d')
            mers = ",".join(["".join(pattern.findall(x)) for x in mers])

            ## Print a message if mers of hlas missing
            if len(hlas)==0:
                hlas = "HLA-A02:01"
            if mers=="":
                mers = "8"

            msg = QtWidgets.QMessageBox(self)
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setWindowTitle('Input warning')
            msg.setText('Unspecified parameters')
            #msg.informativeText('kmers or HLAs unselected and set to default values')
            ok = msg.addButton(
                'OK', QtWidgets.QMessageBox.AcceptRole)
            msg.setDefaultButton(ok)
            msg.exec_()
            msg.deleteLater()


            ## After taking all parameters I need to update the configuration script of netMHCpan
            netConfigFile = self.application_path + "/data/netMHCpan-3.0/netMHCpan"
            new_config = self.application_path + "/data/netMHCpan-3.0/netMHCpan_new"

            if not os.path.exists(home+"/scratch"):
                os.makedirs(home+"/scratch")

            with open(new_config, 'w') as new_file:
                with open(netConfigFile) as old_file:
                    for line in old_file:
                        if "setenv NMHOME" in line:
                            line = "setenv NMHOME " + self.application_path + "/data/netMHCpan-3.0\n"
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
            chunk_cut = 100
            chunks = math.ceil(len(hlas)/chunk_cut)

            pids = []
            completed_output_handles = []
            commands = []
            for i in range(0, chunks):
                hlasToRun = ",".join(hlas[(i*chunk_cut):(i*chunk_cut)+chunk_cut])
                cmd = '{} -p {} -a {}'.format(
                    netConfigFile, self.application_path + "/data/netMHCpan-3.0/test/test.pep",
                                   hlasToRun)
                command = cmd.split()
                output_fn = results_dir + '/netMHCpan.myout' + str(i)
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
        hla_alleles = [line.strip() for line in open(self.application_path+"/data/hla_alleles.txt", "r")]
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


    def BrowseInput(self):
        fname = QFileDialog.getOpenFileName()
        self.inputFileTag.setText(str(fname[0].split("/")[-1]))
        self.inputPath = str(fname[0])

    def BrowseOutput(self):
        dirname = QFileDialog.getExistingDirectory()
        self.outputFileTag.setText(dirname)
        self.outPath = str(dirname)

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