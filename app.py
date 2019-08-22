import os

import cv2
import tensorflow as tf
import keras
import numpy as np
from PIL import Image
from flask import Flask, request, session, render_template
from flask_dropzone import Dropzone
from keras.applications import imagenet_utils
from keras.preprocessing.image import img_to_array
from lime.lime_image import LimeImageExplainer
from skimage.segmentation import mark_boundaries


basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
dropzone = Dropzone()
app.config.update(
    SECRET_KEY='my secret key',

    # File Upload Path:
    UPLOADED_PATH=os.path.join(basedir, r'static\uploads'),

    # Flask-Dropzone config:
    DROPZONE_ALLOWED_FILE_TYPE='image',
    DROPZONE_MAX_FILE_SIZE=10,
    DROPZONE_MAX_FILES=1,
)
dropzone.init_app(app)

model = None

classes = [
    '감수', '결명자', '관목통', '구기자', '나복자',
    '대극', '대황(당고)', '대황(약용)', '대황(종대황)', '도인',
    '목통', '방기', '보골지', '분방기', '상륙',
    '우방자', '육종용', '파극천', '행인'
]


def prepare_image(image, target):
    if image.mode != "RGB":
        image = image.convert("RGB")

    image = image.resize(target)
    image = img_to_array(image)
    image = np.expand_dims(image, axis=0)
    image = imagenet_utils.preprocess_input(image)

    return image


@app.route('/load_model/')
def load_model():
    global model
    global graph
    if model is None:
        model = tf.keras.models.load_model('stdX_test_change_Resnet.h5')
        graph = tf.get_default_graph()
    return 'Model loaded'


@app.route('/', methods=['POST', 'GET'])
def upload():
    if request.method == 'POST':
        image = request.files.get('file')
        image.save(os.path.join(app.config['UPLOADED_PATH'], image.filename))
        session['image'] = '/static/uploads/' + image.filename
        session['image_path'] = app.config['UPLOADED_PATH'] + '\\' + image.filename
        # print(session)
    return render_template('index.html')


@app.route('/result/')
def result():
    global model
    if model is None:
        model = keras.models.load_model('keras_resnet50.h5')

    image = Image.open(session['image_path'])
    image = prepare_image(image, target=(224, 224))

    preds = model.predict(image)

    image = cv2.imread(session['image_path'], cv2.IMREAD_COLOR)
    image = cv2.resize(image, (224, 224))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    explainer = LimeImageExplainer()
    explanation = explainer.explain_instance(image, model.predict, hide_color=0, top_labels=5, num_samples=100)
    temp, mask = explanation.get_image_and_mask(explanation.top_labels[0], positive_only=True, num_features=5,
                                                hide_rest=True)
    features = mark_boundaries(image, mask)

    print(np.argmax(preds), explanation.top_labels[0])

    data = {
        'preds': classes[np.argmax(preds)],
        'temp': temp,
        'mask': mask,
        'features': features,
        'out': classes[explanation.top_labels[0]]
    }

    return render_template('result.html', **data)


if __name__ == "__main__":
    app.run()
