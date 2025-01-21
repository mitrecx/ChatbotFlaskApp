import sqlite3

# 连接数据库（不存在则创建）
conn = sqlite3.connect('example.db')
cursor = conn.cursor()

# 创建表
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)''')

# 插入数据
# cursor.execute("INSERT INTO users (name, age) VALUES (?, ?)", ('Alice', 30))

# 查询数据
cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()
for row in rows:
    print(row)

# 提交事务并关闭连接
conn.commit()
conn.close()