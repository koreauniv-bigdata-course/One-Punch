from flask import Flask, render_template, request, session
from flask_dropzone import Dropzone

import os, time

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
dropzone = Dropzone()

# initialization
dropzone.init_app(app)

# configuration
app.config.update(
    # File Upload Path:
    UPLOADED_PATH=os.path.join(basedir, r'static\uploads'),

    # Flask-Dropzone config:
    DROPZONE_ALLOWED_FILE_TYPE='image',
    DROPZONE_MAX_FILE_SIZE=1,
    DROPZONE_MAX_FILES=1,
)


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
