import os

from shutil import rmtree
import requests
from flask import Flask, render_template, redirect, request, make_response
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
    if not os.path.exists('static/images/'):
        os.makedirs('static/images/')
    app.run()
    rmtree('static/images/')


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
    db_sess = db_session.create_session()
    place = db_sess.query(Map).order_by(Map.id.desc()).first()
    coords = place.coordinates
    size = place.size
    type_map = place.type
    map_request = "http://static-maps.yandex.ru/1.x/?ll={}&spn={}&l={}".format(coords, size, type_map)
    response = requests.get(map_request)
    if not response:
        db_sess.query(Map).filter(Map.coordinates == coords).delete(synchronize_session='evaluate')
        db_sess.commit()
        return render_template('map_show.html', title='Запрос карты', way=None, message='Ошибка запроса карты')
    map_file = "static/images/{}_{}_{}.png".format(coords, size, type_map)
    print(map_file)
    with open(map_file, "wb") as file:
        file.write(response.content)
    return render_template('map_show.html', title='Запрос карты',
                           way=map_file, message='координаты:{} размер:{} тип:{}'.format(coords, size, type_map))


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

@app.route("/article", methods=['GET', 'POST'])
def image():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id, User.article_id == 1, User.was_read == False)
        if user:
            user.was_read = True
            user.article_score = int(request.form['rating'])
            return render_template("type_article.html", was_read=0)
        else:
            return render_template("type_article.html", was_read=1, rating=user.article_score)


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


@app.route('/profile')
@login_required
def profile_redirect():
    return redirect('/profile/{}'.format(current_user.id))


@app.route('/profile/<id>')
def profile_page(id):
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        id_user = db_sess.query(User).filter(
            User.id == id).first()
        if id_user is not None:
            db_sess = db_session.create_session()
            news = db_sess.query(News).filter(
                (News.user_id == id)).filter(News.is_private != True)
            return render_template('profile.html', form=(id_user, news))
        return render_template('404.html', message='Такого пользователя не существует')
    return render_template('404.html', message='Вы не вошли в аккаунт')

if __name__ == '__main__':
    main()
