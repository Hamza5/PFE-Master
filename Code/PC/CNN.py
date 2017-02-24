#!/usr/bin/env python3
import os
import sys
import random
import tensorflow as tf

PICTURE_HEIGHT = 100
PICTURE_WIDTH = 100
DISTANCES_FILE = 'Distances.txt'


def convolutional_neural_network(picture_height, picture_width, picture_channels):

    def weight_variable(shape):
        return tf.Variable(tf.truncated_normal(shape, stddev=0.1))

    def bias_variable(shape):
        return tf.Variable(tf.constant(0.1, shape=shape))

    input_data = tf.placeholder(tf.float32, shape=[None, picture_height, picture_width, picture_channels])
    field_size = 5
    strides = [1, 1, 1, 1]
    padding = 'SAME'
    pooling_size = 2
    # Convolutional layer 1
    depth1 = 32
    layer1_parameters = {'weights': weight_variable([field_size, field_size, picture_channels, depth1]),
                         'biases': bias_variable([depth1])}
    conv_layer1 = tf.nn.relu(
        tf.nn.bias_add(tf.nn.conv2d(input_data, layer1_parameters['weights'], strides=strides, padding=padding),
                       layer1_parameters['biases']),
        name='ConvLayer1')
    # Convolutional layer 2
    depth2 = 64
    layer2_parameters = {'weights': weight_variable([field_size, field_size, depth1, depth2]),
                         'biases': bias_variable([depth2])}
    conv_layer2 = tf.nn.relu(
        tf.nn.bias_add(tf.nn.conv2d(conv_layer1, layer2_parameters['weights'], strides=strides, padding=padding),
                       layer2_parameters['biases']),
        name='ConvLayer2')
    # Pooling layer
    pooling_layer1 = tf.nn.max_pool(conv_layer2, ksize=[1, pooling_size, pooling_size, 1], strides=strides, padding='VALID', name='PoolLayer')
    # Fully connected layer
    neurons = 41  # 40 possibles distances with a resolution of 0.1m + 1 for unknown distances
    flatted_pooling_dim = int(pooling_layer1.shape[1]) * int(pooling_layer1.shape[2]) * depth2
    flatted_pooling_layer1 = tf.reshape(pooling_layer1, [-1, flatted_pooling_dim])
    layer3_parameters = {'weights': weight_variable([flatted_pooling_dim, neurons]),
                         'biases': bias_variable([neurons])}
    output_layer = tf.nn.bias_add(tf.matmul(flatted_pooling_layer1, layer3_parameters['weights']), layer3_parameters['biases'], name='OutputLayer')
    return input_data, output_layer


def load_picture(file_name, height, width):
    picture_raw = tf.read_file(file_name)
    picture = tf.cast(tf.image.decode_jpeg(picture_raw, channels=3), tf.float32)
    picture.set_shape([height, width, 3])
    return picture.eval()


def get_train_validation_test_sets(pictures_distances):
    assert isinstance(pictures_distances, dict)
    pictures_file_names = list(pictures_distances.keys())
    random.shuffle(pictures_file_names)  # Randomly reorders the file names
    train_size = int(0.7*len(pictures_file_names))
    validation_size = int(0.15*len(pictures_file_names))
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
    pictures_file_names = sorted([os.path.join(directory, x) for x in os.listdir(directory) if x.lower().endswith('.jpg') or x.lower().endswith('.jpeg')])
    with open(os.path.join(directory, DISTANCES_FILE)) as distances_file:
        distances = [float(line) for line in distances_file]
    return dict((pict, dist) for pict, dist in zip(pictures_file_names, distances))


def main():
    directory = '.'
    if len(sys.argv) == 2:
        directory = sys.argv[1]
    print('Constructing model...')
    cnn = convolutional_neural_network(PICTURE_HEIGHT, PICTURE_WIDTH, 3)
    labels = tf.placeholder(tf.float32, shape=[None, 41])
    cross_entropy = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=cnn[1], labels=labels))
    train_step = tf.train.AdamOptimizer().minimize(cross_entropy)
    correct_predictions = tf.equal(tf.argmax(cnn[1], 1), tf.argmax(labels, 1))
    accuracy = tf.reduce_mean(tf.cast(correct_predictions, tf.float32))
    print('Beginning session...')
    with tf.Session() as session:
        with session.as_default():
            tf.global_variables_initializer().run()
            print('Initialisation passed')
            train_set, validation_set, test_set = get_train_validation_test_sets(get_pictures_distances(directory))
            print('Beginning training...')
            for i in range(200):
                if i % 10 == 0:
                    pictures_val, distances_val = random_batch(validation_set, len(validation_set))
                    print("Step {} : Train accuracy = {}".format(i, accuracy.eval(feed_dict={cnn[0]: pictures_val, labels: distances_val})))
                pictures, distances = random_batch(train_set, 25)
                train_step.run(feed_dict={cnn[0]: pictures, labels: distances})
            print('Training finished')
            pictures_test, distances_test = random_batch(test_set, len(test_set))
            print("Test accuracy = {}".format(accuracy.eval(feed_dict={cnn[0]: pictures_test, labels: distances_test})))

if __name__ == '__main__':
    main()
