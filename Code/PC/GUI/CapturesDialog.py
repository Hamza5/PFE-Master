# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'GUI/CapturesDialog.ui'
#
# Created by: PyQt5 UI code generator 5.8
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_CapturesDialog(object):
    def setupUi(self, CapturesDialog):
        CapturesDialog.setObjectName("CapturesDialog")
        CapturesDialog.resize(408, 257)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(CapturesDialog)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.capturesGroupBox = QtWidgets.QGroupBox(CapturesDialog)
        self.capturesGroupBox.setObjectName("capturesGroupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.capturesGroupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.captureNumberSpinBox = QtWidgets.QSpinBox(self.capturesGroupBox)
        self.captureNumberSpinBox.setObjectName("captureNumberSpinBox")
        self.horizontalLayout_3.addWidget(self.captureNumberSpinBox)
        self.captureCountLabel = QtWidgets.QLabel(self.capturesGroupBox)
        self.captureCountLabel.setObjectName("captureCountLabel")
        self.horizontalLayout_3.addWidget(self.captureCountLabel)
        self.capturesCountLcdNumber = QtWidgets.QLCDNumber(self.capturesGroupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.capturesCountLcdNumber.sizePolicy().hasHeightForWidth())
        self.capturesCountLcdNumber.setSizePolicy(sizePolicy)
        self.capturesCountLcdNumber.setLocale(QtCore.QLocale(QtCore.QLocale.French, QtCore.QLocale.France))
        self.capturesCountLcdNumber.setObjectName("capturesCountLcdNumber")
        self.horizontalLayout_3.addWidget(self.capturesCountLcdNumber)
        self.gridLayout.addLayout(self.horizontalLayout_3, 0, 1, 1, 1)
        self.captureViewLabel = QtWidgets.QLabel(self.capturesGroupBox)
        self.captureViewLabel.setMinimumSize(QtCore.QSize(98, 98))
        self.captureViewLabel.setMaximumSize(QtCore.QSize(100, 100))
        self.captureViewLabel.setFrameShape(QtWidgets.QFrame.Panel)
        self.captureViewLabel.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.captureViewLabel.setText("")
        self.captureViewLabel.setObjectName("captureViewLabel")
        self.gridLayout.addWidget(self.captureViewLabel, 0, 0, 2, 1)
        self.captureDateTimeEdit = QtWidgets.QDateTimeEdit(self.capturesGroupBox)
        self.captureDateTimeEdit.setReadOnly(True)
        self.captureDateTimeEdit.setObjectName("captureDateTimeEdit")
        self.gridLayout.addWidget(self.captureDateTimeEdit, 1, 1, 1, 1)
        self.verticalLayout_2.addWidget(self.capturesGroupBox)
        self.distancesGroupBox = QtWidgets.QGroupBox(CapturesDialog)
        self.distancesGroupBox.setObjectName("distancesGroupBox")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.distancesGroupBox)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.distancesLineEdit = QtWidgets.QLineEdit(self.distancesGroupBox)
        self.distancesLineEdit.setMinimumSize(QtCore.QSize(380, 0))
        self.distancesLineEdit.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.distancesLineEdit.setReadOnly(True)
        self.distancesLineEdit.setObjectName("distancesLineEdit")
        self.horizontalLayout_2.addWidget(self.distancesLineEdit)
        self.verticalLayout_2.addWidget(self.distancesGroupBox)

        self.retranslateUi(CapturesDialog)
        QtCore.QMetaObject.connectSlotsByName(CapturesDialog)

    def retranslateUi(self, CapturesDialog):
        _translate = QtCore.QCoreApplication.translate
        CapturesDialog.setWindowTitle(_translate("CapturesDialog", "Captures et distances"))
        self.capturesGroupBox.setTitle(_translate("CapturesDialog", "Captures"))
        self.captureCountLabel.setText(_translate("CapturesDialog", "sur"))
        self.captureDateTimeEdit.setDisplayFormat(_translate("CapturesDialog", "dd/MM/yyyy h:mm:ss AP"))
        self.distancesGroupBox.setTitle(_translate("CapturesDialog", "Distances"))
        self.distancesLineEdit.setText(_translate("CapturesDialog", "|0.00|0.00|0.00|0.00|0.00|0.00|0.00|"))

