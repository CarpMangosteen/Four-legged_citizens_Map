import os
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from instance.config import get_config

app = Flask(__name__)

# 配置上传文件夹
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 加载配置
config = get_config()
app.config.from_object(config)

db = SQLAlchemy(app)

if app.config['CORS_ENABLED']:
    CORS(app)

# 数据库模型
class Marker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(200), nullable=True)

# 根路径
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/map-config', methods=['GET'])
@app.route('/api/map-config/', methods=['GET'])
def get_map_config():
    return jsonify({
        "key": config.AMAP_API_KEY,
        "securityJsCode": config.AMAP_SECURITY_CODE
    })

@app.route('/markers', methods=['GET'])
def get_markers():
    markers = Marker.query.all()
    return jsonify([{
        'id': m.id,
        'latitude': m.latitude,
        'longitude': m.longitude,
        'title': m.title,
        'description': m.description,
        'image_url': m.image_url
    } for m in markers])

@app.route('/markers', methods=['POST'])
def add_marker():
    data = request.form
    image = request.files.get('image')
    image_url = None

    if image:
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)
        image_url = f'/uploads/{filename}'

    new_marker = Marker(
        latitude=data['latitude'],
        longitude=data['longitude'],
        title=data['title'],
        description=data.get('description'),
        image_url=image_url
    )
    db.session.add(new_marker)
    db.session.commit()
    return jsonify({'message': 'Marker added successfully'}), 201

@app.route('/markers/<int:id>', methods=['DELETE'])
def delete_marker(id):
    marker = Marker.query.get_or_404(id)
    db.session.delete(marker)
    db.session.commit()
    return jsonify({'message': 'Marker deleted successfully'})

@app.route('/markers/<int:id>', methods=['PUT'])
def update_marker(id):
    marker = Marker.query.get_or_404(id)
    data = request.json
    marker.title = data.get('title', marker.title)
    marker.description = data.get('description', marker.description)
    marker.image_url = data.get('image_url', marker.image_url)
    db.session.commit()
    return jsonify({'message': 'Marker updated successfully'})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
