import datetime
from flask import Flask, render_template, request, jsonify, Response, stream_with_context, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
from volcenginesdkarkruntime import Ark

# 加载 .env 文件中的环境变量
load_dotenv(override=True)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
client = Ark(
    base_url=os.getenv("ARK_BASE_URL"),
    api_key=os.getenv("ARK_API_KEY")
)

# 初始化 Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# 数据模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)


class ChatSession(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    is_used = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 关联用户
    messages = db.relationship('ChatMessage', backref='session', lazy='dynamic')


class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey('chat_session.id'))
    role = db.Column(db.String(10))
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now)


# 初始化数据库
with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# 注册路由
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_pw = generate_password_hash(password)
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('register'))
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('chat'))
    return render_template('register.jinja')


# 登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('chat'))
        flash('用户名或密码错误')
    return render_template('login.jinja')


# 登出路由
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"success": True}), 200


# chat 页面
@app.route('/chat')
@login_required
def chat():
    sessions = ChatSession.query.filter_by(user_id=current_user.id).order_by(ChatSession.created_at.desc()).all()
    session_data = []
    for s in sessions:
        last_msg = s.messages.order_by(ChatMessage.timestamp.desc()).first()
        session_data.append({
            "id": s.id,
            "created_at": s.created_at.strftime("%Y-%m-%d %H:%M"),
            "preview": last_msg.content[:20] + '...' if last_msg else "新会话"
        })
    return render_template('chat.jinja', sessions=session_data)


# 其他路由（/create-session, /get-messages, /chat-stream）都添加@login_required
# 修改/create-session路由中的会话创建逻辑，关联当前用户
@app.route('/create-session', methods=['POST'])
@login_required
def create_session():
    try:
        # 检查是否存在未使用的会话
        unused_session = ChatSession.query.filter_by(is_used=False, user_id=current_user.id).order_by(
            ChatSession.created_at.desc()).first()

        if unused_session:
            return jsonify({
                "success": True,
                "session_id": unused_session.id,
                "created_at": unused_session.created_at.strftime("%Y-%m-%d %H:%M"),
                "is_new": False  # 标记是否为新建
            })

        # 创建新会话
        response = client.context.create(
            model='ep-20250123190804-d927p',
            mode="session",
            messages=[{"role": "system", "content": "你是豆包，是由字节跳动开发的 AI 人工智能助手"}],
            ttl=datetime.timedelta(minutes=60)
        )
        token = response.id

        new_session = ChatSession(id=token, is_used=False, user_id=current_user.id)
        db.session.add(new_session)
        db.session.commit()

        return jsonify({
            "success": True,
            "session_id": token,
            "created_at": new_session.created_at.strftime("%Y-%m-%d %H:%M"),
            "is_new": True
        })

    except Exception as e:
        print(f"Error creating session: {str(e)}")  # 添加错误日志
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/get-messages')
def get_messages():
    """获取指定会话的消息记录"""
    session_id = request.args.get('session_id')
    messages = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.timestamp.asc()).all()

    return jsonify([{
        "role": msg.role,
        "content": msg.content,
        "time": msg.timestamp.strftime("%H:%M")
    } for msg in messages])


@app.route('/chat-stream', methods=['POST'])
def chat_stream():
    # 在生成器外部捕获所有请求数据
    token = request.headers.get('X-Auth-Token')
    user_content = request.json.get('message', '')

    # 标记会话已使用
    current_session = ChatSession.query.get(token)
    if current_session and not current_session.is_used:
        current_session.is_used = True
        db.session.commit()

    # 保存用户消息到数据库
    user_msg = ChatMessage(
        session_id=token,
        role='user',
        content=user_content
    )
    db.session.add(user_msg)
    db.session.commit()  # 立即提交用户消息

    # 生成器函数
    def generate():
        # 使用生成器函数, 使用流式API获取回复. 
        stream = client.context.completions.create(
            context_id=token,
            model='ep-20250123190804-d927p',
            messages=[{"role": "user", "content": user_content}],
            stream=True
        )

        full_response = []
        # 遍历流式响应
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response.append(content)
                yield content  # 流式返回内容

        # 保存AI回复到数据库
        ai_msg = ChatMessage(
            session_id=token,
            role='assistant',
            content=''.join(full_response)
        )
        db.session.add(ai_msg)
        db.session.commit()

    # 使用stream_with_context保持请求上下文
    return Response(stream_with_context(generate()), mimetype='text/plain')


if __name__ == '__main__':
    app.run(debug=True)
