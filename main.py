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
                "username": user.username,
                "usertype": user.usertype
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
    driver = db.Column(db.String(20), nullable=True)
    departure = db.Column(db.String(100), nullable=False)  # 出发地
    destination = db.Column(db.String(100), nullable=False)  # 目的地
    date = db.Column(db.Date, nullable=False)  # 日期
    earliest_departure_time = db.Column(db.Time, nullable=False)  # 最早发车时间
    latest_departure_time = db.Column(db.Time, nullable=False)  # 最晚发车时间
    remark = db.Column(db.String(100), nullable=False)  # remark

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
            "driver": order.driver,
            "departure": order.departure,
            "destination": order.destination,
            "date": order.date.isoformat(),
            "earliest_departure_time": order.earliest_departure_time.isoformat(),
            "latest_departure_time": order.latest_departure_time.isoformat(),
            "remark": order.remark
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
    user_info = User.query.get_or_404(current_user)

    if user_info.usertype == 2:
        return jsonify({
            "code": 403,
            "message": "您当前身份为司机，不可新建订单"
        }), 403

    data = request.json
    new_order = Order(
        user1=current_user,
        departure=data['departure'],
        destination=data['destination'],
        date=datetime.datetime.strptime(data['date'], '%Y-%m-%d').date(),
        earliest_departure_time=datetime.datetime.strptime(data['earliest_departure_time'], '%H:%M').time(),
        latest_departure_time=datetime.datetime.strptime(data['latest_departure_time'], '%H:%M').time(),
        remark=data['remark']
    )
    db.session.add(new_order)
    db.session.commit()
    data = {
            "order_id": new_order.order_id,
            "departure": new_order.departure,
            "destination": new_order.destination,
            "date": new_order.date.isoformat(),
            "earliest_departure_time": new_order.earliest_departure_time.isoformat(),
            "latest_departure_time": new_order.latest_departure_time.isoformat(),
            "remark": new_order.remark
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
                "driver": order.driver,
                "departure": order.departure,
                "destination": order.destination,
                "date": order.date.isoformat(),
                "earliest_departure_time": order.earliest_departure_time.isoformat(),
                "latest_departure_time": order.latest_departure_time.isoformat(),
                "remark": order.remark
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
    user_info = User.query.get_or_404(current_user)
    if user_info.usertype == 1:
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
                # 先删除与该订单关联的所有评分记录
                DriverRating.query.filter_by(order_id=order.order_id).delete()
                
                # 删除订单状态记录
                OrderStatus.query.filter_by(order_id=order.order_id).delete()
                
                # 然后删除订单本身
                db.session.delete(order)
                db.session.commit()

            return jsonify({
                "code": 200,
                "message": "离开订单成功"
            })
        else:
            return jsonify({
                "code": 404,
                "message": "订单中没有该用户"
            }), 404

    elif user_info.usertype == 2:
        if order.driver == current_user:
            order.driver = None
            db.session.commit()
            return jsonify({
                "code": 200,
                "message": "离开订单成功"
            })
        else:
            return jsonify({
                "code": 404,
                "message": "订单中没有该用户"
            }), 404
    else:
        return jsonify({
            "code": 404,
            "message": "用户类型错误"
        }), 404


@app.route('/api/orders/join', methods=['POST'])
def join_order():
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
    current_user = payload['username']  # 解析加入订单的用户

    data = request.json
    order_id = data.get('order_id')

    if not order_id:
        return jsonify({
            "code": 400,
            "message": "order_id缺失"
        }), 400

    order = Order.query.get_or_404(order_id)
    # 检查订单是否已满员
    user_info = User.query.get_or_404(current_user)
    if user_info.usertype == 1:  # 一般用户
        users = [order.user1, order.user2, order.user3, order.user4]
        non_empty_users = [user for user in users if user is not None]
        if len(non_empty_users) >= 4:
            return jsonify({
                "code": 422,
                "message": "加入失败，订单已满员"
            }), 422
        # 订单没有满员
        if order.user1 is None:
            order.user1 = current_user
        elif order.user2 is None:
            order.user2 = current_user
        elif order.user3 is None:
            order.user3 = current_user
        elif order.user4 is None:
            order.user4 = current_user

        db.session.commit()

        return jsonify({
            "code": 200,
            "message": "加入订单成功"
        }), 200

    elif user_info.usertype == 2:  # 司机
        if order.driver is None:
            order.driver = current_user
            db.session.commit()
            return jsonify({
                "code": 200,
                "message": "加入订单成功"
            }), 200

        else:
            return jsonify({
                "code": 422,
                "message": "加入失败，订单内已有司机"
            }), 422
    else:
        return jsonify({
            "code": 404,
            "message": "用户类型错误"
        }), 404


@app.route('/api/getpos', methods=['GET'])
def get_pos():
    return jsonify({
      "code": 200,
      "message": "获取成功",
      "data": {
        "table": [
          "嘉定校区",
          "虹桥火车站",
          "上海南站",
          "四平路校区"
        ]
      }
    })


@app.route('/api/orders/search/<string:keyword>', methods=['GET'])
def search_orders(keyword):
    search_condition = f"%{keyword}%"
    # 去和字段departure以及destination做匹配
    orders = Order.query.filter(
        (Order.departure.ilike(search_condition)) | (Order.destination.ilike(search_condition))
    ).order_by(Order.date.asc()).all()

    result = [
        {
            "order_id": order.order_id,
            "user1": order.user1,
            "user2": order.user2,
            "user3": order.user3,
            "user4": order.user4,
            "driver": order.driver,
            "departure": order.departure,
            "destination": order.destination,
            "date": order.date.isoformat(),
            "earliest_departure_time": order.earliest_departure_time.isoformat(),
            "latest_departure_time": order.latest_departure_time.isoformat(),
            "remark": order.remark
        } for order in orders
    ]
        
    return jsonify({
        "code": 200,
        "message": "搜索成功",
        "data": {
            "list": result
        }
    })


@app.route('/api/user/<string:username>', methods=['GET'])
def user_info(username):
    user = User.query.get_or_404(username)
    if user.usertype == 1:
        type = '一般用户'
    elif user.usertype == 2:
        type = '司机'
    else:
        type = '类型错误'
    return jsonify({
        "code": 200,
        "message": "查询成功",
        "data":
            {
                "phonenumber": user.phonenumber,
                "usertype": f"{type}"
            }
    })


@app.route('/api/user/orders', methods=['GET'])
def user_orders():
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
    current_user = payload['username']  # 当前用户

    # 查询当前用户参与的所有订单
    orders = Order.query.filter(
        (Order.user1 == current_user) |
        (Order.user2 == current_user) |
        (Order.user3 == current_user) |
        (Order.user4 == current_user)
    ).all()

    result = []
    for order in orders:
        result.append({
            "order_id": order.order_id,
            "user1": order.user1,
            "user2": order.user2,
            "user3": order.user3,
            "user4": order.user4,
            "driver": order.driver,
            "departure": order.departure,
            "destination": order.destination,
            "date": order.date.isoformat(),
            "earliest_departure_time": order.earliest_departure_time.isoformat(),
            "latest_departure_time": order.latest_departure_time.isoformat(),
            "remark": order.remark
        })

    return jsonify({
        "code": 200,
        "message": "查询成功",
        "data": {
            "list": result
        }
    })


class OrderStatus(db.Model):
    __tablename__ = "order_status"
    order_id = db.Column(db.Integer, db.ForeignKey("orders.order_id"), primary_key=True)
    status = db.Column(db.Integer, default=0)  # 0: 未开始, 1: 进行中, 2: 已完成
    user1_arrived = db.Column(db.Boolean, default=False)
    user2_arrived = db.Column(db.Boolean, default=False)
    user3_arrived = db.Column(db.Boolean, default=False)
    user4_arrived = db.Column(db.Boolean, default=False)
    driver_arrived = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)  # 订单完成时间


