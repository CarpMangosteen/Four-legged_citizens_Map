import os
import json
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

class Polygon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    coordinates = db.Column(db.Text, nullable=False)  # 存储坐标数组的 JSON 字符串
    name = db.Column(db.String(100), nullable=False)  # 多边形名称
    description = db.Column(db.Text, nullable=True)  # 多边形描述

    def to_array(self):
        return json.loads(self.coordinates.encode('utf-8').decode('utf-8'))
    
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

@app.route('/polygons', methods=['POST'])
def add_polygon():
    try:
        # 清除之前存储的所有 Polygon 数据
        db.session.query(Polygon).delete()
        db.session.commit()

        data = request.json
        coordinates = data['coordinates']
        name = data['name']
        description = data.get('description')

        if not isinstance(coordinates, list) or len(coordinates) % 2 != 0:
            raise ValueError("Invalid coordinates format")

        coordinates_json = json.dumps(coordinates)  # 将坐标数组转换为 JSON 字符串

        new_polygon = Polygon(
            coordinates=coordinates_json,
            name=name,
            description=description
        )
        db.session.add(new_polygon)
        db.session.commit()
        return jsonify({'message': 'Polygon added successfully'}), 201
    except KeyError as e:
        app.logger.error(f"Missing key in request data: {e}")
        return jsonify({'error': f"Missing key: {e}"}), 400
    except ValueError as e:
        app.logger.error(f"Invalid data format: {e}")
        return jsonify({'error': f"Invalid data format: {e}"}), 400
    except Exception as e:
        app.logger.error(f"Error adding polygon: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/polygons', methods=['GET'])
def get_polygons():
    try:
        polygons = Polygon.query.all()
        app.logger.info(f"Fetched {len(polygons)} polygons")
        return jsonify([{
            'id': p.id,
            'coordinates': p.to_array(),
            'name': p.name,
            'description': p.description
        } for p in polygons])
    except Exception as e:
        app.logger.error(f"Error fetching polygons: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
