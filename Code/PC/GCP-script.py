#!/usr/bin/env python3

import os
from collections import OrderedDict
from urllib.request import Request, urlopen, URLError
import json
import sys
import traceback

import CNN


def exceptions_handler(exception_class, exception_instance, tb):
    if exception_class == URLError:
        print('Connection error :', exception_instance.reason, file=sys.stderr)
    elif exception_class == json.JSONDecodeError:
        print('Invalid JSON response :', exception_instance.msg, file=sys.stderr)
    else:
        traceback.print_exception(exception_class, exception_instance, tb, file=sys.stderr)


def get_project_id():
    project_id_request = Request('http://metadata.google.internal/computeMetadata/v1/project/project-id')
    project_id_request.add_header('Metadata-Flavor', 'Google')
    try:
        with urlopen(project_id_request) as response:
            value = response.read().decode()
            return value
    except Exception:
        sys.excepthook(*sys.exc_info())
    return ''


def get_attribute(attr_name) -> str:
    attributes_request = Request('http://metadata.google.internal/computeMetadata/v1/instance/attributes/'+attr_name)
    attributes_request.add_header('Metadata-Flavor', 'Google')
    try:
        with urlopen(attributes_request) as response:
            value = response.read().decode()
            return value
    except Exception:
        sys.excepthook(*sys.exc_info())
    return ''


def get_attributes() -> dict:
    attributes_request = Request('http://metadata.google.internal/computeMetadata/v1/instance/attributes/?recursive=true')
    attributes_request.add_header('Metadata-Flavor', 'Google')
    try:
        with urlopen(attributes_request) as response:
            return json.loads(response.read().decode())
    except Exception:
        sys.excepthook(*sys.exc_info())
    return {}


if __name__ == '__main__':
    sys.excepthook = exceptions_handler
    attrs = get_attributes()

    if attrs:
        input_size = int(attrs.get('input_size', 96))
        input_channels = int(attrs.get('input_channels', 3))
        downscale = int(attrs.get('downscale', 1))
        CNN_filename = attrs.get('CNN_filename')
        data_dir = attrs.get('data_dir')
        iterations = int(attrs.get('iterations', 0))
        batch_size = int(attrs.get('batch_size', 100))
        dropouts = eval(attrs.get('dropouts', '[]'))
        learning_rate = float(attrs.get('learning_rate', 0.01))
        expand_data = attrs.get('expand_data', '').lower() == 'true'

        if CNN_filename and data_dir:
            print('Constructing model of', CNN_filename, '...')
            with open(CNN_filename + '.json') as cnn_json_file:
                cnn = CNN.convolutional_neural_network(input_size, input_size, input_channels, json.load(cnn_json_file, object_pairs_hook=OrderedDict))
                classes = int(cnn['output'].get_shape()[1])
            for variable in cnn['variables']:
                print(variable)

            train_dir = os.path.join(data_dir, 'train')
            val_dir = os.path.join(data_dir, 'validation')
            grayscale = input_channels == 1  # The size of the depth dimension is 1

            print('Loading training data...')
            train = CNN.get_pictures_distances(os.path.join(data_dir, 'train'))
            train_batches = CNN.get_batches(train_dir, train, batch_size, grayscale=grayscale, downscale_factor=downscale, classes=classes)
            print('Loading validation data...')
            val = CNN.get_pictures_distances(val_dir)
            val_batch = CNN.get_batches(val_dir, val, len(val), grayscale=grayscale, downscale_factor=downscale, classes=classes)[0]
            print('Data : training = {}, validation = {}'.format(len(train), len(val)))

            CNN.train_conv_net(conv_net=cnn,
                               train_batches=train_batches,
                               validation_batch=val_batch,
                               iterations=iterations,
                               dropouts=dropouts,
                               data_directory=data_dir,
                               model_path=os.path.join(os.path.realpath(CNN_filename), 'CNN'),
                               learning_rate=learning_rate,
                               expand_data=expand_data,
                               )
