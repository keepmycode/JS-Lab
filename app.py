import json
import re
import os
from datetime import datetime

from flask import (
    Flask, render_template, redirect,
    url_for, request, flash
)
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, UserTaskProgress
from forms import RegisterForm, LoginForm

def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-key-ascii-only'),
        SQLALCHEMY_DATABASE_URI="sqlite:///data.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    # Инициализация БД
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # Загрузка данных задач из JSON
    tasks_file = os.path.join(app.root_path, 'tasks', 'levels.json')
    with open(tasks_file, encoding='utf-8') as f:
        levels_data = json.load(f)

    # Flask-Login
    login = LoginManager(app)
    login.login_view = 'login'
    @login.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # current_year в шаблонах
    @app.context_processor
    def inject_now():
        return {'current_year': datetime.utcnow().year}

    # --- Маршруты ---

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('levels'))
        form = RegisterForm()
        if form.validate_on_submit():
            user = User(
                username=form.username.data,
                password=generate_password_hash(form.password.data)
            )
            db.session.add(user)
            db.session.commit()
            flash("Успешно зарегистрированы, войдите.", "success")
            return redirect(url_for('login'))
        return render_template('register.html', form=form)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('levels'))
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('levels'))
            flash("Неверные имя пользователя или пароль.", "danger")
        return render_template('login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))

    @app.route('/levels')
    @login_required
    def levels():
        info = []
        for lvl_id, lvl in levels_data.items():
            total = len(lvl['tasks'])
            done = UserTaskProgress.query.filter_by(
                user_id=current_user.id,
                level=int(lvl_id),
                completed=True
            ).count()
            if lvl_id == "1":
                unlocked = True
            else:
                prev_done = UserTaskProgress.query.filter_by(
                    user_id=current_user.id,
                    level=int(lvl_id)-1,
                    completed=True
                ).count()
                unlocked = prev_done == len(levels_data[str(int(lvl_id)-1)]['tasks'])
            info.append({
                'id':       int(lvl_id),
                'title':    lvl['title'],
                'done':     done,
                'total':    total,
                'unlocked': unlocked
            })
        return render_template('levels.html', info=info)

    @app.route('/task/<int:level>/<int:idx>', methods=['GET', 'POST'])
    @login_required
    def task(level, idx):
        lvl = levels_data.get(str(level))
        if not lvl or idx < 0 or idx >= len(lvl['tasks']):
            return "Задача не найдена", 404

        # Проверка разблокировки уровня
        if level > 1:
            prev_done = UserTaskProgress.query.filter_by(
                user_id=current_user.id,
                level=level-1,
                completed=True
            ).count()
            if prev_done < len(levels_data[str(level-1)]['tasks']):
                flash("Сначала завершите предыдущий уровень.", "warning")
                return redirect(url_for('levels'))

        task = lvl['tasks'][idx]

        if request.method == 'POST':
            data = task['payload']
            correct = False

            if task['type'] == 'mcq':
                sel = int(request.form.get('choice', -1))
                correct = (sel == data['correct'])

            elif task['type'] == 'ordering':
                order = request.form.get('block', '').split('||')
                seq = [data['blocks'][i] for i in data['correct_order']]
                correct = (order == seq)

            elif task['type'] == 'fill':
                ans = request.form.get('fillin', '').strip()
                correct = bool(re.fullmatch(data['answer_regex'], ans))

            # Сохраняем прогресс
            prog = UserTaskProgress.query.filter_by(
                user_id=current_user.id,
                level=level,
                task_idx=idx
            ).first()
            if not prog:
                prog = UserTaskProgress(
                    user_id=current_user.id,
                    level=level,
                    task_idx=idx,
                    completed=correct
                )
                db.session.add(prog)
            else:
                prog.completed = correct
            db.session.commit()

            if correct:
                flash("Правильно!", "success")
                # Перейти к следующей задаче, если она есть
                if idx + 1 < len(lvl['tasks']):
                    return redirect(url_for('task', level=level, idx=idx+1))
                # Иначе — уровень завершён
                flash(f"Вы завершили уровень «{lvl['title']}»!", "info")
                return redirect(url_for('levels'))
            else:
                flash("Неверно, попробуйте ещё раз.", "danger")

        return render_template(
            'task.html',
            level=level,
            video=task['video'],
            task=task,
            idx=idx
        )

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
