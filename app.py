import base64
import hashlib
import os

import cv2
import tensorflow as tf
from flask import Flask, request, session, render_template, redirect, url_for
from flask_dropzone import Dropzone

from models import db, Herb, Location, Category, SimilarityGroup, News, Journal
from admin import admin, HerbView, LocationView, CategoryView, SimilarityGroupView, NewsView, JournalView

import ml_utils

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
dropzone = Dropzone()
app.config.update(
    # Admin, SQLAlchemy config:
    SQLALCHEMY_DATABASE_URI='sqlite:///database/herb_medicine.db',
    FLASK_ADMIN_SWATCH='cosmo',
    SECRET_KEY='my_secret_key',

    # File Upload Path:
    UPLOADED_PATH=os.path.join(basedir, 'static', 'uploads'),

    # Flask-Dropzone config:
    DROPZONE_ALLOWED_FILE_TYPE='image',
    DROPZONE_MAX_FILE_SIZE=10,
    DROPZONE_MAX_FILES=1,
)
dropzone.init_app(app)
model = None


# admin custom Modelview
table_list = [Herb, Location, Category, SimilarityGroup, News, Journal]
view_list = [HerbView, LocationView, CategoryView, SimilarityGroupView, NewsView, JournalView]
for table, view in zip(table_list, view_list):
    admin.add_view(view(table, db.session))


@app.route('/load_model/')
def load_model():
    model_name = './models/maybe_best_model.h5'
    global model
    if model is None:
        model = tf.keras.models.load_model(model_name)
    return 'Model loaded'


@app.route('/', methods=['POST', 'GET'])
def upload():
    if request.method == 'POST':
        image = request.files.get('file')
        filename, ext = ''.join(image.filename.split('.')[:-1]), image.filename.split('.')[-1]
        filename = hashlib.md5(filename.encode('utf8')).hexdigest()
        ext = '.' + ext

        print(filename+ext)
        path = os.path.join(ml_utils.PREPARE_PATH, filename+ext)
        image.save(path)

        prepareImage = ml_utils.prepare_image(path)
        beforePath = os.path.join(ml_utils.BEFORE_PATH, filename+ext)
        cv2.imwrite(beforePath, prepareImage)

        session['image'] = base64.b64encode(image.read())

        return redirect(url_for('result'))
    return render_template('index.html')


@app.route('/result/')
def result():
    image = ml_utils.get_image(app.config['UPLOADED_PATH'])
    gradCamGrid = ml_utils.grad_cam(model, image)
    smoothGradGrid = ml_utils.smooth_grad(model, image)
    preds, temp, mask, features, out = ml_utils.lime(model, image)

    data = {
        'origin_img': session['image'],
        'preds': preds,
        'temp': temp,
        'mask': mask,
        'features': features,
        'gradCam': gradCamGrid,
        'smoothGradGrid': smoothGradGrid,
        'out': out
    }

    return render_template('result.html', **data)


if __name__ == "__main__":
    app.run()