class DriverRating(db.Model):
    __tablename__ = "driver_rating"
    rating_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.order_id"))
    driver_username = db.Column(db.String(20), db.ForeignKey("user.username"))
    user_username = db.Column(db.String(20), db.ForeignKey("user.username"))
    rating = db.Column(db.Float, nullable=False)  # 1-5分
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)


# 司机平均评分表 - 不修改User表，而是创建新表存储评分信息
class DriverAverageRating(db.Model):
    __tablename__ = "driver_average_rating"
    driver_username = db.Column(db.String(20), db.ForeignKey("user.username"), primary_key=True)
    average_rating = db.Column(db.Float, default=5.0)  # 默认5分
    rating_count = db.Column(db.Integer, default=0)  # 评分次数


# 获取用户最近的订单
@app.route("/api/user/current-order", methods=["GET"])
def get_current_order():
    # 获取请求头中的Token
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"code": 401, "message": "Token缺失"}), 401

    # 检查Token的有效性
    check_result = check_token(token)
    if check_result:
        return check_result  # 如果Token无效，直接返回错误信息

    payload = jwt.decode(token, "secret_key", algorithms=["HS256"])
    current_user = payload["username"]  # 当前用户

    # 获取当前日期和时间
    current_date = datetime.datetime.now().date()
    current_time = datetime.datetime.now()

    # 查询当天用户参与的所有订单
    today_orders = Order.query.filter(((Order.user1 == current_user) | (Order.user2 == current_user) | (Order.user3 == current_user) | (Order.user4 == current_user) | (Order.driver == current_user)) & (Order.date == current_date)).all()

    # 没有当天订单
    if not today_orders:
        return jsonify({"code": 404, "message": "未找到相关订单"})

    # 将订单分为三类：已完成、进行中、未开始
    completed_orders = []  # 已完成订单 (status = 2)
    in_progress_orders = []  # 进行中订单 (status = 1)
    not_started_orders = []  # 未开始订单 (status = 0)

    for order in today_orders:
        order_status = OrderStatus.query.filter_by(order_id=order.order_id).first()

        # 如果没有状态记录，创建一个
        if not order_status:
            order_status = OrderStatus(order_id=order.order_id, status=0, user1_arrived=False, user2_arrived=False, user3_arrived=False, user4_arrived=False, driver_arrived=False)
            db.session.add(order_status)
            db.session.commit()

        if order_status.status == 2:  # 已完成
            completed_orders.append((order, order_status))
        elif order_status.status == 1:  # 进行中
            in_progress_orders.append((order, order_status))
        elif order_status.status == 0:  # 未开始
            not_started_orders.append((order, order_status))

    # 对各类订单按时间排序
    completed_orders.sort(key=lambda x: x[1].completed_at if x[1].completed_at else datetime.datetime.min, reverse=True)
    in_progress_orders.sort(key=lambda x: datetime.datetime.combine(x[0].date, x[0].earliest_departure_time))
    not_started_orders.sort(key=lambda x: datetime.datetime.combine(x[0].date, x[0].earliest_departure_time))

    target_order = None
    target_order_status = None

    # 优先级1：显示进行中订单（取最早的）
    if in_progress_orders:
        target_order, target_order_status = in_progress_orders[0]

    # 优先级2：显示已超过开始时间或开始时间在30分钟内的未开始订单
    elif not_started_orders:
        # 筛选出已超过开始时间的未开始订单
        overdue_orders = []
        future_orders = []

        for order, status in not_started_orders:
            order_start_time = datetime.datetime.combine(order.date, order.earliest_departure_time)
            time_diff = (order_start_time - current_time).total_seconds() / 60  # 转换为分钟

            if order_start_time <= current_time:  # 已超过开始时间
                overdue_orders.append((order, status))
            else:
                future_orders.append((order, status, time_diff))

        # 按时间差排序
        future_orders.sort(key=lambda x: x[2])  # 按时间差升序排序

        if overdue_orders:  # 有已超过开始时间的未开始订单
            target_order, target_order_status = overdue_orders[0]  # 取最早的
        elif future_orders and completed_orders:
            # 判断最近的未开始订单是否在30分钟内
            nearest_future_order, nearest_future_status, time_diff = future_orders[0]

            # 检查用户是否已对最近完成的订单评分
            last_completed_order, last_completed_status = completed_orders[0]
            has_rated = True  # 默认假设已评分

            if last_completed_order.driver:
                # 查询用户是否已经评分
                existing_rating = DriverRating.query.filter_by(order_id=last_completed_order.order_id, user_username=current_user, driver_username=last_completed_order.driver).first()
                has_rated = existing_rating is not None

                # 如果是司机，视为已评分（司机不需要评价自己）
                if current_user == last_completed_order.driver:
                    has_rated = True

            # 如果最近的未开始订单开始时间在30分钟内，显示未开始订单
            # 否则，如果用户未评分，显示已完成订单
            if time_diff <= 30:
                target_order, target_order_status = nearest_future_order, nearest_future_status
            elif not has_rated and current_user != last_completed_order.driver:
                target_order, target_order_status = last_completed_order, last_completed_status
            else:
                # 如果超过30分钟，且已完成订单已评分或用户是司机，显示未开始订单
                target_order, target_order_status = nearest_future_order, nearest_future_status
        elif future_orders:  # 没有已完成订单，显示最近的未开始订单
            target_order, target_order_status = future_orders[0][0], future_orders[0][1]

    # 优先级3：显示已完成订单（未评分的情况）
    elif completed_orders:
        last_completed_order, last_completed_status = completed_orders[0]

        # 检查用户是否已经评分
        has_rated = False
        if last_completed_order.driver:
            # 查询用户是否已经评分
            existing_rating = DriverRating.query.filter_by(order_id=last_completed_order.order_id, user_username=current_user, driver_username=last_completed_order.driver).first()
            has_rated = existing_rating is not None

            # 如果是司机，视为已评分（司机不需要评价自己）
            if current_user == last_completed_order.driver:
                has_rated = True

        # 如果未评分且当前用户不是司机，显示最后完成的订单
        if not has_rated and current_user != last_completed_order.driver:
            target_order = last_completed_order
            target_order_status = last_completed_status
        else:
            # 已评分或用户是司机，返回无订单
            return jsonify({"code": 404, "message": "未找到相关订单"})

    # 所有情况都没有匹配到
    if not target_order:
        return jsonify({"code": 404, "message": "未找到相关订单"})

    # 返回选中的订单
    return jsonify(
        {
            "code": 200,
            "message": "查询成功",
            "data": {
                "order": {
                    "order_id": target_order.order_id,
                    "user1": target_order.user1,
                    "user2": target_order.user2,
                    "user3": target_order.user3,
                    "user4": target_order.user4,
                    "driver": target_order.driver,
                    "departure": target_order.departure,
                    "destination": target_order.destination,
                    "date": target_order.date.isoformat(),
                    "earliest_departure_time": target_order.earliest_departure_time.isoformat(),
                    "latest_departure_time": target_order.latest_departure_time.isoformat(),
                    "remark": target_order.remark,
                },
                "status": {
                    "status": target_order_status.status,
                    "user1_arrived": target_order_status.user1_arrived,
                    "user2_arrived": target_order_status.user2_arrived,
                    "user3_arrived": target_order_status.user3_arrived,
                    "user4_arrived": target_order_status.user4_arrived,
                    "driver_arrived": target_order_status.driver_arrived,
                },
            },
        }
    )


