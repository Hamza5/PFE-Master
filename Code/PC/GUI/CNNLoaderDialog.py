# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'GUI/CNNLoaderDialog.ui'
#
# Created by: PyQt5 UI code generator 5.8
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_CNNDialog(object):
    def setupUi(self, CNNDialog):
        CNNDialog.setObjectName("CNNDialog")
        CNNDialog.resize(449, 447)
        CNNDialog.setLocale(QtCore.QLocale(QtCore.QLocale.French, QtCore.QLocale.France))
        self.verticalLayout = QtWidgets.QVBoxLayout(CNNDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.cnnPathGroupBox = QtWidgets.QGroupBox(CNNDialog)
        self.cnnPathGroupBox.setObjectName("cnnPathGroupBox")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.cnnPathGroupBox)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.cnnPathLineEdit = QtWidgets.QLineEdit(self.cnnPathGroupBox)
        self.cnnPathLineEdit.setEnabled(True)
        self.cnnPathLineEdit.setObjectName("cnnPathLineEdit")
        self.gridLayout_2.addWidget(self.cnnPathLineEdit, 0, 0, 1, 1)
        self.cnnPathPushButton = QtWidgets.QPushButton(self.cnnPathGroupBox)
        self.cnnPathPushButton.setObjectName("cnnPathPushButton")
        self.gridLayout_2.addWidget(self.cnnPathPushButton, 0, 1, 1, 1)
        self.verticalLayout.addWidget(self.cnnPathGroupBox)
        self.checkpointGroupBox = QtWidgets.QGroupBox(CNNDialog)
        self.checkpointGroupBox.setObjectName("checkpointGroupBox")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.checkpointGroupBox)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.checkpointPathLineEdit = QtWidgets.QLineEdit(self.checkpointGroupBox)
        self.checkpointPathLineEdit.setEnabled(True)
        self.checkpointPathLineEdit.setObjectName("checkpointPathLineEdit")
        self.gridLayout_3.addWidget(self.checkpointPathLineEdit, 0, 0, 1, 1)
        self.checkpointPathPushButton = QtWidgets.QPushButton(self.checkpointGroupBox)
        self.checkpointPathPushButton.setObjectName("checkpointPathPushButton")
        self.gridLayout_3.addWidget(self.checkpointPathPushButton, 0, 1, 1, 1)
        self.verticalLayout.addWidget(self.checkpointGroupBox)
        self.inputGroupBox = QtWidgets.QGroupBox(CNNDialog)
        self.inputGroupBox.setObjectName("inputGroupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.inputGroupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.heightLabel = QtWidgets.QLabel(self.inputGroupBox)
        self.heightLabel.setObjectName("heightLabel")
        self.gridLayout.addWidget(self.heightLabel, 0, 0, 1, 1)
        self.heightSpinBox = QtWidgets.QSpinBox(self.inputGroupBox)
        self.heightSpinBox.setMinimum(24)
        self.heightSpinBox.setMaximum(96)
        self.heightSpinBox.setSingleStep(24)
        self.heightSpinBox.setProperty("value", 48)
        self.heightSpinBox.setObjectName("heightSpinBox")
        self.gridLayout.addWidget(self.heightSpinBox, 0, 1, 1, 1)
        self.widthLabel = QtWidgets.QLabel(self.inputGroupBox)
        self.widthLabel.setObjectName("widthLabel")
        self.gridLayout.addWidget(self.widthLabel, 1, 0, 1, 1)
        self.widthSpinBox = QtWidgets.QSpinBox(self.inputGroupBox)
        self.widthSpinBox.setMinimum(24)
        self.widthSpinBox.setMaximum(96)
        self.widthSpinBox.setSingleStep(24)
        self.widthSpinBox.setProperty("value", 48)
        self.widthSpinBox.setObjectName("widthSpinBox")
        self.gridLayout.addWidget(self.widthSpinBox, 1, 1, 1, 1)
        self.channelsLabel = QtWidgets.QLabel(self.inputGroupBox)
        self.channelsLabel.setObjectName("channelsLabel")
        self.gridLayout.addWidget(self.channelsLabel, 2, 0, 1, 1)
        self.channelsSpinBox = QtWidgets.QSpinBox(self.inputGroupBox)
        self.channelsSpinBox.setMinimum(1)
        self.channelsSpinBox.setMaximum(3)
        self.channelsSpinBox.setSingleStep(2)
        self.channelsSpinBox.setObjectName("channelsSpinBox")
        self.gridLayout.addWidget(self.channelsSpinBox, 2, 1, 1, 1)
        self.verticalLayout.addWidget(self.inputGroupBox)
        self.buttonBox = QtWidgets.QDialogButtonBox(CNNDialog)
        self.buttonBox.setEnabled(True)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(CNNDialog)
        self.buttonBox.rejected.connect(CNNDialog.reject)
        self.buttonBox.accepted.connect(CNNDialog.accept)
        QtCore.QMetaObject.connectSlotsByName(CNNDialog)

    def retranslateUi(self, CNNDialog):
        _translate = QtCore.QCoreApplication.translate
        CNNDialog.setWindowTitle(_translate("CNNDialog", "Chargeur du réseau"))
        self.cnnPathGroupBox.setTitle(_translate("CNNDialog", "Fichier du réseau de neurones convolutionel"))
        self.cnnPathPushButton.setText(_translate("CNNDialog", "Choisir"))
        self.checkpointGroupBox.setTitle(_translate("CNNDialog", "Fichier du point de contrôle"))
        self.checkpointPathPushButton.setText(_translate("CNNDialog", "Choisir"))
        self.inputGroupBox.setTitle(_translate("CNNDialog", "Paramètres d\'images"))
        self.heightLabel.setText(_translate("CNNDialog", "Hauteur"))
        self.widthLabel.setText(_translate("CNNDialog", "Largeur"))
        self.channelsLabel.setText(_translate("CNNDialog", "Canaux"))
