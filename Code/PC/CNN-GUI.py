import os
import sys
import traceback

import tensorflow as tf
import numpy as np
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox, QApplication, QMainWindow, QWidget
from tensorflow.python.framework.errors_impl import InvalidArgumentError, NotFoundError

from GUI.DatasetsGenerator import Ui_DatasetsGeneratorDialog
from GUI.CNNLoaderDialog import Ui_CNNDialog
from GUI.TestPredictionWindow import Ui_CNNTesterWindow
import CNN

DISTANCES_FILENAME = "Distances.txt"


def show_error(parent, message, details=''):
    assert isinstance(parent, QWidget)
    assert isinstance(message, str)
    assert isinstance(details, str)
    msgBox = QMessageBox(QMessageBox.Critical, 'Erreur', message, parent=parent)
    if details:
        msgBox.setDetailedText(details)
    msgBox.exec()


class DatasetsGenerator(QDialog, Ui_DatasetsGeneratorDialog):

    def __init__(self, parent):
        super(DatasetsGenerator, self).__init__(parent)
        self.setupUi(self)
        self.datasetLineEdit.textChanged.connect(self.validate_entry)
        self.destinationLineEdit.textChanged.connect(self.validate_entry)

    def validate_entry(self):
        self.generatePushButton.setEnabled(os.path.isdir(self.datasetLineEdit.text()) and self.destinationLineEdit.text())

    def choose_original_dataset(self):
        directory = QFileDialog.getExistingDirectory(self)
        if directory:
            self.datasetLineEdit.setText(directory)

    def generate(self):
        CNN.generate_datasets(self.datasetLineEdit.text(), self.destinationLineEdit.text(),
                              self.trainRatioSpinBox.value()/100, self.valTestRatioSpinBox.value()/100)


class CNNLoaderDialog(QDialog, Ui_CNNDialog):

    def __init__(self, app):
        super(CNNLoaderDialog, self).__init__()
        self.setupUi(self)
        self.window = None
        self.app = app

        self.cnnPathPushButton.clicked.connect(self.choose_cnn)
        self.checkpointPathPushButton.clicked.connect(self.choose_checkpoint)

    def choose_cnn(self):
        cnn_file_path = QFileDialog.getOpenFileName(self, filter='ConvNet JSON (*.json)')[0]
        if cnn_file_path:
            self.cnnPathLineEdit.setText(cnn_file_path)

    def choose_checkpoint(self):
        checkpoint_file_path = QFileDialog.getOpenFileName(self, filter='Checkpoint (checkpoint)')[0]
        if checkpoint_file_path:
            self.checkpointPathLineEdit.setText(checkpoint_file_path)

    def accept(self):
        import json
        try:
            with open(self.cnnPathLineEdit.text()) as cnn_json_file:
                from collections import OrderedDict
                ConvNet = CNN.convolutional_neural_network(self.heightSpinBox.value(),
                                                           self.widthSpinBox.value(),
                                                           self.channelsSpinBox.value(),
                                                           json.load(cnn_json_file, object_pairs_hook=OrderedDict))
            self.window = EvaluationWindow(ConvNet, self.cnnPathLineEdit.text(), self.checkpointPathLineEdit.text())
            self.window.move(self.app.desktop().availableGeometry().center() - self.window.rect().center())
            self.window.show()
            self.hide()
        except OSError as e:
            show_error(self, 'Impossible de charger le fichier du réseau !', e.strerror)
        except json.JSONDecodeError:
            show_error(self, 'Le fichier est invalide !')


