import os
import sys
import requests
from flask import Flask, render_template, redirect, request, make_response, url_for
from forms.user import RegisterForm, LoginForm, MapRequestForm
from data.news import News, NewsForm
from data.sql_forms import User, Map
from data import db_session
from flask_login import LoginManager, login_user, login_required, current_user, logout_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ekxhzywvzbrwucpbwqurrmvoe'

app.config['RECAPTCHA_PUBLIC_KEY'] = '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe'

login_manager = LoginManager()
login_manager.init_app(app)
user = User()
map = Map()


def main():
    db_session.global_init("db/base_sql.db")
    app.run()


@app.route('/test', methods=['GET', 'POST'])
def yandex_map_api():
    form = MapRequestForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        map.coordinates = form.coordinates.data
        map.size = form.size.data
        map.type = form.type.data
        db_sess.add(map)
        db_sess.commit()
        return redirect('/test_map')
    return render_template('map_request.html', title='Запрос карты', form=form)


@app.route('/test_map', methods=['GET', 'POST'])
def yandex_map_api_show():
    coords = '19.138796,43.955195'
    size = '1,1'
    type_map = 'sat'
    map_request = "http://static-maps.yandex.ru/1.x/?ll={}&spn={}&l={}".format(coords, size, type_map)
    response = requests.get(map_request)
    if not response:
        sys.exit(1)
    map_file = "static/images/temporary_map.png"
    with open(map_file, "wb") as file:
        file.write(response.content)
    way = {url_for('static', filename='images/temporary_map.png')}  # TODO почему-то не работает путь до папки, надо
    # TODO разобраться, тогда будет готова эта штука, а ну и реализация связи с sqlalchemy. Связь сделаю.
    print(way)
    return render_template('map_show.html', title='Запрос карты', way=way)


@app.route("/")
def index():
    posts = 'Земля'
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        news = db_sess.query(News).filter(
            (News.user == current_user) | (News.is_private != True))
    else:
        news = db_sess.query(News).filter(
            (News.is_private != True)
        )
    return render_template("index.html", news=news, posts=posts)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Такой пользователь уже есть")

        user.name = form.name.data
        user.email = form.email.data
        user.about = form.about.data
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route("/cookie_test")
def cookie_test():
    visits_count = int(request.cookies.get("visits_count", 0))
    if visits_count:
        res = make_response(
            f"Вы пришли на эту страницу {visits_count + 1} раз")
        res.set_cookie("visits_count", str(visits_count + 1),
                       max_age=60 * 60 * 24 * 365 * 2)
    else:
        res = make_response(
            "Вы пришли на эту страницу в первый раз за последние 2 года")
        res.set_cookie("visits_count", '1',
                       max_age=60 * 60 * 24 * 365 * 2)
    return res


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/news', methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data
        current_user.news.append(news)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('news.html', title='Добавление новости',
                           form=form)


if __name__ == '__main__':
    main()