# 用户/司机确认到达
@app.route("/api/order/confirm-arrival", methods=["POST"])
def confirm_arrival():
    # 获取请求头中的Token
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"code": 401, "message": "Token缺失"}), 401

    # 检查Token的有效性
    check_result = check_token(token)
    if check_result:
        return check_result  # 如果Token无效，直接返回错误信息

    payload = jwt.decode(token, "secret_key", algorithms=["HS256"])
    current_user = payload["username"]  # 当前用户

    data = request.json
    order_id = data.get("order_id")

    if not order_id:
        return jsonify({"code": 400, "message": "order_id缺失"}), 400

    # 获取订单和订单状态
    order = Order.query.get_or_404(order_id)
    order_status = OrderStatus.query.filter_by(order_id=order_id).first()

    if not order_status:
        return jsonify({"code": 404, "message": "订单状态不存在"}), 404

    # 标记用户到达状态
    is_driver = False
    if current_user == order.driver:
        order_status.driver_arrived = True
        is_driver = True
    elif order.user1 == current_user:
        order_status.user1_arrived = True
    elif order.user2 == current_user:
        order_status.user2_arrived = True
    elif order.user3 == current_user:
        order_status.user3_arrived = True
    elif order.user4 == current_user:
        order_status.user4_arrived = True
    else:
        return jsonify({"code": 403, "message": "您不是该订单的参与者"}), 403

    # 检查是否所有乘客都已到达（不包括司机）
    all_passengers_arrived = True
    if order.user1 and order.user1 != order.driver and not order_status.user1_arrived:
        all_passengers_arrived = False
    if order.user2 and order.user2 != order.driver and not order_status.user2_arrived:
        all_passengers_arrived = False
    if order.user3 and order.user3 != order.driver and not order_status.user3_arrived:
        all_passengers_arrived = False
    if order.user4 and order.user4 != order.driver and not order_status.user4_arrived:
        all_passengers_arrived = False

    # 订单状态保持为0（未开始），直到司机主动点击"开始行程"

    db.session.commit()

    return jsonify(
        {
            "code": 200,
            "message": "确认到达成功",
            "data": {
                "status": order_status.status,
                "user1_arrived": order_status.user1_arrived,
                "user2_arrived": order_status.user2_arrived,
                "user3_arrived": order_status.user3_arrived,
                "user4_arrived": order_status.user4_arrived,
                "driver_arrived": order_status.driver_arrived,
                "all_passengers_arrived": all_passengers_arrived,
            },
        }
    )


