#!/usr/bin/env python3
import os
import sys
import random
import tensorflow as tf

PICTURE_HEIGHT = 96
PICTURE_WIDTH = 96
DISTANCES_FILE = 'Distances.txt'


def convolutional_neural_network(picture_height, picture_width, picture_channels):

    def weight_variable(shape):
        weights = tf.Variable(tf.truncated_normal(shape, stddev=0.1, dtype=tf.float32), name='weights')
        tf.summary.histogram(weights.name, weights)
        return weights

    def bias_variable(shape):
        biases = tf.Variable(tf.constant(0.1, shape=shape, dtype=tf.float32), name='biases')
        tf.summary.histogram(biases.name, biases)
        return biases

    field_size = 3
    stride_size = 1
    padding = 'SAME'
    pooling_size = 2
    pooling_stride = 2
    pooling_padding = 'VALID'

    with tf.name_scope('Input'):
        input_data = tf.placeholder(tf.float32, shape=[None, picture_height, picture_width, picture_channels], name='input')
    # Convolutional layer 1
    with tf.name_scope('ConvolutionalLayer1'):
        depth1 = 16
        layer1_parameters = {'weights': weight_variable([field_size, field_size, picture_channels, depth1]),
                             'biases': bias_variable([depth1])}
        conv_layer1 = tf.nn.relu(
            tf.nn.bias_add(tf.nn.conv2d(input_data, layer1_parameters['weights'],
                                        strides=[1, stride_size, stride_size, 1],
                                        padding=padding), layer1_parameters['biases']), 'conv1')
        tf.summary.histogram(conv_layer1.name, conv_layer1)
    print(conv_layer1)
    # Convolutional layer 2
    with tf.name_scope('ConvolutionalLayer2'):
        depth2 = 32
        layer2_parameters = {'weights': weight_variable([field_size, field_size, depth1, depth2]),
                             'biases': bias_variable([depth2])}
        conv_layer2 = tf.nn.relu(
            tf.nn.bias_add(tf.nn.conv2d(conv_layer1, layer2_parameters['weights'],
                                        strides=[1, stride_size, stride_size, 1],
                                        padding=padding), layer2_parameters['biases']), name='conv2')
        tf.summary.histogram(conv_layer2.name, conv_layer2)
    print(conv_layer2)
    # Pooling layer 1
    with tf.name_scope('PoolingLayer1'):
        pooling_layer1 = tf.nn.max_pool(conv_layer2, ksize=[1, pooling_size, pooling_size, 1],
                                        strides=[1, pooling_stride, pooling_stride, 1], padding=pooling_padding,
                                        name='pool1')
        tf.summary.histogram(pooling_layer1.name, pooling_layer1)
    print(pooling_layer1)
    # Convolutional layer 3
    with tf.name_scope('ConvolutionalLayer3'):
        depth3 = 32
        layer3_parameters = {'weights': weight_variable([field_size, field_size, depth2, depth3]),
                             'biases': bias_variable([depth3])}
        conv_layer3 = tf.nn.relu(
            tf.nn.bias_add(tf.nn.conv2d(pooling_layer1, layer3_parameters['weights'],
                                        strides=[1, stride_size, stride_size, 1], padding=padding),
                           layer3_parameters['biases']), name='conv3')
        tf.summary.histogram(conv_layer3.name, conv_layer3)
    print(conv_layer3)
    # Convolutional layer 4
    with tf.name_scope('ConvolutionalLayer4'):
        depth4 = 64
        layer4_parameters = {'weights': weight_variable([field_size, field_size, depth3, depth4]),
                             'biases': bias_variable([depth4])}
        conv_layer4 = tf.nn.relu(
            tf.nn.bias_add(tf.nn.conv2d(conv_layer3, layer4_parameters['weights'], strides=[1, stride_size, stride_size, 1],
                                        padding=padding),
                           layer4_parameters['biases']), name='conv4')
        tf.summary.histogram(conv_layer4.name, conv_layer4)
    print(conv_layer4)
    # Pooling layer 1
    with tf.name_scope('PoolingLayer2'):
        pooling_layer2 = tf.nn.max_pool(conv_layer4, ksize=[1, pooling_size, pooling_size, 1],
                                        strides=[1, pooling_stride, pooling_stride, 1], padding=pooling_padding,
                                        name='pool2')
        tf.summary.histogram(pooling_layer2.name, pooling_layer2)
        print(pooling_layer2)
    # Fully connected layer
    with tf.name_scope('FullyConnectedLayer'):
        fc_depth = 64
        flatted_pooling_dim = int(pooling_layer2.shape[1]) * int(pooling_layer2.shape[2]) * depth4
        flatted_pooling_layer2 = tf.reshape(pooling_layer2, [-1, flatted_pooling_dim])
        layer5_parameters = {'weights': weight_variable([flatted_pooling_dim, fc_depth]),
                             'biases': bias_variable([fc_depth])}
        default_keep_factor = tf.constant(1, tf.float32)
        dropout_keep_factor = tf.placeholder_with_default(default_keep_factor, default_keep_factor.get_shape())
        dense_layer = tf.nn.relu(tf.nn.bias_add(tf.matmul(flatted_pooling_layer2, layer5_parameters['weights']),
                                                layer5_parameters['biases']), name='dense')
        dropout_layer = tf.nn.dropout(dense_layer, dropout_keep_factor, name='dropout')
        tf.summary.histogram(dropout_layer.name, dropout_layer)
    print(dropout_layer)
    # Output layer
    with tf.name_scope('ReadoutLayer'):
        classes = 41  # 40 possibles distances with a resolution of 0.1m + 1 for unknown distances
        output_layer_parameters = {'weights': weight_variable([fc_depth, classes]),
                                   'biases': bias_variable([classes])}
        output_layer = tf.nn.bias_add(tf.matmul(dropout_layer, output_layer_parameters['weights']),
                                      output_layer_parameters['biases'], name='output')
        tf.summary.histogram(output_layer.name, output_layer)
    print(output_layer)
    return input_data, output_layer, dropout_keep_factor


