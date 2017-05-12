#!/usr/bin/env python3

"""
Module containing the necessary functions to generate and load the datasets
and to build and train the convolutional neural networks.

Hamza Abbad
"""

import os
import sys
import random
import csv
from numbers import Real, Integral
from collections import OrderedDict

import tensorflow as tf
import numpy as np

DISTANCES_FILE = 'Distances.txt'


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
    variables = []
    for layer_name, layer_parameters in layers.items():
        assert isinstance(layer_parameters, dict)
        with tf.name_scope(layer_name):
            if len(layer_parameters) > 3:  # More than 3 hyper-parameters : convolutional layer
                assert 'field_size' in layer_parameters and isinstance(layer_parameters['field_size'], int)
                assert 'stride_size' in layer_parameters and isinstance(layer_parameters['stride_size'], int)
                assert 'padding' in layer_parameters and layer_parameters['padding'] in ('SAME', 'VALID')
                assert 'depth' in layer_parameters and isinstance(layer_parameters['depth'], int)
                W = weights([layer_parameters['field_size']] * 2 + [int(previous_layer.shape[3]), layer_parameters['depth']])
                b = biases([layer_parameters['depth']])
                variables += [W, b]
                current_layer = tf.nn.relu(
                    tf.nn.bias_add(
                        tf.nn.conv2d(previous_layer,
                                     W,
                                     strides=[1] + [layer_parameters['stride_size']] * 2 + [1],
                                     padding=layer_parameters['padding']),
                        b
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
                dropout_keep_factor = tf.placeholder_with_default(1.0, ())
                dropouts.append(dropout_keep_factor)
                W = weights([flatted_previous_dim, layer_parameters['depth']])
                b = biases([layer_parameters['depth']])
                variables += [W, b]
                dense_layer = tf.nn.relu(
                    tf.nn.bias_add(
                        tf.matmul(flatted_previous_layer, W),
                        b
                    )
                )
                current_layer = tf.nn.dropout(dense_layer, dropout_keep_factor)
        previous_layer = current_layer

    return {'input': input_layer, 'output': previous_layer, 'dropouts': dropouts, 'variables': variables}


def get_train_validation_test_sets(pictures_distances, train_percent, validation_rest_percent) -> (dict, dict, dict):
    """
    Generate the training, the validation and the testing datasets from the original one.  
    :param pictures_distances: a dictionary with pictures IDs (str) as keys and distances as values.
    :param train_percent: the ratio of the training examples compared to the original dataset.
    :param validation_rest_percent: the ratio of the validation examples compared to the rest of the examples.
    :return: 3 dictionaries representing the training, validation and testing datasets, respectively.
    """

    assert isinstance(pictures_distances, dict)
    assert isinstance(train_percent, Real)
    assert isinstance(validation_rest_percent, Real)
    pictures_ids = list(pictures_distances.keys())
    random.shuffle(pictures_ids)  # Randomly reorders the file names
    train_size = round(train_percent * len(pictures_ids))
    validation_size = round((len(pictures_ids) - train_size) * validation_rest_percent)
    train_ids = pictures_ids[:train_size]
    validation_ids = pictures_ids[train_size:train_size+validation_size]
    test_ids = pictures_ids[train_size+validation_size:]
    pictures_distances_train = dict((x, pictures_distances[x]) for x in train_ids)
    pictures_distances_validation = dict((x, pictures_distances[x]) for x in validation_ids)
    pictures_distances_test = dict((x, pictures_distances[x]) for x in test_ids)
    return pictures_distances_train, pictures_distances_validation, pictures_distances_test


def load_picture(file_name, gray, resize_factor, integers=False):
    """
    Load a picture from file and return its content as 3D NumPy array.  
    :param integers: whether the pixels values should be kept as uint8 
    :param file_name: the path of the file.
    :param gray: whether the picture is converted to grayscale or not.
    :param resize_factor: the scaling factor : 1, 2, 4, or 8.
    :return: ndarray representing the content of the picture.
    """
    picture_raw = tf.read_file(file_name)
    picture = tf.image.decode_jpeg(picture_raw, channels=(1 if gray else 3), ratio=resize_factor)
    if not integers:
        picture = tf.image.convert_image_dtype(picture, tf.float32)
    picture_content = picture.eval()
    return picture_content


def get_batches(data_directory, pictures_distances, batch_size, classes, grayscale=False, downscale_factor=1) -> list:
    assert isinstance(data_directory, str)
    assert isinstance(pictures_distances, dict)
    assert isinstance(batch_size, Integral)
    assert isinstance(grayscale, bool)
    assert isinstance(downscale_factor, Integral)
    pictures_ids = list(pictures_distances.keys())
    batches = []
    npz_files = list(filter(lambda x: x.startswith('batch_{}^{:d}~{}#{}-'.format(downscale_factor, grayscale, classes, batch_size)) and x.endswith('.npz'), os.listdir(data_directory)))
    if len(npz_files) > 0:  # Batches are saved as NumPy arrays ! this is awesome !
        for npz_filename in npz_files:
            batch = np.load(os.path.join(data_directory, npz_filename), allow_pickle=False)
            batches.append((batch['pictures'], batch['distances']))
    else:  # Oh no ! we have to load all images one by one, this will take a while.
        with tf.Session() as session:
            with session.as_default():
                offset = 0
                while offset < len(pictures_distances):
                    pictures_batch = []
                    distances_batch = []
                    for picture_id in pictures_ids[offset:offset+batch_size]:
                        picture = load_picture(os.path.join(data_directory, 'IMG_' + picture_id + '.jpg'), grayscale, downscale_factor)
                        pictures_batch.append(picture)
                        if classes > 1:
                            distances_batch.append(tf.one_hot(np.uint8(pictures_distances[picture_id] / 4.5 * (classes - 1)), classes).eval())
                        else:
                            distances_batch.append(np.array([pictures_distances[picture_id]]))
                    batch = (np.stack(pictures_batch), np.stack(distances_batch))
                    batches.append(batch)
                    offset += len(pictures_batch)
        i = 1
        for batch in batches:
            np.savez(os.path.join(data_directory, 'batch_{}^{:d}~{}#{}-{:03d}'.format(downscale_factor, grayscale, classes, batch_size, i)), pictures=batch[0], distances=batch[1])
            i += 1
    return batches


def get_pictures_distances(directory) -> dict:
    assert isinstance(directory, str)
    with open(os.path.join(directory, DISTANCES_FILE)) as distances_file:
        pictures_ids_distances = {}
        for line in csv.reader(distances_file):
            distances = np.array(line[1:], dtype=np.float32)
            distances[distances >= 4.5] = np.nan  # Unknown distance
            if not np.all(np.isnan(distances)):  # There is at least one known distance
                # pictures_ids_distances[line[0]] = np.nanmedian(distances, keepdims=True)
                pictures_ids_distances[line[0]] = np.nanmedian(distances)
            else:
                pictures_ids_distances[line[0]] = 4.5
        return pictures_ids_distances


def mirrored_data(pictures, distances) -> (np.ndarray, np.ndarray):
    assert isinstance(pictures, np.ndarray)
    assert isinstance(distances, np.ndarray)
    return np.flip(pictures, 2), distances


def balanced_data_min(pictures_distances, classes) -> dict:
    assert isinstance(pictures_distances, dict)
    distances = np.asarray(list(pictures_distances.values()))
    all_labels, counts = np.unique(np.uint8(distances / 4.5 * (classes-1)), return_counts=True)
    groups_min = np.min(counts)
    pictures_groups = {}
    counters = [0 for x in all_labels]
    for p, d in pictures_distances.items():
        if all(x >= groups_min for x in counters):
            break
        label = int(d / 4.5 * (classes - 1))
        if counters[label] < groups_min:
            pictures_groups[p] = d
            counters[label] += 1
    return pictures_groups


def get_saved_model_path_and_last_step(checkpoint_file_path):
    with open(checkpoint_file_path) as checkpoint:
        model_path_line = checkpoint.readline()
    # Initialise the global step to the last one of the previous run
    restore_file_path = model_path_line.split(" ")[-1].strip('\n"')
    last_global_step = int(restore_file_path.split('-')[-1])
    return restore_file_path, last_global_step


def train_conv_net(conv_net, iterations, dropouts, train_batches, validation_batch=None, test_batch=None, accepted_error=0, accepted_accuracy=0.95, data_directory='.', model_path=os.path.realpath('CNN'), expand_data=True, learning_rate=0.001, logger=None):
    assert isinstance(conv_net, dict)
    assert isinstance(dropouts, list)
    assert isinstance(data_directory, str)
    assert isinstance(model_path, str)
    assert isinstance(iterations, Integral)
    assert isinstance(expand_data, bool)
    assert isinstance(accepted_error, Real)
    assert isinstance(learning_rate, Real)

    pictures_val, distances_val = validation_batch if validation_batch else (None, None)
    pictures_test, distances_test = test_batch if test_batch else (None, None)

    regression = int(conv_net['output'].get_shape()[1]) == 1

    print('Regression problem' if regression else 'Classification problem')

    print('Setting up the graph...')
    labels = tf.placeholder(tf.float32, shape=conv_net['output'].get_shape())
    with tf.name_scope('Cost'):
        if regression:
            difference = tf.abs(tf.subtract(conv_net['output'], labels))
        else:
            difference = tf.nn.softmax_cross_entropy_with_logits(logits=conv_net['output'], labels=labels)
        cost = tf.reduce_mean(difference, name='cost')
        tf.summary.scalar(cost.name, cost)
    optimizer = tf.train.AdadeltaOptimizer(learning_rate=learning_rate)
    train_step = optimizer.minimize(loss=cost, var_list=conv_net['variables'])
    with tf.name_scope('Accuracy'):
        if regression:
            correct_predictions = tf.less_equal(difference, tf.constant(accepted_error))  # Error tolerance
        else:
            correct_predictions = tf.equal(tf.argmax(labels, 1), tf.argmax(conv_net['output'], 1))
        accuracy = tf.reduce_mean(tf.cast(correct_predictions, tf.float32), name='accuracy')
        tf.summary.scalar(accuracy.name, accuracy)
    merged_summaries = tf.summary.merge_all()
    variables_saver = tf.train.Saver(var_list=conv_net['variables'], max_to_keep=3)
    log_dir = model_path + '-log'
    if not tf.gfile.Exists(log_dir):
        tf.gfile.MakeDirs(log_dir)
    train_summary_writer = tf.summary.FileWriter(os.path.join(log_dir, 'train'), tf.get_default_graph())
    validation_summary_writer = tf.summary.FileWriter(os.path.join(log_dir, 'validation'), tf.get_default_graph())
    # Look for the checkpoint to find the last global step
    checkpoint_file_path = os.path.join(os.path.dirname(model_path), 'checkpoint')
    last_global_step = 0
    with tf.Session() as session:
        with session.as_default():
            tf.global_variables_initializer().run()
            print('Variables initialised')
            if tf.gfile.Exists(checkpoint_file_path):
                restore_file_path, last_global_step = get_saved_model_path_and_last_step(checkpoint_file_path)
                variables_saver.restore(tf.get_default_session(), restore_file_path)
                print('Variables restored')
            if pictures_val is not None:
                val_loss, val_accuracy = session.run([cost, accuracy], feed_dict={conv_net['input']: pictures_val, labels: distances_val})
                val_text = 'Initial validation : loss = {:.4f}, accuracy = {:.4f}'.format(val_loss, val_accuracy)
                print(val_text)
                if logger:
                    logger.log_text(val_text)
            print('Beginning training...')
            train_summary = None
            i = 0
            for i in range(last_global_step+1, iterations+1):
                try:
                    print('Step', i)
                    train_loss = 0
                    train_accuracy = 0
                    for pictures_train, distances_train in train_batches:
                        if expand_data:
                            pictures_train_mirrored, distances_train_mirrored = mirrored_data(pictures_train, distances_train)
                            pictures_train_mixed = np.concatenate((pictures_train, pictures_train_mirrored))
                            distances_train_mixed = np.concatenate((distances_train, distances_train_mirrored))
                        else:
                            pictures_train_mixed = pictures_train
                            distances_train_mixed = distances_train
                        arguments = {conv_net['input']: pictures_train_mixed, labels: distances_train_mixed}
                        if dropouts:
                            for dropout_tensor, dropout_keep_value in zip(conv_net['dropouts'], dropouts):
                                arguments.update({dropout_tensor: dropout_keep_value})
                        _, train_loss, train_accuracy, train_summary = session.run(
                            [train_step, cost, accuracy, merged_summaries],
                            feed_dict=arguments
                        )
                    if not regression:
                        print('Training : loss = {:.4f}, accuracy = {:.4f}'.format(train_loss, train_accuracy))
                    else:
                        print('Training : loss = {:.4f}, accuracy with {}m error tolerance = {:.4f}'.format(
                            train_loss, accepted_error, train_accuracy))
                    variables_saver.save(session, model_path, i)
                    if train_summary is not None:
                        train_summary_writer.add_summary(train_summary, i)
                    if pictures_val is not None:
                        val_loss, val_accuracy, val_summary = session.run(
                            [cost, accuracy, merged_summaries],
                            feed_dict={conv_net['input']: pictures_val, labels: distances_val}
                        )
                        if not regression:
                            val_text = "Validation : loss = {:.4f}, accuracy = {:.4f}".format(val_loss, val_accuracy)
                        else:
                            val_text = "Validation : loss = {:.4f}, accuracy with {}m error tolerance = {:.4f}".format(val_loss, accepted_error, val_accuracy)
                        print(val_text)
                        if logger:
                            logger.log_text(val_text)
                        validation_summary_writer.add_summary(val_summary, i)
                        if val_loss <= accepted_error or val_accuracy >= accepted_accuracy:  # Accepted
                            break
                except KeyboardInterrupt:
                    break
            train_summary_writer.close()
            validation_summary_writer.close()
            if i >= iterations:
                end_msg = 'Training finished'
            else:
                end_msg = 'Training interrupted'
            print(end_msg)
            if logger:
                logger.log_text(end_msg)
            if pictures_test is not None:
                print('Test...')
                if not regression:
                    test_text = "Loss = {0:.4f} | Accuracy = {1:.4f}".format(
                        *session.run([cost, accuracy], feed_dict={conv_net['input']: pictures_test, labels: distances_test}))
                else:
                    test_text = "Loss = {0:.4f} | Accuracy with {2}m tolerance = {1:.4f}".format(
                        *session.run([cost, accuracy], feed_dict={conv_net['input']: pictures_test, labels: distances_test}),
                        accepted_error
                    )
                print(test_text)
                if logger:
                    logger.log_text(test_text)


def generate_datasets(original_directory, destination_directory, train_ratio=0.8, validation_rest_ratio=0.5):
    train_dir = os.path.join(destination_directory, 'train')
    val_dir = os.path.join(destination_directory, 'validation')
    test_dir = os.path.join(destination_directory, 'test')
    pictures_distances = {}
    with open(os.path.join(original_directory, DISTANCES_FILE)) as original_distances_file:
        for line in original_distances_file:
            picture_id, distances = line.split(',', 1)
            pictures_distances[picture_id] = distances
    train, val, test = get_train_validation_test_sets(pictures_distances, train_ratio, validation_rest_ratio)
    if train_ratio > 0:
        if not os.path.exists(train_dir):
            os.mkdir(train_dir)
        with open(os.path.join(train_dir, DISTANCES_FILE), 'x') as destination_distances_file:
            for picture_id, distances in train.items():
                print(picture_id, distances, sep=',', end='', file=destination_distances_file)
                os.link(os.path.join(original_directory, 'IMG_'+picture_id+'.jpg'), os.path.join(train_dir, 'IMG_'+picture_id+'.jpg'))
    if validation_rest_ratio > 0:
        if not os.path.exists(val_dir):
            os.mkdir(val_dir)
        with open(os.path.join(val_dir, DISTANCES_FILE), 'x') as destination_distances_file:
            for picture_id, distances in val.items():
                print(picture_id, distances, sep=',', end='', file=destination_distances_file)
                os.link(os.path.join(original_directory, 'IMG_' + picture_id + '.jpg'), os.path.join(val_dir, 'IMG_'+picture_id + '.jpg'))
    if validation_rest_ratio < 1:
        if not os.path.exists(test_dir):
            os.mkdir(test_dir)
        with open(os.path.join(test_dir, DISTANCES_FILE), 'x') as destination_distances_file:
            for picture_id, distances in test.items():
                print(picture_id, distances, sep=',', end='', file=destination_distances_file)
                os.link(os.path.join(original_directory, 'IMG_'+picture_id+'.jpg'), os.path.join(test_dir, 'IMG_'+picture_id+'.jpg'))


def link_data(source, destination, start, end):
    with open(os.path.join(destination, DISTANCES_FILE), 'a') as dst_file:
        with open(os.path.join(source, DISTANCES_FILE)) as src_file:
            for line in src_file:
                file_id = line.split(',', 1)[0]
                if start <= file_id <= end:
                    dst_file.write(line)
                    os.link(os.path.join(source, 'IMG_'+file_id+'.jpg'), os.path.join(destination, 'IMG_'+file_id+'.jpg'))


def main(args):
    model_file_name = args[1]
    data_dir = args[2]
    # print('Constructing model of', model_file_name, '...')
    # with open(model_file_name+'.json') as cnn_json_file:
    #     import json
    #     cnn = convolutional_neural_network(96, 96, 1, json.load(cnn_json_file, object_pairs_hook=OrderedDict))
    # print('Variables')
    # for variable in cnn['variables']:
    #     print(variable)
    train_dir = os.path.join(data_dir, 'train')
    val_dir = os.path.join(data_dir, 'validation')
    # downscale = 1
    # grayscale = int(cnn['input'].get_shape()[3]) == 1  # The size of the depth dimension is 1
    # classes = int(cnn['output'].get_shape()[1])
    # print('Loading training data ...')
    train = get_pictures_distances(train_dir)
    print(len(balanced_data_min(train, 4)))
    # train_batches = get_batches(train_dir, train, 200, grayscale=grayscale, downscale_factor=downscale, classes=classes)
    # print('Loading validation data ...')
    # val = get_pictures_distances(val_dir)
    # val_batch = get_batches(val_dir, val, len(val), grayscale=grayscale, downscale_factor=downscale, classes=classes)[0]
    # print('Data : training = {}, validation = {}'.format(len(train), len(val)))
    # train_conv_net(conv_net=cnn,
    #                train_batches=train_batches,
    #                validation_batch=val_batch,
    #                iterations=300,
    #                dropouts=[],
    #                data_directory=data_dir,
    #                model_path=os.path.join(os.path.realpath(model_file_name), 'CNN'),
    #                learning_rate=0.001,
    #                expand_data=True,
    #                )


if __name__ == '__main__':
    # try:
    #     generate_datasets(sys.argv[2], sys.argv[2], 0.8, 1)
    #     print('Datasets generated')
    # except FileExistsError:
    #     print('Datasets already exist')
    picts_dists = get_pictures_distances(os.path.join(sys.argv[2], 'validation'))
    bd = balanced_data_min(picts_dists, 4)
    print(len(bd))
    # main(sys.argv)
    # link_data('../../Data/Info-TP', '../../Data/Info-TP-Pass', '', '9999999999999')
    # link_data('../../Data/Info-Pass', '../../Data/Info-TP-Pass', '', '9999999999999')
