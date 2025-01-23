import datetime
from flask import Flask, Response, stream_with_context, session, render_template, request
import uuid
import os
from volcenginesdkarkruntime import Ark

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.urandom(24)

client = Ark(
    base_url=os.getenv("ARK_BASE_URL"),
    api_key=os.getenv("ARK_API_KEY")
)

doubao_pro_128k = 'ep-20250120130849-sd562'
doubao_15pro_32k = 'ep-20250123190804-d927p'
current_model = doubao_15pro_32k


@app.route('/chat')
def chat():
    # 打印创建上下文的提示信息
    print("----- create context -----")
    # 调用client的context.create方法创建一个会话上下文
    response = client.context.create(
        # 指定模型
        model=current_model,
        # 指定模式为会话
        mode="session",
        # 设置消息列表，包含一个系统角色的消息
        messages=[
            {"role": "system", "content": "你是豆包，是由字节跳动开发的 AI 人工智能助手"},
        ],
        # 设置会话的生存时间为60分钟
        ttl=datetime.timedelta(minutes=60),
    )
    # 打印创建上下文的响应结果
    print(response)
    token = response.id
    # token = str(uuid.uuid4())
    session['auth_token'] = token
    return render_template('chat.html', token=token)


@app.route('/chat-stream', methods=['POST', 'OPTIONS'])
def chat_stream():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()

    token = request.headers.get('X-Auth-Token')
    if not token or token != session.get('auth_token'):
        return _cors_response('Unauthorized', 401)

    user_content = request.json.get('message', '')

    def generate():
        # stream = client.chat.completions.create(
        stream = client.context.completions.create(
            # 指定上下文ID
            context_id=token,
            model=current_model,
            messages=[
                {"role": "user", "content": user_content},
            ],
            stream=True
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    return _cors_response(stream_with_context(generate()))


def _build_cors_preflight_response():
    response = Response()
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Auth-Token'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    return response


def _cors_response(content, status=200):
    response = Response(content, status=status, mimetype='text/plain')
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


if __name__ == '__main__':
    app.run()
