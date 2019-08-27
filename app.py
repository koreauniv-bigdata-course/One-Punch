import base64
import io

import matplotlib.pyplot as plt
from flask import Flask, request, session, render_template
from flask_dropzone import Dropzone

import ml_utils
from admin import admin, HerbView, LocationView, CategoryView, SimilarityGroupView, NewsView, JournalView
from models import db, Herb, Location, Category, SimilarityGroup, News, Journal
from tasks import *

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
    DROPZONE_MAX_FILE_SIZE=1024,
    DROPZONE_MAX_FILES=1,
    DROPZONE_REDIRECT_VIEW='result',
    DROPZONE_PARALLEL_UPLOADS=1,
    DROPZONE_TIMEOUT=5 * 60 * 1000
)
dropzone.init_app(app)
db.init_app(app)
model = None

# admin custom Modelview
table_list = [Herb, Location, Category, SimilarityGroup, News, Journal]
view_list = [HerbView, LocationView, CategoryView, SimilarityGroupView, NewsView, JournalView]
for table, view in zip(table_list, view_list):
    admin.add_view(view(table, db.session))


@app.before_first_request
def load_model():
    model_name = './models/maybe_best_model.h5'
    global model
    if model is None:
        model = ml_utils.load_model(model_name)
    return 'Model loaded'


@app.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if session.get('id') is None:
            id = str(uuid1())
            session['id'] = id

        image = request.files.get('file')
        filename = session['id'] + '.' + image.filename.split('.')[-1]

        image.save(os.path.join(UPLOADED_PATH, 'img', filename))
    return render_template('index.html')


def herb_info(herb_id):
    herb = Herb.query.filter_by(herb_id=herb_id).first()
    category = Category.query.filter_by(category_id=herb.category_id_fk).first()

    group = SimilarityGroup.query.filter_by(group_id=herb.group_id_fk).first()
    group_name = group.group_name
    group_herbs = Herb.query.filter_by(group_id_fk=group.group_id).all()
    groups = [(_.herb_name, _.image_path) for _ in group_herbs]

    location_list = Location.query.filter_by(herb_id_fk=herb_id).all()
    x_avg, y_avg = 0., 0.
    for x, y in [(location.pos_x, location.pos_y) for location in location_list]:
        x_avg += x
        y_avg += y
    n = len(location_list)
    x_avg /= n
    y_avg /= n

    news_list = News.query.filter_by(herb_id_fk=herb_id).all()[:3]
    data = {
        'herb': herb,
        'category': category,
        'group_name': group_name,
        'groups': groups,
        'location_list': location_list,
        'location_avg': (x_avg, y_avg),
        'news_list': news_list
    }
    return data


@app.route('/result/')
def result():
    if session.get('id') is None:
        return render_template('attach.html')

    image = load_image(UPLOADED_PATH, session['id'])

    original_img = io.BytesIO()
    plt.imshow(image)
    plt.savefig(original_img, format='png')
    original_img.seek(0)
    original_img = base64.b64encode(original_img.getvalue()).decode()
    plt.close()

    # Prediction
    img = np.expand_dims(image, axis=0)
    pred = model.predict(img)

    # Lime
    label, _, _, features, res = lime(model, image)
    feature_image = io.BytesIO()
    plt.imshow(features)
    plt.savefig(feature_image, format='png')
    feature_image.seek(0)
    feature_image = base64.b64encode(feature_image.getvalue()).decode()
    plt.close()
    class_index = int(label)

    # Grad Cam
    grid = grad_cam(model, image, 1)
    grad_image = io.BytesIO()
    plt.imshow(grid)
    plt.savefig(grad_image, format='png')
    grad_image.seek(0)
    grad_image = base64.b64encode(grad_image.getvalue()).decode()
    plt.close()

    herb = herb_info(class_index+1)
    data = {
        'pred': round(pred[0][class_index] * 100, 2),
        'original_img': f'data:image/png;base64,{original_img}',
        'features': f'data:image/png;base64,{feature_image}',
        'grad': f'data:image/png;base64,{grad_image}',
    }

    session.clear()
    return render_template('app.html', **data, **herb)


@app.errorhandler(404)
def error_page(error):
    return render_template('404.html')


@app.errorhandler(504)
def error_page(error):
    return render_template('404.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=6000)