def load_picture(file_name, height, width):
    picture_raw = tf.read_file(file_name)
    picture = tf.cast(tf.image.decode_jpeg(picture_raw, channels=3), tf.float32)
    picture.set_shape([height, width, 3])
    return picture.eval()


def get_train_validation_test_sets(pictures_distances):
    assert isinstance(pictures_distances, dict)
    pictures_file_names = list(pictures_distances.keys())
    random.shuffle(pictures_file_names)  # Randomly reorders the file names
    train_size = int(0.8*len(pictures_file_names))
    validation_size = int(0.1*len(pictures_file_names))
    train_files = pictures_file_names[:train_size]
    validation_files = pictures_file_names[train_size:train_size+validation_size]
    test_files = pictures_file_names[train_size+validation_size:]
    pictures_distances_train = dict((x, pictures_distances[x]) for x in train_files)
    pictures_distances_validation = dict((x, pictures_distances[x]) for x in validation_files)
    pictures_distances_test = dict((x, pictures_distances[x]) for x in test_files)
    return pictures_distances_train, pictures_distances_validation, pictures_distances_test


def random_batch(pictures_distances, batch_size):
    assert isinstance(pictures_distances, dict)
    pictures_files = random.sample(list(pictures_distances.keys()), k=batch_size)
    pictures = []
    distances = []
    for file_name in pictures_files:
        picture = load_picture(file_name, PICTURE_HEIGHT, PICTURE_WIDTH)
        pictures.append(picture)
        distance = pictures_distances[file_name]
        if 0 < distance <= 4:
            distances.append(tf.one_hot(int(round(distance, 1)/0.1), 41).eval())
        else:
            distances.append(tf.one_hot(40, 41).eval())
    return pictures, distances