# 司机开始行程接口
@app.route("/api/order/start-trip", methods=["POST"])
def start_trip():
    # 获取请求头中的Token
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"code": 401, "message": "Token缺失"}), 401

    # 检查Token的有效性
    check_result = check_token(token)
    if check_result:
        return check_result  # 如果Token无效，直接返回错误信息

    payload = jwt.decode(token, "secret_key", algorithms=["HS256"])
    current_user = payload["username"]  # 当前用户

    data = request.json
    order_id = data.get("order_id")

    if not order_id:
        return jsonify({"code": 400, "message": "order_id缺失"}), 400

    # 获取订单和订单状态
    order = Order.query.get_or_404(order_id)
    order_status = OrderStatus.query.filter_by(order_id=order_id).first()

    if not order_status:
        return jsonify({"code": 404, "message": "订单状态不存在"}), 404

    # 检查是否是司机
    if current_user != order.driver:
        return jsonify({"code": 403, "message": "只有司机可以开始行程"}), 403

    # 检查司机是否已到达
    if not order_status.driver_arrived:
        return jsonify({"code": 400, "message": "司机尚未确认到达"}), 400

    # 检查所有乘客是否已到达
    all_passengers_arrived = True
    if order.user1 and order.user1 != order.driver and not order_status.user1_arrived:
        all_passengers_arrived = False
    if order.user2 and order.user2 != order.driver and not order_status.user2_arrived:
        all_passengers_arrived = False
    if order.user3 and order.user3 != order.driver and not order_status.user3_arrived:
        all_passengers_arrived = False
    if order.user4 and order.user4 != order.driver and not order_status.user4_arrived:
        all_passengers_arrived = False

    if not all_passengers_arrived:
        return jsonify({"code": 400, "message": "等待所有乘客确认到达"}), 400

    # 更新订单状态为进行中
    order_status.status = 1  # 进行中

    db.session.commit()

    return jsonify({"code": 200, "message": "行程开始成功", "data": {"status": order_status.status}})


