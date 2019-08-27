import hashlib
import os
import shutil
import time
from uuid import uuid1

from keras.preprocessing.image import ImageDataGenerator
import numpy as np
from lime.lime_image import LimeImageExplainer
from skimage.segmentation import mark_boundaries
from tf_explain.core import GradCAM


basedir = os.path.abspath(os.path.dirname(__file__))
UPLOADED_PATH = os.path.join(basedir, 'static', 'uploads')
AFTER_PATH = os.path.join(basedir, 'static', 'uploads', 'after')
CLASSES = [
    '감수', '결명자', '관목통', '구기자', '나복자',
    '대극', '대황(당고)', '대황(약용)', '대황(종대황)', '도인',
    '목통', '방기', '보골지', '분방기', '상륙',
    '우방자', '육종용', '파극천', '행인'
]


def make_folder(session_id):
    path = os.path.join(UPLOADED_PATH, session_id)
    if not os.path.exists(path):
        os.mkdir(path)
    return path


def save_image(image, path):
    if not os.path.exists(path):
        make_folder(path)
    image.save(path)


# TASK 2.
def load_image(path, session_id):
    dataGen = ImageDataGenerator(rescale=1. / 255)
                                 # samplewise_center=True,
                                 # samplewise_std_normalization=True)
    generator = dataGen.flow_from_directory(path,
                                            target_size=(224, 224),
                                            batch_size=1,
                                            shuffle=False,
                                            class_mode="categorical")

    for directory in generator.filenames:
        image = generator.next()
        filename = directory.split('/')[-1]
        print(filename, session_id)
        if filename.startswith(session_id):
            print('find!')
            break
    return image[0][0]


# TASK 3.
def predict(model, image):
    img = np.expand_dims(image, axis=0)
    pred = model.predict(img)
    return pred[0][int(np.argmax(pred))]


def lime(model, image):
    explainer = LimeImageExplainer()
    explanation = explainer.explain_instance(image, model.predict, hide_color=0, top_labels=5, num_samples=100)
    temp, mask = explanation.get_image_and_mask(explanation.top_labels[0], positive_only=True, num_features=5,
                                                hide_rest=True)
    features = mark_boundaries(image, mask)
    label = explanation.top_labels[0]
    print(label)
    result = CLASSES[label]

    return label, temp, mask, features, result


def grad_cam(model, image, class_index):
    data = ([image], None)

    explainer = GradCAM()
    grid = explainer.explain(data, model.get_layer('mobilenetv2_1.00_224'), 'block_16_expand', class_index)

    return grid