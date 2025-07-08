from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from datetime import datetime
from config import Config

# 模拟数据库
class User:
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password
        self.chat_history = []

    def get_id(self):
        return str(self.id)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

# 模拟数据库存储
users_db = {
    "1": User("1", "testuser", generate_password_hash("testpass"))
}

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return users_db.get(user_id)

def call_deepseek_api(prompt):
    # 模拟API响应
    return {
        "content": f"这是对'{prompt}'的模拟回复。在实际应用中，这里会调用DeepSeekR1 API。",
        "timestamp": datetime.now().isoformat()
    }

@app.route('/')
@login_required
def home():
    return redirect(url_for('profile'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = next((u for u in users_db.values() if u.username == username), None)

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('profile'))
        else:
            flash("无效的用户名或密码", "error")

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    chat_id = request.args.get('chat_id')
    selected_chat = None

    if chat_id:
        selected_chat = next((c for c in current_user.chat_history if c["id"] == chat_id), None)

    if request.method == 'POST':
        prompt = request.form.get('prompt')

        if prompt:
            response = call_deepseek_api(prompt)

            if selected_chat:
                # 继续现有对话
                selected_chat["messages"].append({
                    "role": "user",
                    "content": prompt,
                    "timestamp": datetime.now().isoformat()
                })
                selected_chat["messages"].append({
                    "role": "assistant",
                    "content": response["content"],
                    "timestamp": response["timestamp"]
                })
            else:
                # 新对话
                conversation = {
                    "id": str(uuid.uuid4()),
                    "title": prompt[:30] + ("..." if len(prompt) > 30 else ""),
                    "messages": [
                        {"role": "user", "content": prompt, "timestamp": datetime.now().isoformat()},
                        {"role": "assistant", "content": response["content"], "timestamp": response["timestamp"]}
                    ],
                    "created_at": datetime.now().isoformat()
                }
                current_user.chat_history.append(conversation)
                selected_chat = conversation

            return redirect(url_for('chat', chat_id=selected_chat["id"]))

    return render_template(
        'chat.html',
        user=current_user,
        selected_chat=selected_chat,
        suggestions=[
            "如何提高工作效率？",
            "解释一下量子计算的基本概念",
            "写一封辞职信的模板"
        ]
    )

from markdown import markdown

@app.template_filter('format_time')
def format_time_filter(iso_string):
    dt = datetime.fromisoformat(iso_string)
    return dt.strftime('%H:%M')

@app.template_filter('markdown')
def markdown_filter(text):
    return markdown(text)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username and password:
            user_id = str(uuid.uuid4())
            hashed_password = generate_password_hash(password)
            new_user = User(user_id, username, hashed_password)
            users_db[user_id] = new_user
            flash("注册成功，请登录", "success")
            return redirect(url_for('login'))
        else:
            flash("用户名和密码不能为空", "error")

    return render_template('register.html')

@app.route('/delete_chat/<chat_id>', methods=['POST'])
@login_required
def delete_chat(chat_id):
    # 从当前用户的聊天历史中移除指定的聊天记录
    current_user.chat_history = [chat for chat in current_user.chat_history if chat["id"] != chat_id]
    return redirect(url_for('chat'))

if __name__ == '__main__':
    app.run(debug=True)