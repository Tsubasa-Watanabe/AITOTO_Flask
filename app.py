import datetime
import os
import random
from enum import unique

import pytz
from flask import Flask, flash, redirect, render_template, request, session
from flask_login import (LoginManager, UserMixin, login_required, login_user,
                         logout_user)
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///info.db"
db = SQLAlchemy(app)

migrate = Migrate(app, db)

# ログインを管理するための設定
login_manager = LoginManager()
login_manager.init_app(app)


app.config['SECRET_KEY'] = 'secret_key'
app.config['USERNAME'] = 'user'
app.config['PASSWORD'] = 'pass'

UPLOAD_FOLDER = './static/up'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

class Database(db.Model):
    __tablename__ = 'database'
    id = db.Column(db.Integer, primary_key=True)  # ID
    date = db.Column(db.DateTime, default=datetime.datetime.now(pytz.timezone('Asia/Tokyo'))) # 日付と時間
    title = db.Column(db.String(100), nullable=True) # タイトル
    note = db.Column(db.Text, nullable=True) # メモ
    file_path = db.Column(db.String(255), nullable=True)

# ユーザー情報を管理するデータベース
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  # ID
    username = db.Column(db.String(30), nullable=False, unique=True)  # ユーザー名
    password = db.Column(db.String(12), nullable=False)  # パスワード
    birthday = db.Column(db.String(30), nullable=True) # 生年月日
    gender = db.Column(db.String(50)) #性別

    def __init__(self, username, password, birthday, gender):
    # def __init__(self, username, password, birthday):
        self.username = username
        self.password = password
        self.birthday = birthday
        self.gender = gender


# アンケート情報を管理するデータベース
class SurveyData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipient_name = db.Column(db.String(255))
    gender = db.Column(db.String(50))
    age = db.Column(db.String(50))
    relationship = db.Column(db.String(50))
    occasion = db.Column(db.String(50))
    gift_reason = db.Column(db.String(255))
    additional_notes = db.Column(db.Text)

# ユーザーローダー関数を設定
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

# トップページはシンプルにindex.htmlを表示するだけ
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')

# アンケートページ
@app.route('/submit_survey', methods=['GET', 'POST'])
def submit_survey():
    if request.method == 'POST': # POST
        recipient_name = request.form.get('recipientName')
        # genderだけbuttonなのでif文で仕分け
        if request.form.get('genderMale') == 'male':
            gender = 'male'
        elif request.form.get('genderFemale') == 'female':
            gender = 'female'
        elif request.form.get('genderOther') == 'other':
            gender = 'other'
        else:
            gender = 'Null'
        age = request.form.get('age')
        relationship = request.form.get('relationship')
        occasion = request.form.get('occasion')
        gift_reason = request.form.get('giftReason')
        additional_notes = request.form.get('additionalNotes')

        # デバッグ
        print(recipient_name)
        print(gender)
        print(age)
        print(relationship)
        print(occasion)
        print(gift_reason)

        # すべてのデータが入力されているかチェック
        if not recipient_name or not gender or not age or not relationship or not occasion or not gift_reason:
            flash('必須項目を入力してください。', 'error')
            return redirect(request.url)
        
        else:
            flash('送信完了しました。', 'success')

            # データベースに送信
            survey_data = SurveyData(
                recipient_name=recipient_name,
                gender=gender,
                age=age,
                relationship=relationship,
                occasion=occasion,
                gift_reason=gift_reason,
                additional_notes=additional_notes
            )

            db.session.add(survey_data)
            db.session.commit()
            
            return redirect('/')
    
    else:
        return render_template('question.html')

# 会員登録機能を追加
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        birthday = request.form.get("birthday")
        # genderだけbuttonなのでif文で仕分け
        if request.form.get('genderMale') == 'male':
            gender = 'male'
        elif request.form.get('genderFemale') == 'female':
            gender = 'female'
        elif request.form.get('genderOther') == 'other':
            gender = 'other'
        else:
            gender = 'Null'
        

        print(username)
        print(password)
        print(gender)
        print(birthday)

        # ユーザー名が既に使用されているかどうかをチェック
        if User.query.filter_by(username=username).first():
            flash('ユーザ名は既に使用されています')
            return redirect('/register')
        else:
            # ユーザー情報をデータベースに登録
            user = User(
                username=username, 
                password=password,
                birthday=birthday,
                gender=gender,
                )
            db.session.add(user)
            db.session.commit()

        flash('会員登録が完了しました')
        return redirect('/login')
    
    else:
        return render_template('register.html')

# ログイン機能を追加
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
    
        user = User.query.filter_by(username=username).first()
        # パスワードはハッシュ化されているので、check_password_hashを使ってユーザー名、パスワードが正しいかチェック
        if (user.password == password):
            login_user(user)
            return redirect('/')
        else:
            flash('ユーザ名もしくはパスワードが異なります')
            return render_template('login.html')
    
    else:
        return render_template('login.html')

# ログアウト機能を追加
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/preview_page', methods=['GET', 'POST'])
# ログイン中でないとアクセスできないようにする
@login_required
def preview():
    if request.method == 'POST':
        title = request.form.get('title')
        note = request.form.get('note')
        file = request.files['file']
        dstr = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        filename = dstr + str(random.randint(0, 10000)) + ".jpg"

        if filename == '':
            flash("ファイルが選択されていません")
            return redirect('/preview_page')

        savepath = os.path.join('static', 'up', filename)
        file.save(savepath)

        data = Database(title=title, note=note, file_path=filename)
        db.session.add(data)
        db.session.commit()

        return redirect('/list')
    else:
        return render_template('preview.html')

@app.route('/list')
# ログイン中でないとアクセスできないようにする
@login_required
def list():
    posts = Database.query.all()
    return render_template('list.html', posts=posts)

if __name__ == '__main__':
    app.run(debug=True)