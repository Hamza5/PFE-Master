#!/usr/bin/env python3
import os
import sys
import random
import csv
from collections import OrderedDict

import tensorflow as tf
import numpy as np

DISTANCES_FILE = 'Distances.txt'
TOLERATED_ERROR = 0.3  # in meters
TRAIN_DATA_FACTOR = 0.7
VALIDATION_DATA_FACTOR = 0.15


def convolutional_neural_network(height, width, channels, layers) -> dict:
    """
    Generates a single stack convolutional neural network.
    :param height: the height of the input picture. 
    :param width: the width of the input picture.
    :param channels: the number of channels in the picture.
    :param layers: a dictionary containing the layers parameters.
    :return: a dictionary with 3 keys : 'input', 'output' and 'dropouts', the value of each key is a tensor.
    """
    assert isinstance(height, int)
    assert isinstance(width, int)
    assert isinstance(channels, int)
    assert isinstance(layers, OrderedDict)

    def weights(shape, name='weights'):
        """
        Generates a tensor that holds the weights.
        :param shape: the shape of the tensor.
        :param name: the name of the tensor.
        :return: A variable tensor initialised with small random values.
        """
        assert isinstance(shape, list)
        assert isinstance(name, str)
        w = tf.Variable(tf.truncated_normal(shape, stddev=0.1, dtype=tf.float32), name=name)
        return w

    def biases(shape, name='biases'):
        """
        Generates a tensor that holds the biases.
        :param shape: the shape of the tensor.
        :param name: the name of the tensor.
        :return: A constant tensor initialised with a small constant value.
        """
        assert isinstance(shape, list)
        assert isinstance(name, str)
        b = tf.Variable(tf.constant(0.1, shape=shape, dtype=tf.float32), name=name)
        return b

    with tf.name_scope('InputLayer'):
        input_layer = tf.placeholder(tf.float32, shape=[None, height, width, channels], name='input')
    previous_layer = input_layer
    dropouts = []
    for layer_name, layer_parameters in layers.items():
        assert isinstance(layer_parameters, dict)
        with tf.name_scope(layer_name):
            if len(layer_parameters) > 3:  # More than 3 hyper-parameters : convolutional layer
                assert 'field_size' in layer_parameters and isinstance(layer_parameters['field_size'], int)
                assert 'stride_size' in layer_parameters and isinstance(layer_parameters['stride_size'], int)
                assert 'padding' in layer_parameters and layer_parameters['padding'] in ('SAME', 'VALID')
                assert 'depth' in layer_parameters and isinstance(layer_parameters['depth'], int)
                current_layer = tf.nn.relu(
                    tf.nn.bias_add(
                        tf.nn.conv2d(previous_layer,
                                     weights([layer_parameters['field_size']] * 2 + [int(previous_layer.shape[3]), layer_parameters['depth']]),
                                     strides=[1] + [layer_parameters['stride_size']] * 2 + [1],
                                     padding=layer_parameters['padding']),
                        biases([layer_parameters['depth']])
                    )
                )
            elif len(layer_parameters) > 2:  # Max pooling layer
                assert 'field_size' in layer_parameters and isinstance(layer_parameters['field_size'], int)
                assert 'stride_size' in layer_parameters and isinstance(layer_parameters['stride_size'], int)
                assert 'padding' in layer_parameters and layer_parameters['padding'] in ('SAME', 'VALID')
                current_layer = tf.nn.max_pool(previous_layer,
                                               ksize=[1] + [layer_parameters['field_size']] * 2 + [1],
                                               strides=[1] + [layer_parameters['stride_size']] * 2 + [1],
                                               padding=layer_parameters['padding'])
            else:  # Fully connected layer
                assert 'depth' in layer_parameters and isinstance(layer_parameters['depth'], int)
                flatted_previous_dim = 1
                for dimension in previous_layer.shape[1:]:
                    flatted_previous_dim *= int(dimension)
                flatted_previous_layer = tf.reshape(previous_layer, [-1, flatted_previous_dim])
                default_keep_factor = tf.constant(layer_parameters.get('dropout_keep', 1), tf.float32)
                dropout_keep_factor = tf.placeholder_with_default(default_keep_factor, default_keep_factor.get_shape())
                dropouts.append(dropout_keep_factor)
                dense_layer = tf.nn.relu(
                    tf.nn.bias_add(
                        tf.matmul(flatted_previous_layer, weights([flatted_previous_dim, layer_parameters['depth']])),
                        biases([layer_parameters['depth']])
                    )
                )
                current_layer = tf.nn.dropout(dense_layer, dropout_keep_factor)
            previous_layer = current_layer

    return {'input': input_layer, 'output': previous_layer, 'dropouts': dropouts}


