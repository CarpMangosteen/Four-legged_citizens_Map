from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import instance.config as config

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///markers.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 数据库模型
class Marker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(200), nullable=True)

# 根路径，返回地图前端页面
@app.route('/')
def home():
    return render_template('index.html')  # 渲染位于 templates/index.html 的前端文件

@app.route('/api/map-config', methods=['GET'])
def get_map_config():
    return jsonify({
        "key": config.AMap_API_KEY,  # 从配置文件读取 API Key
        "securityJsCode": config.AMap_SECURITY_CODE  # 从配置文件读取安全代码
    })

# 获取所有点标记
@app.route('/markers', methods=['GET'])
def get_markers():
    markers = Marker.query.all()  # 从数据库获取所有点标记
    return jsonify([{
        'id': m.id,
        'latitude': m.latitude,
        'longitude': m.longitude,
        'title': m.title,
        'description': m.description,
        'image_url': m.image_url
    } for m in markers])

# 添加点标记
@app.route('/markers', methods=['POST'])
def add_marker():
    data = request.json
    new_marker = Marker(
        latitude=data['latitude'],
        longitude=data['longitude'],
        title=data['title'],
        description=data.get('description'),
        image_url=data.get('image_url')
    )
    db.session.add(new_marker)
    db.session.commit()
    return jsonify({'message': 'Marker added successfully'}), 201

# 删除点标记
@app.route('/markers/<int:id>', methods=['DELETE'])
def delete_marker(id):
    marker = Marker.query.get_or_404(id)
    db.session.delete(marker)
    db.session.commit()
    return jsonify({'message': 'Marker deleted successfully'})

# 更新点标记
@app.route('/markers/<int:id>', methods=['PUT'])
def update_marker(id):
    marker = Marker.query.get_or_404(id)
    data = request.json
    marker.title = data.get('title', marker.title)
    marker.description = data.get('description', marker.description)
    marker.image_url = data.get('image_url', marker.image_url)
    db.session.commit()
    return jsonify({'message': 'Marker updated successfully'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
