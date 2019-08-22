from flask import Flask, render_template, request, session
from flask_dropzone import Dropzone
from models import db, Herb, Location, Category, SimilarityGroup, News, Journal
from admin import admin, HerbView, LocationView, CategoryView, SimilarityGroupView, NewsView, JournalView
import os, time

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

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

# configuration
app.config.update(
    # File Upload Path:
    UPLOADED_PATH=os.path.join(basedir, r'static\uploads'),

    # Flask-Dropzone config:
    DROPZONE_ALLOWED_FILE_TYPE='image',
    DROPZONE_MAX_FILE_SIZE=1,
    DROPZONE_MAX_FILES=1,
    # admin, sqlalchemy config:
    SQLALCHEMY_DATABASE_URI='sqlite:///herb_medicine.db',
    FLASK_ADMIN_SWATCH='cosmo',  # admin 테마 지정
    SECRET_KEY='my_secret_key',  # admin권한을 위한 키생성

    # debug 모드 지정
    DEBUG=True
)


# models.py -> config에 설정된 db를 생성
@app.route('/create_all')
def create_all():
    db.create_all()
    return "create OK"



@app.route('/')
@app.route('/index/')
def index():
    return render_template('index.html')


@app.route('/', methods=['POST', 'GET'])
def upload():
    if request.method == 'POST':
        image = request.files.get('file')
        print(app.config['UPLOADED_PATH'])
        image.save(os.path.join(app.config['UPLOADED_PATH'], image.filename))
        session['image'] = '/static/uploads/' + image.filename
        time.sleep(0.75)
    return render_template('index.html')


if __name__ == '__main__':
    app.run()
