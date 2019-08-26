import base64
import hashlib
import io
import os

import cv2
from flask import Flask, request, session, render_template, redirect
from flask_dropzone import Dropzone
from numpy import unicode
import matplotlib.pyplot as plt

import ml_utils
from admin import admin, HerbView, LocationView, CategoryView, SimilarityGroupView, NewsView, JournalView
from models import db, Herb, Location, Category, SimilarityGroup, News, Journal

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
dropzone = Dropzone()
app.config.update(
    # Admin, SQLAlchemy config:
    SQLALCHEMY_DATABASE_URI='sqlite:///database/herb_medicine.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    FLASK_ADMIN_SWATCH='cosmo',
    SECRET_KEY='my_secret_key',

    # File Upload Path:
    UPLOADED_PATH=os.path.join(basedir, 'static', 'uploads'),

    # Flask-Dropzone config:
    DROPZONE_ALLOWED_FILE_TYPE='image',
    DROPZONE_MAX_FILE_SIZE=10000,
    DROPZONE_MAX_FILES=1,
)
dropzone.init_app(app)
db.init_app(app)
model = None

# admin custom Modelview
table_list = [Herb, Location, Category, SimilarityGroup, News, Journal]
view_list = [HerbView, LocationView, CategoryView, SimilarityGroupView, NewsView, JournalView]
for table, view in zip(table_list, view_list):
    admin.add_view(view(table, db.session))


def _create_identifier():
    base = unicode("%s|%s".format((request.remote_addr,
                                   request.headers.get("User-Agent")), 'utf8', errors='replace'))
    hsh = hashlib.md5()
    hsh.update(base.encode("utf8"))
    return hsh.hexdigest()


# @app.route('/load_model/')
@app.before_first_request
def load_model():
    model_name = './models/maybe_best_model.h5'
    global model
    if model is None:
        model = ml_utils.load_model(model_name)
    return 'Model loaded'


@app.route('/')
def upload():
    session.pop('id')
    session['id'] = _create_identifier()
    return render_template('index.html')


@app.route('/grad_cam/')
def grad_cam():
    global model
    image = ml_utils.get_image(session['id'])
    gradCamGrid = ml_utils.grad_cam(model, image)

    img = io.BytesIO()
    plt.imshow(gradCamGrid)
    plt.savefig(img, format='png')
    img.seek(0)
    img = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return f'data:image/png;base64,{img}'


@app.route('/smooth_grad/')
def smooth_grad():
    global model
    image = ml_utils.get_image(session['id'])
    smoothGradGrid = ml_utils.smooth_grad(model, image)

    img = io.BytesIO()
    plt.imshow(smoothGradGrid)
    plt.savefig(img, format='png')
    img.seek(0)
    img = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return f'data:image/png;base64,{img}'


@app.route('/lime/')
def lime():
    global model
    image = ml_utils.get_image(session['id'])
    _, _, _, features, _ = ml_utils.lime(model, image)

    img = io.BytesIO()
    plt.imshow(features)
    plt.savefig(img, format='png')
    img.seek(0)
    img = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return f'data:image/png;base64,{img}'


@app.route('/result/', methods=["POST"])
def result():
    if request.method == 'POST':
        image = request.files.get('file')
        filename, ext = ''.join(image.filename.split('.')[:-1]), image.filename.split('.')[-1]
        filename = hashlib.md5(filename.encode('utf8')).hexdigest()
        ext = '.' + ext

        directory = os.path.join(ml_utils.PREPARE_PATH, session['id'])
        os.makedirs(directory)

        directory = os.path.join(directory, 'image')
        os.makedirs(directory)

        path = os.path.join(directory, filename + ext)
        image.save(path)

        prepareImage = ml_utils.prepare_image(path)

        beforePath = os.path.join(ml_utils.BEFORE_PATH, session['id'])
        os.makedirs(beforePath)

        beforePath = os.path.join(beforePath, 'image')
        os.makedirs(beforePath)

        beforePath = os.path.join(beforePath, filename + ext)
        cv2.imwrite(beforePath, prepareImage)

        session['image'] = image.read()
        result_id = 2

        herb = Herb.query.filter_by(herb_id=result_id).first()
        category = Category.query.filter_by(category_id=herb.category_id_fk).first()

        group = SimilarityGroup.query.filter_by(group_id=herb.group_id_fk).first()
        group_name = group.group_name
        # 유사약재들 처리
        # 1. 해당 유사약재그룹id를 가진 약재 모두다 조회
        group_herbs = Herb.query.filter_by(group_id_fk=group.group_id).all()
        # 2. 유사약재허브들 객체들에서 이름, 이미지경로 가져오기
        groups = [(_.herb_name, _.image_path) for _ in group_herbs]

        location_list = Location.query.filter_by(herb_id_fk=result_id).all()
        # 좌표들의 평균구하기
        x_avg, y_avg = 0., 0.
        for x, y in [(location.pos_x, location.pos_y) for location in location_list]:
            x_avg += x
            y_avg += y
        n = len(location_list)
        x_avg /= n
        y_avg /= n

        news_list = News.query.filter_by(herb_id_fk=result_id).all()[:3]

        data = {
            'herb': herb,
            'category': category,
            'group_name': group_name,
            'groups': groups,  # 튜플로 유사그룹 name, img_path가 담김
            'location_list': location_list,
            'location_avg': (x_avg, y_avg),  # 백단에서 계산된 x, y좌표들의 평균
            'news_list': news_list,
            'origin_img_path': path
        }
        session.pop('id')
        return render_template('app.html', **data)
    else:
        return redirect('/')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=6000)