def load_picture(file_name):
    picture_raw = tf.read_file(file_name)
    picture = tf.image.convert_image_dtype(tf.image.decode_jpeg(picture_raw, channels=3), tf.float32)
    picture_content = picture.eval()
    return picture_content


def get_train_validation_test_sets(pictures_distances) -> (dict, dict, dict):
    assert isinstance(pictures_distances, dict)
    pictures_ids = list(pictures_distances.keys())
    random.shuffle(pictures_ids)  # Randomly reorders the file names
    train_size = round(TRAIN_DATA_FACTOR*len(pictures_ids))
    validation_size = round(VALIDATION_DATA_FACTOR*len(pictures_ids))
    train_ids = pictures_ids[:train_size]
    validation_ids = pictures_ids[train_size:train_size+validation_size]
    test_ids = pictures_ids[train_size+validation_size:]
    pictures_distances_train = dict((x, pictures_distances[x]) for x in train_ids)
    pictures_distances_validation = dict((x, pictures_distances[x]) for x in validation_ids)
    pictures_distances_test = dict((x, pictures_distances[x]) for x in test_ids)
    return pictures_distances_train, pictures_distances_validation, pictures_distances_test


def next_batch(data_directory, pictures_distances, batch_size, start) -> (list, list):
    assert isinstance(data_directory, str)
    assert isinstance(pictures_distances, dict)
    assert isinstance(batch_size, int)
    assert isinstance(start, int)
    pictures_ids = list(pictures_distances.keys())[start:start+batch_size]
    pictures = []
    distances = []
    for picture_id in pictures_ids:
        picture = load_picture(os.path.join(data_directory, 'IMG_' + picture_id + '.jpg'))
        pictures.append(picture)
        distances.append(pictures_distances[picture_id])
    return pictures, distances


def get_pictures_distances(directory) -> dict:
    with open(os.path.join(directory, DISTANCES_FILE)) as distances_file:
        pictures_ids_distances = {}
        for line in csv.reader(distances_file):
            pictures_ids_distances[line[0]] = np.array(line[1:], dtype=np.float16)
        return pictures_ids_distances


def mirrored_data(pictures, distances) -> (list, list):
    assert isinstance(pictures, list)
    assert isinstance(distances, list)
    return [np.fliplr(picture) for picture in pictures], [np.flip(distance, 0) for distance in distances]