# 确认到达目的地
@app.route("/api/order/confirm-destination", methods=["POST"])
def confirm_destination():
    # 获取请求头中的Token
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"code": 401, "message": "Token缺失"}), 401

    # 检查Token的有效性
    check_result = check_token(token)
    if check_result:
        return check_result  # 如果Token无效，直接返回错误信息

    payload = jwt.decode(token, "secret_key", algorithms=["HS256"])
    current_user = payload["username"]  # 当前用户

    data = request.json
    order_id = data.get("order_id")

    if not order_id:
        return jsonify({"code": 400, "message": "order_id缺失"}), 400

    # 获取订单和订单状态
    order = Order.query.get_or_404(order_id)

    # 检查是否是司机
    user = User.query.filter_by(username=current_user).first()
    is_driver = user and current_user == order.driver

    if is_driver:
        # 司机确认处理
        order_status = OrderStatus.query.filter_by(order_id=order_id).first()
        if not order_status:
            return jsonify({"code": 404, "message": "订单状态不存在"}), 404

        # 只有在进行中状态才能确认到达目的地
        if order_status.status == 1:
            # 设置为"已完成"
            order_status.status = 2  # 已完成
            # 设置完成时间为当前时间
            order_status.completed_at = datetime.datetime.now()
            message = "确认到达目的地成功"
        else:
            message = "状态更新失败，订单状态异常"

        db.session.commit()

        return jsonify({"code": 200, "message": message, "data": {"status": order_status.status, "completed_at": order_status.completed_at.isoformat() if order_status.completed_at else None}})

    return jsonify({"code": 200, "message": "用户确认到达目的地"})