def get_pictures_distances(directory='.'):
    pictures_file_names = sorted([os.path.join(directory, x) for x in os.listdir(directory)
                                  if x.lower().endswith('.jpg') or x.lower().endswith('.jpeg')])
    with open(os.path.join(directory, DISTANCES_FILE)) as distances_file:
        distances = [float(line) for line in distances_file]
    return dict((pict, dist) for pict, dist in zip(pictures_file_names, distances))


def train(conv_net, pictures_distances, train_batch_size, dropout, model_path=os.path.realpath('CNN')):
    labels = tf.placeholder(tf.float32, shape=[None, 41])
    with tf.name_scope('Cross-entropy'):
        cross_entropy = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=conv_net[1], labels=labels),
                                       name='cost')
        tf.summary.scalar(cross_entropy.name, cross_entropy)
    optimizer = tf.train.RMSPropOptimizer(learning_rate=0.001, momentum=0.5, epsilon=0.001)
    train_step = optimizer.minimize(cross_entropy)
    with tf.name_scope('Accuracy'):
        correct_predictions = tf.equal(tf.argmax(conv_net[1], 1), tf.argmax(labels, 1))
        accuracy = tf.reduce_mean(tf.cast(correct_predictions, tf.float32), name='accuracy')
        tf.summary.scalar(accuracy.name, accuracy)
    merged_summaries = tf.summary.merge_all()
    variables_saver = tf.train.Saver()
    print('Beginning session...')
    with tf.Session() as session:
        with session.as_default():
            if tf.gfile.Exists(os.path.join(os.path.dirname(model_path), 'checkpoint')):
                variables_saver.restore(session, model_path)
                print('Variables restored')
            else:
                tf.global_variables_initializer().run()
                print('Variables initialised')
            log_dir = os.path.join(os.path.dirname(model_path), 'log')
            if tf.gfile.Exists(log_dir):
                tf.gfile.DeleteRecursively(log_dir)
            tf.gfile.MakeDirs(log_dir)
            summary_writer = tf.summary.FileWriter(log_dir, session.graph)
            train_set, validation_set, test_set = get_train_validation_test_sets(pictures_distances)
            print('Beginning training...')
            pictures_val, distances_val = random_batch(validation_set, len(validation_set))
            for i in range(50):
                pictures, distances = random_batch(train_set, train_batch_size)
                print('Step {}'.format(i+1))
                train_loss, train_accuracy, train_summary = session.run([cross_entropy, accuracy, merged_summaries],
                                                                        feed_dict={conv_net[0]: pictures,
                                                                                   labels: distances})
                val_loss, val_accuracy, val_summary = session.run([cross_entropy, accuracy, merged_summaries],
                                                                  feed_dict={conv_net[0]: pictures_val,
                                                                             labels: distances_val})
                print("Loss : Train = {:.4f} , Validation = {:.4f} | Accuracy : Train = {:.4f}, Validation = {:.4f}"
                      .format(train_loss, val_loss, train_accuracy, val_accuracy))
                summary_writer.add_summary(val_summary)
                summary_writer.add_summary(train_summary)
                variables_saver.save(session, model_path)
                train_step.run(feed_dict={conv_net[0]: pictures, labels: distances, conv_net[2]: dropout})
            summary_writer.close()
            print('Training finished')
            pictures_test, distances_test = random_batch(test_set, len(test_set))
            print('Test')
            print("Loss = {:.4f} | Accuracy = {:.4f}".format(
                cross_entropy.eval(feed_dict={conv_net[0]: pictures_test, labels: distances_test}),
                accuracy.eval(feed_dict={conv_net[0]: pictures_test, labels: distances_test})
            ))


def main():
    directory = '.'
    if len(sys.argv) == 2:
        directory = sys.argv[1]
    print('Constructing model...')
    cnn = convolutional_neural_network(PICTURE_HEIGHT, PICTURE_WIDTH, 3)
    train(cnn, get_pictures_distances(directory), 50, 0.7)
if __name__ == '__main__':
    main()
