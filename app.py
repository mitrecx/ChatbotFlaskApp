from flask import Flask, Response, stream_with_context
from flask import render_template, request
from volcenginesdkarkruntime import Ark
import os

client = Ark(
    base_url=os.getenv("ARK_BASE_URL"),
    api_key=os.getenv("ARK_API_KEY")
)

app = Flask(__name__)


@app.route('/chat')
def chat():
    return render_template('chat.html')


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


# 运行应用程序: flask --app 文件名(不含.py后缀) run; 如果文件名为 app.py 或 wsgi.py, 可以简写为: flask run
# 告诉您的操作系统侦听所有公有 IP: flask run --host=0.0.0.0
# 启用调试模式，请使用 --debug 选项。

if __name__ == '__main__':
    app.run()