# 提交司机评分
@app.route("/api/order/rate-driver", methods=["POST"])
def rate_driver():
    # 获取请求头中的Token
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"code": 401, "message": "Token缺失"}), 401

    # 检查Token的有效性
    check_result = check_token(token)
    if check_result:
        return check_result  # 如果Token无效，直接返回错误信息

    payload = jwt.decode(token, "secret_key", algorithms=["HS256"])
    current_user = payload["username"]  # 当前用户

    data = request.json
    order_id = data.get("order_id")
    rating = data.get("rating")

    if not order_id or not rating:
        return jsonify({"code": 400, "message": "订单ID或评分缺失"}), 400

    # 验证评分范围
    try:
        rating_value = float(rating)
        if rating_value < 1 or rating_value > 5:
            return jsonify({"code": 400, "message": "评分必须在1-5之间"}), 400
    except ValueError:
        return jsonify({"code": 400, "message": "评分必须是数字"}), 400

    # 获取订单信息
    order = Order.query.get_or_404(order_id)

    # 确保用户是该订单的参与者
    if current_user != order.user1 and current_user != order.user2 and current_user != order.user3 and current_user != order.user4:
        return jsonify({"code": 403, "message": "您不是该订单的参与者"}), 403

    # 找到司机
    driver_user = User.query.filter_by(username=order.driver).first()
    if not driver_user:
        return jsonify({"code": 404, "message": "找不到该订单的司机"}), 404

    # 检查用户是否已经评价过
    existing_rating = DriverRating.query.filter_by(order_id=order_id, user_username=current_user, driver_username=driver_user.username).first()

    # 获取或创建司机平均评分记录
    driver_avg_rating = DriverAverageRating.query.filter_by(driver_username=driver_user.username).first()

    if not driver_avg_rating:
        driver_avg_rating = DriverAverageRating(driver_username=driver_user.username, average_rating=5.0, rating_count=0)
        db.session.add(driver_avg_rating)

    if existing_rating:
        # 如果已有评分，需要更新平均分
        old_rating = existing_rating.rating
        # 更新现有评分记录
        existing_rating.rating = rating_value
        existing_rating.created_at = datetime.datetime.now()

        # 更新平均评分: 从总和中减去旧评分再加上新评分
        if driver_avg_rating.rating_count > 0:
            total_rating = driver_avg_rating.average_rating * driver_avg_rating.rating_count
            total_rating = total_rating - old_rating + rating_value
            driver_avg_rating.average_rating = total_rating / driver_avg_rating.rating_count
    else:
        # 创建新评分
        new_rating = DriverRating(order_id=order_id, driver_username=driver_user.username, user_username=current_user, rating=rating_value)
        db.session.add(new_rating)

        # 更新平均评分: 计算新的平均值
        if driver_avg_rating.rating_count == 0:
            driver_avg_rating.average_rating = rating_value
        else:
            total_rating = driver_avg_rating.average_rating * driver_avg_rating.rating_count
            driver_avg_rating.average_rating = (total_rating + rating_value) / (driver_avg_rating.rating_count + 1)

        # 增加评分次数
        driver_avg_rating.rating_count += 1

    db.session.commit()

    return jsonify({"code": 200, "message": "评分提交成功", "data": {"driver_rating": driver_avg_rating.average_rating}})


# 获取司机评分
@app.route("/api/user/driver-rating/<string:username>", methods=["GET"])
def get_driver_rating(username):
    # 验证该用户是司机
    driver = User.query.filter_by(username=username, usertype=2).first()
    if not driver:
        return jsonify({"code": 404, "message": "找不到该司机"}), 404

    # 获取司机平均评分
    driver_avg_rating = DriverAverageRating.query.filter_by(driver_username=username).first()

    if not driver_avg_rating:
        # 如果没有评分记录，返回默认值
        return jsonify({"code": 200, "message": "查询成功", "data": {"username": username, "rating": 5.0, "rating_count": 0}})

    return jsonify({"code": 200, "message": "查询成功", "data": {"username": username, "rating": driver_avg_rating.average_rating, "rating_count": driver_avg_rating.rating_count}})


