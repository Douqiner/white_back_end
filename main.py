from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import jwt

app = Flask(__name__)
app.secret_key = 'xxxxxx'

# 配置CORS
# CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})
# CORS(app, resources={r"/api/*": {"origins": "*"}})

# 导通mysql并建立映射
host = "localhost",
port = 3306,
user = "root",
password = "Huangjiayi_001",
database = "white_web",
charset = "utf8"
# 配置app参数
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Huangjiayi_001@localhost:3306/white_web?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True  # True跟踪数据库的修改，及时发送信号
db = SQLAlchemy(app)

with app.app_context():
    db.create_all()


class User(db.Model):
    __tablename__ = "user"
    username = db.Column(db.String(20), nullable=False, unique=True, primary_key=True)
    password = db.Column(db.String(200), nullable=False)
    phonenumber = db.Column(db.String(11), nullable=False)
    usertype = db.Column(db.Integer, nullable=False)
    # usertype 区分用户类型 1为一般用户 2为司机


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
    phonenumber = data.get('phonenumber')
    usertype = data.get('usertype')

    # 验证用户
    user = User.query.filter_by(username=username).first()
    if user:
        # 用户已存在
        return jsonify({
            "code": 401,
            "message": "用户已存在"
        })
    # 添加用户
    user = User(username=username, password=generate_password_hash(password), phonenumber=phonenumber,
                usertype=usertype)
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
        return jsonify({"code": 401, "message": "缺少Token"}), 401

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
    payload = {
        "username": username,
        "exp": datetime.datetime.now() + datetime.timedelta(hours=1)  # 1小时有效期
    }
    token = jwt.encode(payload, "secret_key", algorithm="HS256")
    return token


def check_token(token):
    print(token)
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


class Order(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)  # 订单编号
    user1 = db.Column(db.String(20), nullable=True)  # 拼车的四位用户
    user2 = db.Column(db.String(20), nullable=True)
    user3 = db.Column(db.String(20), nullable=True)
    user4 = db.Column(db.String(20), nullable=True)
    departure = db.Column(db.String(100), nullable=False)  # 出发地
    destination = db.Column(db.String(100), nullable=False)  # 目的地
    date = db.Column(db.Date, nullable=False)  # 日期
    earliest_departure_time = db.Column(db.Time, nullable=False)  # 最早发车时间
    latest_departure_time = db.Column(db.Time, nullable=False)  # 最晚发车时间

    def __repr__(self):
        return f'<Order {self.order_id}>'


# 获取所有订单
@app.route('/api/orders', methods=['GET'])
def get_orders():
    orders = Order.query.all()
    data = [
        {
            "order_id": order.order_id,
            "user1": order.user1,
            "user2": order.user2,
            "user3": order.user3,
            "user4": order.user4,
            "departure": order.departure,
            "destination": order.destination,
            "date": order.date.isoformat(),
            "earliest_departure_time": order.earliest_departure_time.isoformat(),
            "latest_departure_time": order.latest_departure_time.isoformat()
        } for order in orders
    ]
    return jsonify({
        "code": 200,
        "message": "查询成功",
        "data": {
            "list": data
        }
    })


# 添加新订单
@app.route('/api/orders/add', methods=['POST'])
def add_order():
    # 获取请求头中的Token
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({
            "code": 401,
            "message": "Token缺失"
        }), 401

    # 检查Token的有效性
    check_result = check_token(token)
    if check_result:
        return check_result  # 如果Token无效，直接返回错误信息

    payload = jwt.decode(token, "secret_key", algorithms=["HS256"])
    current_user = payload['username']  # 解析订单发起人

    data = request.json
    new_order = Order(
        user1=current_user,
        departure=data['departure'],
        destination=data['destination'],
        date=datetime.datetime.strptime(data['date'], '%Y-%m-%d').date(),
        earliest_departure_time=datetime.datetime.strptime(data['earliest_departure_time'], '%H:%M').time(),
        latest_departure_time=datetime.datetime.strptime(data['latest_departure_time'], '%H:%M').time()
    )
    db.session.add(new_order)
    db.session.commit()
    data = {
            "order_id": new_order.order_id,
            "departure": new_order.departure,
            "destination": new_order.destination,
            "date": new_order.date.isoformat(),
            "earliest_departure_time": new_order.earliest_departure_time.isoformat(),
            "latest_departure_time": new_order.latest_departure_time.isoformat()
        }
    return jsonify({
        "code": 201,
        "message": "Order added successfully",
        "username": current_user,
        "data": data
    }), 201


# 获取单个订单
@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify({
        "code": 200,
        "message": "查询成功",
        "data":
            {
                "order_id": order.order_id,
                "user1": order.user1,
                "user2": order.user2,
                "user3": order.user3,
                "user4": order.user4,
                "departure": order.departure,
                "destination": order.destination,
                "date": order.date.isoformat(),
                "earliest_departure_time": order.earliest_departure_time.isoformat(),
                "latest_departure_time": order.latest_departure_time.isoformat()
            }
    })


# 删除订单
@app.route('/api/orders/leave', methods=['POST'])
def delete_order():
    # 获取请求头中的Token
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({
            "code": 401,
            "message": "Token缺失"
        }), 401

    # 检查Token的有效性
    check_result = check_token(token)
    if check_result:
        return check_result  # 如果Token无效，直接返回错误信息

    # 获取请求体中的order_id
    data = request.json
    order_id = data.get('order_id')
    if not order_id:
        return jsonify({
            "code": 400,
            "message": "order_id缺失"
        }), 400

    payload = jwt.decode(token, "secret_key", algorithms=["HS256"])
    current_user = payload['username']

    order = Order.query.get_or_404(order_id)

    users = [order.user1, order.user2, order.user3, order.user4]

    non_empty_users = [user for user in users if user is not None]
    non_empty_count = len(non_empty_users)

    # 移除当前用户
    if current_user in non_empty_users:
        if order.user1 == current_user:
            order.user1 = None
        elif order.user2 == current_user:
            order.user2 = None
        elif order.user3 == current_user:
            order.user3 = None
        elif order.user4 == current_user:
            order.user4 = None

        # 重新排列用户
        users = [order.user1, order.user2, order.user3, order.user4]
        users = [user for user in users if user is not None]
        order.user1, order.user2, order.user3, order.user4 = (
            users[0] if len(users) > 0 else None,
            users[1] if len(users) > 1 else None,
            users[2] if len(users) > 2 else None,
            users[3] if len(users) > 3 else None
        )

        db.session.commit()

        # 检查是否所有用户都离开了
        if len(users) == 0:
            db.session.delete(order)
            db.session.commit()

        return jsonify({
            "code": 200,
            "message": "离开订单成功"
        })
    else:
        return jsonify({
            "code": 404,
            "error": "订单中没有该用户"
        }), 404


if __name__ == '__main__':
    app.run(debug=True, port=8443)