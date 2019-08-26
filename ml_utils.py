import os, shutil

import tensorflow as tf
import keras
import numpy as np
import cv2
from keras.applications import imagenet_utils
from keras.preprocessing.image import img_to_array
from lime.lime_image import LimeImageExplainer
from skimage.segmentation import mark_boundaries
from tf_explain.core import GradCAM
from tf_explain.core.smoothgrad import SmoothGrad

_classes = [
    '감수', '결명자', '관목통', '구기자', '나복자',
    '대극', '대황(당고)', '대황(약용)', '대황(종대황)', '도인',
    '목통', '방기', '보골지', '분방기', '상륙',
    '우방자', '육종용', '파극천', '행인'
]

basedir = os.path.abspath(os.path.dirname(__file__))
PREPARE_PATH = os.path.join(basedir, 'static', 'uploads', 'pre')
BEFORE_PATH = os.path.join(basedir, 'static','uploads', 'before')
AFTER_PATH = os.path.join(basedir, 'static','uploads', 'after')
GRAPH_PAPER_PATH = os.path.join(basedir, 'static', 'uploads', 'gp', 'monun.jpg')


def load_model(model_name):
    device = tf.test.gpu_device_name()
    with tf.device(device):
        model = tf.keras.models.load_model(model_name)
    # model = tf.keras.models.load_model(model_name)
    return model


def object_detection(image):
    img = image.copy()
    mask = np.zeros(img.shape[:2], np.uint8)

    bgdModel = np.zeros((1, 65), np.float64)
    fgdModel = np.zeros((1, 65), np.float64)

    start = img.shape[0] // 4
    end = img.shape[1] // 2

    rect = (start, start, end, end)
    cv2.grabCut(img, mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)

    mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
    img = img * mask2[:, :, np.newaxis]

    return img


def image_at_graph_paper(image, graph_paper):
    img = image.copy()
    for rgb in range(graph_paper.shape[2]):
        for y in range(graph_paper.shape[1]):
            for x in range(graph_paper.shape[0]):
                if img[x][y][rgb] == 0:
                    img[x][y][rgb] = graph_paper[x][y][rgb]
    return img


def prepare_image_for_predict(image, target=(224, 224)):
    if image.mode != "RGB":
        image = image.convert("RGB")

    image = image.resize(target)
    image = img_to_array(image)
    image = np.expand_dims(image, axis=0)
    image = imagenet_utils.preprocess_input(image)

    return image


def prepare_image(image_path):
    graphPaper = cv2.imread(GRAPH_PAPER_PATH)
    graphPaper = cv2.cvtColor(graphPaper, cv2.COLOR_BGR2RGB)

    # img = np.fromstring(image, np.uint8)
    # img = cv2.imdecode(img, cv2.CV_LOAD_IMAGE_UNCHANGED)
    img = cv2.imread(image_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, dsize=(224, 224))

    img = object_detection(img)
    img = image_at_graph_paper(img, graphPaper)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    return img


def get_image(path):
    dataGen = keras.preprocessing.image.ImageDataGenerator(rescale=1. / 255,
                                                           samplewise_center=True,
                                                           samplewise_std_normalization=True)
    generator = dataGen.flow_from_directory(os.path.join(PREPARE_PATH, path),
                                            target_size=(224, 224),
                                            batch_size=5,
                                            shuffle=False,
                                            class_mode="categorical")
    print(generator.filepaths)
    print(generator.filenames)
    imgPath = generator.filepaths[0]
    imgName = generator.filenames[0].split('/')[1]
    image = generator.next()[0][0]

    # movePath = os.path.join(AFTER_PATH, imgName)
    # shutil.copy(imgPath, movePath)
    # shutil.move(imgPath, movePath)
    # os.remove(path)

    return image


def grad_cam(model, image):
    # img = tf.keras.preprocessing.image.load_img(imgPath, target_size=(224, 224))
    # img = tf.keras.preprocessing.image.img_to_array(img)
    data = ([image], None)

    explainer = GradCAM()
    grid = explainer.explain(data, model.get_layer('resnet50'), 'res2a_branch2a', 1)
    # explainer.save(grid, '/drive/My Drive/workspace', 'grad_cam.png')

    return grid


def smooth_grad(model, image, class_index):
    data = ([image], None)

    explainer = SmoothGrad()
    grid = explainer.explain(data, model, class_index)

    return grid


def lime(model, image):
    # image = cv2.imread(img_path, cv2.IMREAD_COLOR)
    # image = cv2.resize(image, (224, 224))
    # image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    explainer = LimeImageExplainer()
    explanation = explainer.explain_instance(image, model.predict, hide_color=0, top_labels=5, num_samples=100)
    temp, mask = explanation.get_image_and_mask(explanation.top_labels[0], positive_only=True, num_features=5,
                                                hide_rest=True)
    features = mark_boundaries(image, mask)
    preds = explanation.top_labels[0]
    result = _classes[preds]

    return preds, temp, mask, features, result