# 检查用户是否已对订单司机评分
@app.route("/api/order/check-user-rating", methods=["POST"])
def check_user_rating():
    # 获取请求头中的Token
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"code": 401, "message": "Token缺失"}), 401

    # 检查Token的有效性
    check_result = check_token(token)
    if check_result:
        return check_result  # 如果Token无效，直接返回错误信息

    payload = jwt.decode(token, "secret_key", algorithms=["HS256"])
    current_user = payload["username"]  # 当前用户

    data = request.json
    order_id = data.get("order_id")
    driver_username = data.get("driver_username")

    if not order_id or not driver_username:
        return jsonify({"code": 400, "message": "订单ID或司机用户名缺失"}), 400

    # 查询是否已经评分
    existing_rating = DriverRating.query.filter_by(order_id=order_id, user_username=current_user, driver_username=driver_username).first()

    return jsonify({"code": 200, "message": "查询成功", "data": {"has_rated": existing_rating is not None}})


@app.route("/api/user/completed-orders", methods=["GET"])
def get_completed_orders():
    # 获取请求头中的Token
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"code": 401, "message": "Token缺失"}), 401

    # 检查Token的有效性
    check_result = check_token(token)
    if check_result:
        return check_result  # 如果Token无效，直接返回错误信息

    payload = jwt.decode(token, "secret_key", algorithms=["HS256"])
    current_user = payload["username"]  # 当前用户

    # 查询用户参与且已完成的订单
    completed_orders = (
        Order.query.join(OrderStatus, Order.order_id == OrderStatus.order_id)
        .filter(((Order.user1 == current_user) | (Order.user2 == current_user) | (Order.user3 == current_user) | (Order.user4 == current_user) | (Order.driver == current_user)) & (OrderStatus.status == 2))  # 已完成状态
        .order_by(OrderStatus.completed_at.desc())
        .all()
    )

    result = []
    for order in completed_orders:
        order_status = OrderStatus.query.filter_by(order_id=order.order_id).first()
        result.append(
            {
                "order_id": order.order_id,
                "user1": order.user1,
                "user2": order.user2,
                "user3": order.user3,
                "user4": order.user4,
                "driver": order.driver,
                "departure": order.departure,
                "destination": order.destination,
                "date": order.date.isoformat(),
                "earliest_departure_time": order.earliest_departure_time.isoformat(),
                "latest_departure_time": order.latest_departure_time.isoformat(),
                "remark": order.remark,
                "completed_at": order_status.completed_at.isoformat() if order_status.completed_at else None,
            }
        )

    return jsonify({"code": 200, "message": "查询成功", "data": {"list": result}})


# 获取所有未开始的订单
@app.route("/api/orders/not-started", methods=["GET"])
def get_not_started_orders():
    # 先获取所有订单
    orders = Order.query.all()
    result = []

    for order in orders:
        # 获取订单状态
        order_status = OrderStatus.query.filter_by(order_id=order.order_id).first()

        # 如果没有状态记录，创建一个（默认为未开始）
        if not order_status:
            order_status = OrderStatus(order_id=order.order_id, status=0, user1_arrived=False, user2_arrived=False, user3_arrived=False, user4_arrived=False, driver_arrived=False)  # 0表示未开始
            db.session.add(order_status)
            db.session.commit()

        # 只添加未开始的订单
        if order_status.status == 0:
            result.append(
                {
                    "order_id": order.order_id,
                    "user1": order.user1,
                    "user2": order.user2,
                    "user3": order.user3,
                    "user4": order.user4,
                    "driver": order.driver,
                    "departure": order.departure,
                    "destination": order.destination,
                    "date": order.date.isoformat(),
                    "earliest_departure_time": order.earliest_departure_time.isoformat(),
                    "latest_departure_time": order.latest_departure_time.isoformat(),
                    "remark": order.remark,
                }
            )

    return jsonify({"code": 200, "message": "查询成功", "data": {"list": result}})


if __name__ == '__main__':
    app.run(debug=True, port=8443)