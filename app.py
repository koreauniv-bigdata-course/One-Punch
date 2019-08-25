from flask import Flask, render_template, request, session, redirect, url_for
from flask_dropzone import Dropzone
from models import db, Herb, Location, Category, SimilarityGroup, News, Journal
from admin import admin, HerbView, LocationView, CategoryView, SimilarityGroupView, NewsView, JournalView
import os
import base64, hashlib
import cv2
import tensorflow as tf
import ml_utils


basedir = os.path.abspath(os.path.dirname(__file__))


app = Flask(__name__)
# configuration
app.config.update(
    # File Upload Path:
    UPLOADED_PATH=os.path.join(basedir, 'static', 'uploads'),
    DROPZONE_ALLOWED_FILE_TYPE='image',
    DROPZONE_MAX_FILE_SIZE=10,
    DROPZONE_MAX_FILES=1,

    # admin, sqlalchemy config:
    SQLALCHEMY_DATABASE_URI='sqlite:///database/herb_medicine.db',
    FLASK_ADMIN_SWATCH='cosmo',  # admin 테마 지정
    SECRET_KEY='my_secret_key',  # admin권한을 위한 키생성

    # debug 모드 지정
    DEBUG=True
)

db.init_app(app)
admin.init_app(app)

dropzone = Dropzone()
# initialization
dropzone.init_app(app)

# admin custom Modelview
table_list = [Herb, Location, Category, SimilarityGroup, News, Journal]
view_list = [HerbView, LocationView, CategoryView, SimilarityGroupView, NewsView, JournalView]
for table, view in zip(table_list, view_list):
    admin.add_view(view(table, db.session))

model = None
@app.route('/load_model/')
def load_model():
    model_name = './models/maybe_best_model.h5'
    global model
    if model is None:
        model = tf.keras.models.load_model(model_name)
    return 'Model loaded'


# # models.py -> config에 설정된 db를 생성
# @app.route('/create_all')
# def create_all():
#     db.create_all()
#     return "create OK"
@app.route('/predict/')
def predict():
    image = ml_utils.get_image(app.config['UPLOADED_PATH'])
    # gradCamGrid = ml_utils.grad_cam(model, image)
    # smoothGradGrid = ml_utils.smooth_grad(model, image)
    # preds, temp, mask, features, out = ml_utils.lime(model, image)

    # data = {
    #     'origin_img': session['image'],
    #     'preds': preds,
    #     'temp': temp,
    #     'mask': mask,
    #     'features': features,
    #     # 'gradCam': gradCamGrid,
    #     # 'smoothGradGrid': smoothGradGrid,
    #     'out': out
    # }

    return render_template('predict.html', **data)

@app.route('/result/')
@app.route('/result/<herb_id>')
def result(herb_id=2):
    result_id = 2
    if herb_id:
        result_id=herb_id

    herb = Herb.query.filter_by(herb_id=result_id).first()
    category = Category.query.filter_by(category_id=herb.category_id_fk).first()

    group = SimilarityGroup.query.filter_by(group_id=herb.group_id_fk).first()
    group_name = group.group_name
    # 유사약재들 처리
    # 1. 해당 유사약재그룹id를 가진 약재 모두다 조회
    group_herbs = Herb.query.filter_by(group_id_fk=group.group_id).all()
    # 2. 유사약재허브들 객체들에서 이름, 이미지경로 가져오기
    groups = [ (_.herb_name, _.image_path) for _ in group_herbs]

    location_list = Location.query.filter_by(herb_id_fk=result_id).all()
    # 좌표들의 평균구하기
    x_avg, y_avg = 0., 0.
    for x, y in [ (location.pos_x, location.pos_y) for location in location_list]:
        x_avg += x
        y_avg += y
    n = len(location_list)
    x_avg /= n
    y_avg /= n

    news_list = News.query.filter_by(herb_id_fk=result_id).all()[:3]


    data = {
        'herb': herb,
        'category' : category,
        'group_name' : group_name,
        'groups' : groups, # 튜플로 유사그룹 name, img_path가 담김
        'location_list' : location_list,
        'location_avg' : (x_avg, y_avg), # 백단에서 계산된 x, y좌표들의 평균
        'news_list' : news_list,
        'img_path' : session['image']

    }
    # 'img_path': session['image']
    return render_template('app.html', **data)


@app.route('/')
@app.route('/index/')
def index():
    return render_template('index.html')


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

        session['image'] =image.read()

        return redirect(url_for('result'))
    return render_template('index.html')


if __name__ == '__main__':
    app.run()