class EvaluationWindow(QMainWindow, Ui_CNNTesterWindow):

    DISTANCES_VALUES = ['Petite', 'Moyenne', 'Grande', 'Inconnue']

    def __init__(self, conv_net, conv_net_file_path, checkpoint_file_path):
        super(EvaluationWindow, self).__init__()
        self.setupUi(self)
        self.distances = []
        self.conv_net = conv_net
        self.conv_net_file_path = conv_net_file_path
        self.checkpoint_file_path = checkpoint_file_path

        self.datasetPathPushButton.clicked.connect(self.choose_dataset)
        self.datasetPathLineEdit.textChanged.connect(self.dataset_path_updated)
        self.imagePathLineEdit.textChanged.connect(self.predict_image_path_changed)
        self.imagePathPushButton.clicked.connect(self.choose_image)

    def choose_dataset(self):
        directory = QFileDialog.getExistingDirectory(self)
        if directory:
            self.datasetPathLineEdit.setText(directory)

    def choose_image(self):
        image_path, _ = QFileDialog.getOpenFileName(self, filter='Image JPEG (*.jpeg, *.jpg)')
        if image_path:
            self.imagePathLineEdit.setText(image_path)

    def predict_image_path_changed(self, image_path):
        if os.path.isfile(image_path):
            try:
                saved_model_file_path, _ = CNN.get_saved_model_path_and_last_step(self.checkpoint_file_path)
                variables_saver = tf.train.Saver(self.conv_net['variables'])
                with tf.Session() as session:
                    with session.as_default():
                        picture_color = CNN.load_picture(image_path, False, 1, True)
                        picture_gray = CNN.load_picture(image_path, True,
                                                        picture_color.shape[0] / int(self.conv_net['input'].get_shape()[1]))
                        variables_saver.restore(session, saved_model_file_path)
                        [output] = session.run([self.conv_net['output']], feed_dict={
                        self.conv_net['input']: picture_gray.reshape((1,) + picture_gray.shape)})
                # print(output.reshape((-1,)))
                if output.shape[1] > 1:
                    self.imagePredictionValueLabel.setText(self.DISTANCES_VALUES[np.argmax(output)])
                image = QImage(picture_color.tobytes(),  # The content of the image
                               picture_color.shape[1],  # The width (number of columns)
                               picture_color.shape[0],  # The height (number of rows)
                               QImage.Format_RGB888)  # The image is stored in uint8
                capture = QPixmap.fromImage(image)
                self.predictCaptureViewLabel.setPixmap(capture)
            except (InvalidArgumentError, NotFoundError) as e:
                show_error(self, 'Impossible de charger les poids du modèle !', e.message)
                self.close()
            except Exception:
                traceback.print_exception(*sys.exc_info())
        else:
            self.imagePredictionValueLabel.setText('Aucune')
            self.predictCaptureViewLabel.setPixmap(QPixmap())

    def set_captures_count(self, count):
        self.captureNumberSpinBox.setMaximum(count)
        self.capturesCountLcdNumber.display(count)

    def set_current_capture(self, captureNumber):
        try:
            capture_id, distance = self.distances[captureNumber-1]
            capture_filename = 'IMG_{}.jpg'.format(capture_id)
            directory = self.datasetPathLineEdit.text()
            capture_file_path = os.path.join(directory, capture_filename)
            saved_model_file_path, _ = CNN.get_saved_model_path_and_last_step(self.checkpoint_file_path)
            variables_saver = tf.train.Saver(self.conv_net['variables'])
            with tf.Session() as session:
                with session.as_default():
                    picture_color = CNN.load_picture(capture_file_path, False, 1, True)
                    picture_gray = CNN.load_picture(capture_file_path, True,
                                                    picture_color.shape[0] / int(self.conv_net['input'].get_shape()[1]))
                    variables_saver.restore(session, saved_model_file_path)
                    [output] = session.run([self.conv_net['output']], feed_dict={self.conv_net['input']: picture_gray.reshape((1,)+picture_gray.shape)})
            if output.shape[1] > 1:
                self.cnnPredictionValueLabel.setText(self.DISTANCES_VALUES[np.argmax(output)])
                self.groundTruthValueLabel.setText(self.DISTANCES_VALUES[int(distance / 4.5 * (output.shape[1] - 1))])
            image = QImage(picture_color.tobytes(),  # The content of the image
                           picture_color.shape[1],  # The width (number of columns)
                           picture_color.shape[0],  # The height (number of rows)
                           QImage.Format_RGB888)  # The image is stored in uint8
            capture = QPixmap.fromImage(image)
            self.captureViewLabel.setPixmap(capture)
        except (InvalidArgumentError, NotFoundError) as e:
            show_error(self, 'Impossible de charger les poids du modèle !', e.message)
            self.close()
        except Exception:
            traceback.print_exception(*sys.exc_info())

    def disable_results(self):
        self.cnnPredictionValueLabel.setText('Aucune')
        self.groundTruthValueLabel.setText('Aucune')
        try:
            self.captureNumberSpinBox.valueChanged.disconnect()
        except TypeError:  # happens when the signal is not connected
            pass
        self.captureNumberSpinBox.setMinimum(0)
        self.captureNumberSpinBox.setValue(0)
        self.capturesCountLcdNumber.display(0)
        self.captureViewLabel.setPixmap(QPixmap())
        self.entryGroupBox.setEnabled(False)

    def dataset_path_updated(self, directory):
        distances_file_path = os.path.join(directory, DISTANCES_FILENAME)
        if os.path.isfile(distances_file_path):
            try:
                self.distances = list(CNN.get_pictures_distances(directory).items())
                self.set_captures_count(len(self.distances))
                self.captureNumberSpinBox.valueChanged.connect(self.set_current_capture)
                self.captureNumberSpinBox.setValue(1)
                self.captureNumberSpinBox.setMinimum(1)
                self.entryGroupBox.setEnabled(True)
            except OSError:
                self.disable_results()
                show_error(self, 'Impossible de charger le fichier de distances !')
        else:
            self.disable_results()

if __name__ == '__main__':
    application = QApplication(sys.argv)
    loader = CNNLoaderDialog(application)
    loader.show()
    sys.exit(application.exec())
