
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