def train_conv_net(conv_net, iterations, pictures_distances, train_batch_size, dropouts, directory='.', model_path=os.path.realpath('CNN')):
    assert isinstance(conv_net, dict)
    assert isinstance(train_batch_size, int)
    assert isinstance(dropouts, list)
    assert isinstance(directory, str)
    assert isinstance(model_path, str)
    labels = tf.placeholder(tf.float32, shape=conv_net['output'].get_shape())
    with tf.name_scope('Cost'):
        difference = tf.losses.absolute_difference(predictions=conv_net['output'], labels=labels)
        cost = tf.reduce_mean(difference, name='cost')
        tf.summary.scalar(cost.name, cost)
    optimizer = tf.train.RMSPropOptimizer(learning_rate=0.001, momentum=0.5, epsilon=0.001)
    train_step = optimizer.minimize(cost)
    with tf.name_scope('Accuracy'):
        correct_predictions = tf.less_equal(difference, tf.constant(TOLERATED_ERROR))  # Error tolerance
        accuracy = tf.reduce_mean(tf.cast(correct_predictions, tf.float32), name='accuracy')
        tf.summary.scalar(accuracy.name, accuracy)
    merged_summaries = tf.summary.merge_all()
    variables_saver = tf.train.Saver()
    print('Beginning session...')
    with tf.Session() as session:
        with session.as_default():
            # Look for the checkpoint to find the global step
            checkpoint_file_path = os.path.join(os.path.dirname(model_path), 'checkpoint')
            if tf.gfile.Exists(checkpoint_file_path):
                with open(checkpoint_file_path) as checkpoint:
                    model_path_line = checkpoint.readline()
                    restore_file_path = model_path_line.split(" ")[-1].strip('\n"')
                    last_global_step = int(restore_file_path.split('-')[-1])
                    variables_saver.restore(session, restore_file_path)
                    print('Variables restored')
            else:
                last_global_step = 0
                tf.global_variables_initializer().run()
                print('Variables initialised')
            log_dir = model_path+'-log'
            if not tf.gfile.Exists(log_dir):
                # tf.gfile.DeleteRecursively(log_dir)
                tf.gfile.MakeDirs(log_dir)
            train_summary_writer = tf.summary.FileWriter(os.path.join(log_dir, 'train'), session.graph)
            validation_summary_writer = tf.summary.FileWriter(os.path.join(log_dir, 'validation'), session.graph)
            print('Loading the data...')
            train_set, validation_set, test_set = get_train_validation_test_sets(pictures_distances)
            print('Data = {} : train = {}, validation = {}, test = {}'.format(
                len(pictures_distances), len(train_set), len(validation_set), len(test_set))
            )
            print('Beginning training...')
            pictures_val, distances_val = next_batch(directory, validation_set, len(validation_set), 0)
            for i in range(last_global_step, iterations):
                print('Step', i+1)
                total_train_loss = 0
                sum_train_accuracy = 0
                offset = 0
                folds = 0
                while offset < len(train_set):
                    pictures_train, distances_train = next_batch(directory, train_set, train_batch_size, offset)
                    pictures_train_mirrored, distances_train_mirrored = mirrored_data(pictures_train, distances_train)
                    pictures_train_mixed = np.concatenate((pictures_train, pictures_train_mirrored))
                    distances_train_mixed = np.concatenate((distances_train, distances_train_mirrored))
                    _, cost_value, accuracy_value, train_summary = session.run(
                        [train_step, cost, accuracy, merged_summaries],
                        feed_dict={conv_net['input']: pictures_train_mixed, labels: distances_train_mixed,
                                   conv_net['dropouts'][0]: dropouts[0]}
                    )
                    total_train_loss += cost_value
                    sum_train_accuracy += accuracy_value
                    train_summary_writer.add_summary(train_summary)
                    folds += 1
                    offset += len(pictures_train)
                val_loss, val_accuracy, val_summary = session.run(
                    [cost, accuracy, merged_summaries],
                    feed_dict={conv_net['input']: pictures_val, labels: distances_val}
                )
                print("Loss : Train = {:.4f} , Validation = {:.4f} | Accuracy with {}m tolerance : Train = {:.4f}, Validation = {:.4f}"
                      .format(total_train_loss / folds, val_loss, TOLERATED_ERROR, sum_train_accuracy / folds, val_accuracy))
                validation_summary_writer.add_summary(val_summary)
                variables_saver.save(session, model_path, i+1, max_to_keep=3)
            train_summary_writer.close()
            validation_summary_writer.close()
            print('Training finished')
            print('Test...')
            pictures_test, distances_test = next_batch(directory, test_set, len(test_set), 0)
            print("Loss = {0:.4f} | Accuracy with {2}m tolerance = {1:.4f}".format(
                *session.run([cost, accuracy], feed_dict={conv_net['input']: pictures_test, labels: distances_test}),
                TOLERATED_ERROR
            ))


def main():
    directory = '.'
    if len(sys.argv) == 2:
        directory = sys.argv[1]
    print('Constructing model...')
    cnn = convolutional_neural_network(96, 96, 3, OrderedDict(
        [
            ('Convolutional_layer_1', {
                'field_size': 3,
                'stride_size': 1,
                'padding': 'SAME',
                'depth': 16
            }),
            ('Convolutional_layer_2', {
                'field_size': 3,
                'stride_size': 1,
                'padding': 'SAME',
                'depth': 16
            }),
            ('Pooling_layer_1', {
                'field_size': 2,
                'stride_size': 2,
                'padding': 'VALID'
            }),
            ('Convolutional_layer_3', {
                'field_size': 3,
                'stride_size': 1,
                'padding': 'SAME',
                'depth': 32
            }),
            ('Convolutional_layer_4', {
                'field_size': 3,
                'stride_size': 1,
                'padding': 'SAME',
                'depth': 32
            }),
            ('Pooling_layer_2', {
                'field_size': 2,
                'stride_size': 2,
                'padding': 'VALID'
            }),
            ('Fully_connected', {
                'depth': 64,
                'dropout_keep': 0.7
            }),
            ('Readout', {
                'depth': 7
            }),
        ]
    ))
    with tf.Session().as_default():
        train_conv_net(cnn, 20, get_pictures_distances(directory), 50, [0.7], directory, os.path.realpath('CNN-C16C16PC32C32PF64O7'))


if __name__ == '__main__':
    main()
