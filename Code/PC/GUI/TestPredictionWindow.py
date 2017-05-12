# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'GUI/TestPredictionWindow.ui'
#
# Created by: PyQt5 UI code generator 5.8
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_CNNTesterWindow(object):
    def setupUi(self, CNNTesterWindow):
        CNNTesterWindow.setObjectName("CNNTesterWindow")
        CNNTesterWindow.resize(488, 449)
        CNNTesterWindow.setLocale(QtCore.QLocale(QtCore.QLocale.French, QtCore.QLocale.France))
        self.centralwidget = QtWidgets.QWidget(CNNTesterWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.modeTabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.modeTabWidget.setObjectName("modeTabWidget")
        self.testTab = QtWidgets.QWidget()
        self.testTab.setObjectName("testTab")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.testTab)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.datasetGroupBox = QtWidgets.QGroupBox(self.testTab)
        self.datasetGroupBox.setObjectName("datasetGroupBox")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.datasetGroupBox)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.datasetPathLineEdit = QtWidgets.QLineEdit(self.datasetGroupBox)
        self.datasetPathLineEdit.setEnabled(True)
        self.datasetPathLineEdit.setObjectName("datasetPathLineEdit")
        self.horizontalLayout.addWidget(self.datasetPathLineEdit)
        self.datasetPathPushButton = QtWidgets.QPushButton(self.datasetGroupBox)
        self.datasetPathPushButton.setObjectName("datasetPathPushButton")
        self.horizontalLayout.addWidget(self.datasetPathPushButton)
        self.verticalLayout.addWidget(self.datasetGroupBox)
        self.entryGroupBox = QtWidgets.QGroupBox(self.testTab)
        self.entryGroupBox.setEnabled(False)
        self.entryGroupBox.setObjectName("entryGroupBox")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.entryGroupBox)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.captureViewLabel = QtWidgets.QLabel(self.entryGroupBox)
        self.captureViewLabel.setMinimumSize(QtCore.QSize(98, 98))
        self.captureViewLabel.setMaximumSize(QtCore.QSize(100, 100))
        self.captureViewLabel.setFrameShape(QtWidgets.QFrame.Panel)
        self.captureViewLabel.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.captureViewLabel.setText("")
        self.captureViewLabel.setObjectName("captureViewLabel")
        self.gridLayout_2.addWidget(self.captureViewLabel, 0, 0, 1, 1)
        self.distanceGroupBox = QtWidgets.QGroupBox(self.entryGroupBox)
        self.distanceGroupBox.setObjectName("distanceGroupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.distanceGroupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.cnnPredictionLabel = QtWidgets.QLabel(self.distanceGroupBox)
        self.cnnPredictionLabel.setObjectName("cnnPredictionLabel")
        self.gridLayout.addWidget(self.cnnPredictionLabel, 0, 0, 1, 1)
        self.cnnPredictionValueLabel = QtWidgets.QLabel(self.distanceGroupBox)
        self.cnnPredictionValueLabel.setStyleSheet("*:enabled {\n"
"color : lightblue;\n"
"}")
        self.cnnPredictionValueLabel.setObjectName("cnnPredictionValueLabel")
        self.gridLayout.addWidget(self.cnnPredictionValueLabel, 0, 1, 1, 1)
        self.groundTruthLabel = QtWidgets.QLabel(self.distanceGroupBox)
        self.groundTruthLabel.setObjectName("groundTruthLabel")
        self.gridLayout.addWidget(self.groundTruthLabel, 1, 0, 1, 1)
        self.groundTruthValueLabel = QtWidgets.QLabel(self.distanceGroupBox)
        self.groundTruthValueLabel.setStyleSheet("*:enabled {\n"
"color : lightgreen;\n"
"}")
        self.groundTruthValueLabel.setObjectName("groundTruthValueLabel")
        self.gridLayout.addWidget(self.groundTruthValueLabel, 1, 1, 1, 1)
        self.gridLayout_2.addWidget(self.distanceGroupBox, 0, 1, 1, 1)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.captureNumberLabel = QtWidgets.QLabel(self.entryGroupBox)
        self.captureNumberLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.captureNumberLabel.setObjectName("captureNumberLabel")
        self.horizontalLayout_3.addWidget(self.captureNumberLabel)
        self.captureNumberSpinBox = QtWidgets.QSpinBox(self.entryGroupBox)
        self.captureNumberSpinBox.setObjectName("captureNumberSpinBox")
        self.horizontalLayout_3.addWidget(self.captureNumberSpinBox)
        self.captureCountLabel = QtWidgets.QLabel(self.entryGroupBox)
        self.captureCountLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.captureCountLabel.setObjectName("captureCountLabel")
        self.horizontalLayout_3.addWidget(self.captureCountLabel)
        self.capturesCountLcdNumber = QtWidgets.QLCDNumber(self.entryGroupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.capturesCountLcdNumber.sizePolicy().hasHeightForWidth())
        self.capturesCountLcdNumber.setSizePolicy(sizePolicy)
        self.capturesCountLcdNumber.setLocale(QtCore.QLocale(QtCore.QLocale.French, QtCore.QLocale.France))
        self.capturesCountLcdNumber.setObjectName("capturesCountLcdNumber")
        self.horizontalLayout_3.addWidget(self.capturesCountLcdNumber)
        self.gridLayout_2.addLayout(self.horizontalLayout_3, 1, 0, 1, 2)
        self.verticalLayout.addWidget(self.entryGroupBox)
        self.modeTabWidget.addTab(self.testTab, "")
        self.predictionTab = QtWidgets.QWidget()
        self.predictionTab.setObjectName("predictionTab")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.predictionTab)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.predictImageGroupBox = QtWidgets.QGroupBox(self.predictionTab)
        self.predictImageGroupBox.setObjectName("predictImageGroupBox")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.predictImageGroupBox)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.imagePathPushButton = QtWidgets.QPushButton(self.predictImageGroupBox)
        self.imagePathPushButton.setObjectName("imagePathPushButton")
        self.gridLayout_3.addWidget(self.imagePathPushButton, 0, 4, 1, 1)
        self.imagePathLineEdit = QtWidgets.QLineEdit(self.predictImageGroupBox)
        self.imagePathLineEdit.setEnabled(True)
        self.imagePathLineEdit.setObjectName("imagePathLineEdit")
        self.gridLayout_3.addWidget(self.imagePathLineEdit, 0, 0, 1, 4)
        self.predictCaptureViewLabel = QtWidgets.QLabel(self.predictImageGroupBox)
        self.predictCaptureViewLabel.setMinimumSize(QtCore.QSize(98, 98))
        self.predictCaptureViewLabel.setMaximumSize(QtCore.QSize(100, 100))
        self.predictCaptureViewLabel.setFrameShape(QtWidgets.QFrame.Panel)
        self.predictCaptureViewLabel.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.predictCaptureViewLabel.setText("")
        self.predictCaptureViewLabel.setObjectName("predictCaptureViewLabel")
        self.gridLayout_3.addWidget(self.predictCaptureViewLabel, 1, 0, 1, 1)
        self.imagePredictionLabel = QtWidgets.QLabel(self.predictImageGroupBox)
        self.imagePredictionLabel.setObjectName("imagePredictionLabel")
        self.gridLayout_3.addWidget(self.imagePredictionLabel, 1, 2, 1, 1)
        self.imagePredictionValueLabel = QtWidgets.QLabel(self.predictImageGroupBox)
        self.imagePredictionValueLabel.setStyleSheet("* {\n"
"color : lightblue;\n"
"}")
        self.imagePredictionValueLabel.setObjectName("imagePredictionValueLabel")
        self.gridLayout_3.addWidget(self.imagePredictionValueLabel, 1, 4, 1, 1)
        self.verticalLayout_3.addWidget(self.predictImageGroupBox)
        self.modeTabWidget.addTab(self.predictionTab, "")
        self.verticalLayout_2.addWidget(self.modeTabWidget)
        CNNTesterWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(CNNTesterWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 488, 39))
        self.menubar.setObjectName("menubar")
        CNNTesterWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(CNNTesterWindow)
        self.statusbar.setObjectName("statusbar")
        CNNTesterWindow.setStatusBar(self.statusbar)

        self.retranslateUi(CNNTesterWindow)
        self.modeTabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(CNNTesterWindow)

    def retranslateUi(self, CNNTesterWindow):
        _translate = QtCore.QCoreApplication.translate
        CNNTesterWindow.setWindowTitle(_translate("CNNTesterWindow", "Evaluateur du réseau"))
        self.datasetGroupBox.setTitle(_translate("CNNTesterWindow", "Ensemble de données de test"))
        self.datasetPathLineEdit.setPlaceholderText(_translate("CNNTesterWindow", "Répertoire contenant Distances.txt"))
        self.datasetPathPushButton.setText(_translate("CNNTesterWindow", "Choisir"))
        self.entryGroupBox.setTitle(_translate("CNNTesterWindow", "Donnée et résultat"))
        self.distanceGroupBox.setTitle(_translate("CNNTesterWindow", "Distance"))
        self.cnnPredictionLabel.setText(_translate("CNNTesterWindow", "Prédiction du réseau"))
        self.cnnPredictionValueLabel.setText(_translate("CNNTesterWindow", "Aucune"))
        self.groundTruthLabel.setText(_translate("CNNTesterWindow", "Réponse attendue"))
        self.groundTruthValueLabel.setText(_translate("CNNTesterWindow", "Aucune"))
        self.captureNumberLabel.setText(_translate("CNNTesterWindow", "N°"))
        self.captureCountLabel.setText(_translate("CNNTesterWindow", "sur"))
        self.modeTabWidget.setTabText(self.modeTabWidget.indexOf(self.testTab), _translate("CNNTesterWindow", "Test"))
        self.predictImageGroupBox.setTitle(_translate("CNNTesterWindow", "Image"))
        self.imagePathPushButton.setText(_translate("CNNTesterWindow", "Choisir"))
        self.imagePredictionLabel.setText(_translate("CNNTesterWindow", "Prédiction du réseau"))
        self.imagePredictionValueLabel.setText(_translate("CNNTesterWindow", "Aucune"))
        self.modeTabWidget.setTabText(self.modeTabWidget.indexOf(self.predictionTab), _translate("CNNTesterWindow", "Prédiction"))

