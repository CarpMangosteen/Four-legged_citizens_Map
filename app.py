from flask import Flask, render_template, jsonify, request
import os
from dotenv import load_dotenv
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

@app.route("/get_keys", methods=["GET"])
def get_keys():
    return jsonify({
        "AMap_API_KEY": app.config["AMap_API_KEY"],
        "AMap_SECURITY_KEY": app.config["AMap_SECURITY_KEY"]
    })

# 模拟数据库：标记信息
markers = [
    {"id": 1, "position": [116.397428, 39.90923], "image": "//a.amap.com/jsapi_demos/static/demo-center/icons/dir-via-marker.png"},
]

# 首页路由
@app.route("/")
def index():
    return render_template("index.html")

# 获取标记数据的 API
@app.route("/get_markers", methods=["GET"])
def get_markers():
    return jsonify({"markers": markers})

# 添加新标记的 API
@app.route("/add_marker", methods=["POST"])
def add_marker():
    data = request.json
    new_marker = {
        "id": len(markers) + 1,
        "position": data["position"],
        "image": data["image"],
    }
    markers.append(new_marker)
    return jsonify({"success": True, "marker": new_marker})

# 删除标记的 API
@app.route("/delete_marker/<int:marker_id>", methods=["DELETE"])
def delete_marker(marker_id):
    global markers
    markers = [m for m in markers if m["id"] != marker_id]
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(debug=True)
