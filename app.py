from datetime import datetime
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import time
import threading
from flask import Flask, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy

from volcenginesdkarkruntime import Ark

client = Ark(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key="a1e9238a-9d4f-4ad4-97c8-889534ed1f15"
)


app = Flask(__name__)


HOSTNAME = '127.0.0.1'
PORT = 3307
USERNAME = 'root'
PASSWORD = 'Pass001!'
DATABASE = 'my_test'
app.config[
    'SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}?charset=utf8mb4'

# SQLAlchemy 是一个用于 Python 的 SQL 工具包和对象关系映射（ORM）库，
# 它可以帮助开发者更方便地与数据库进行交互。
db = SQLAlchemy(app)


# 创建一个应用上下文（application context）。
# 在 Flask 中，应用上下文用于存储与当前应用相关的信息，比如配置、数据库连接等。
# with app.app_context():
#     with db.engine.connect() as conn:
#         rs = conn.execute(text("SELECT version()"))
#         print(rs.fetchone())

class User(db.Model):
    # select id, name, age, sex, birthday,
    # address, phone, email, create_time, update_time from t_test_user;
    __tablename__ = 't_test_user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    birthday = db.Column(db.DateTime, nullable=False)


# with app.app_context():
#     user = User(name='马冬梅', age=20, birthday=datetime.today())
#     db.session.commit()
#     db.session.add(user)
#

# 使用 route() 装饰器将函数绑定到 URL
@app.route('/user/add', methods=['POST'])
def add_user():  # put application's code here
    user = User(name='马冬梅', age=20, birthday=datetime.today())
    db.session.add(user)
    db.session.commit()
    return "用户创建成功"

# 使用 route() 装饰器将函数绑定到 URL
@app.route('/user/get', methods=['GET'])
def get_user():
    # users = User.query.all()
    user = User.query.get(1)
    print(user)
    users = User.query.filter_by(id=user.id)
    for u in users:
        print(u)
    return "查找成功"



@app.route('/stream')
def stream():
    """
    流式输出 API
    """
    print('start')
    def generate_stream():
        stream = client.chat.completions.create(
            model="ep-20250120130849-sd562",
            messages=[
                {"role": "system", "content": "你是豆包，是由字节跳动开发的 AI 人工智能助手"},
                {"role": "user", "content": "常见的十字花科植物有哪些？"},
            ],
            extra_headers={'x-is-encrypted': 'true'},
            stream=True
        )
        for chunk in stream:
            if not chunk.choices:
                continue
            yield chunk.choices[0].delta.content  # 逐段输出
            yield ""  # 分隔符，防止浏览器缓存
    return Response(generate_stream(), content_type='text/plain; charset=utf-8')

@app.route('/chat')
def chat():
    return render_template('chat.html')


@app.route('/chat2')
def chat2():
    return render_template('chat2.html')


@app.route('/chat-stream', methods=['POST'])
def chat_stream():
    user_content = request.json.get('message', '')

    def generate():
        stream = client.chat.completions.create(
            model="ep-20250120130849-sd562",
            messages=[
                {"role": "system", "content": "你是豆包，是由字节跳动开发的 AI 人工智能助手"},
                {"role": "user", "content": user_content},
            ],
            stream=True
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                # 直接返回纯文本内容，不添加任何前缀
                yield chunk.choices[0].delta.content

    return Response(
        stream_with_context(generate()),
        mimetype='text/plain',
        headers={
            'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'
        }
    )

@app.route('/chat-stream2', methods=['GET'])  # 改为只接受GET请求
def chat_stream2():
    # 通过URL参数获取用户问题
    user_content = request.args.get('message', '')

    def generate():
        stream = client.chat.completions.create(
            model="ep-20250120130849-sd562",
            messages=[
                {"role": "system", "content": "你是豆包，是由字节跳动开发的 AI 人工智能助手"},
                {"role": "user", "content": user_content},
            ],
            stream=True
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                yield f"data: {content}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'
        }
    )

# 运行应用程序: flask --app 文件名(不含.py后缀) run; 如果文件名为 app.py 或 wsgi.py, 可以简写为: flask run
# 告诉您的操作系统侦听所有公有 IP: flask run --host=0.0.0.0
# 启用调试模式，请使用 --debug 选项。

if __name__ == '__main__':
    app.run()
