from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = 'xxxxxxx'

# 配置CORS
# CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})
# CORS(app, resources={r"/api/*": {"origins": "*"}})

#导通mysql并建立映射
host = "localhost",
port = 3306,
user = "root",
password = "123456",
database = "white_web",
charset = "utf8"
# 配置app参数
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/white_web?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True  # True跟踪数据库的修改，及时发送信号
db = SQLAlchemy(app)

with app.app_context():
    db.create_all()

class User(db.Model):
    __tablename__ = "user"
    username = db.Column(db.String(20), nullable=False, unique=True, primary_key=True)
    password = db.Column(db.String(200), nullable=False)

# 用户登录
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # 验证用户
    user = User.query.filter_by(username=username).first()
    if user and (check_password_hash(user.password, password)):
        # 登录成功
        token = generate_token(user.username)  # 生成Token
        print('登录成功')
        return jsonify({
            "code": 200,
            "message": "登录成功",
            "data": {
                "token": token,
                "username": user.username
            }
        })
    else:
        # 登录失败
        print('登录失败')
        return jsonify({
            "code": 401,
            "message": "账号或密码错误"
        })

# 用户注册
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # 验证用户
    user = User.query.filter_by(username=username).first()
    if user:
        # 用户已存在
        return jsonify({
            "code": 401,
            "message": "用户已存在"
        })
    # 添加用户
    user = User(username=username, password=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()
    print('注册成功')
    token = generate_token(user.username)  # 生成Token
    return jsonify({
        "code": 200,
        "message": "注册成功",
        "data": {
            "token": token,
            "username": user.username
        }
    })
    

# 查看表格
@app.route('/api/look', methods=['GET'])
def look():
    # 获取请求头中的Token
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"code": 401, "message": "缺少Token"})
    
    message = check_token(token)
    if message:
        return message

    # 查询所有用户数据
    users = User.query.all()
    table_data = [
        {
            "username": user.username,
            "password": user.password
        } for user in users
    ]
    return jsonify({
        "code": 200,
        "message": "查询成功",
        "data": {
            "table": table_data
        }
    })

# 生成Token
def generate_token(username):
    import jwt
    import datetime
    payload = {
        "username": username,
        "exp": datetime.datetime.now() + datetime.timedelta(hours=1)  # 1小时有效期
    }
    token = jwt.encode(payload, "secret_key", algorithm="HS256")
    return token

def check_token(token):
    print(token)
    import jwt
    # 解码Token
    try:
        payload = jwt.decode(token, "secret_key", algorithms=["HS256"])
        username = payload['username']
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({"code": 401, "message": "用户不存在"})
    except jwt.ExpiredSignatureError:
        return jsonify({"code": 401, "message": "Token已过期"})
    except jwt.InvalidTokenError:
        return jsonify({"code": 401, "message": "无效的Token"})
    return None

if __name__ == '__main__':
    app.run(debug=True, port=8443)