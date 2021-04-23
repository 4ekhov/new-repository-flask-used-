import os
from shutil import rmtree
import requests
from flask import Flask, render_template, redirect, request
from forms.user import RegisterForm, LoginForm, MapRequestForm, NewsForm, RatingForm
from data.sql_forms import User, Map, News, Article
from data import db_session, api
from flask_login import LoginManager, login_user, current_user, logout_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ekxhzywvzbrwucpbwqurrmvoe'
app.config['RECAPTCHA_PUBLIC_KEY'] = '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe'
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config['JSON_AS_ASCII'] = False

login_manager = LoginManager()
login_manager.init_app(app)
user = User()
map = Map()


def main():
    db_session.global_init("db/base_sql.db")
    app.register_blueprint(api.blueprint)
    if not os.path.exists('static/images/'):
        os.makedirs('static/images/')
    app.run()
    rmtree('static/images/')


def article(article_id):
    ways = ['earth_article.png',
            'water_article.png',
            'fire_article.png',
            'air_article.png']
    way = ways[article_id - 1]
    pics = ['earth.jpeg',
            'water.jpg',
            'fire.jpg',
            'air.jpg']
    pic = pics[article_id - 1]
    db_sess = db_session.create_session()
    art = db_sess.query(Article).filter(Article.id == article_id).first()
    form = RatingForm()
    users_id, users_score = art.users_id, art.users_score
    users_id, users_score = list(users_id), list(users_score)
    try:
        if str(current_user.id) in users_id:
            num = users_id.index(str(current_user.id))
            print(art.users_score[num])
            return render_template("type_article.html", title='Статья', way=way, was_scored=1,
                                   article_score=int(art.users_score[num]), form=form,
                                   column1=art.text, column2=art.text_2, pic=pic)
        else:
            form = RatingForm()
            if form.validate_on_submit():
                art.users_id = str(art.users_id) + str(current_user.id)
                art.users_score = str(art.users_score) + str(form.rating.data)
                db_sess.commit()
                return render_template("type_article.html", title='Статья', way=way, was_scored=1,
                                       article_score=int(art.users_score[-1]), form=form,
                                       column1=art.text, column2=art.text_2, pic=pic)
            return render_template("type_article.html", title='Статья', way=way, was_scored=0, form=form,
                                   column1=art.text, column2=art.text_2, pic=pic)
    except AttributeError:
        return redirect('/')


@app.route('/yandex_api', methods=['GET', 'POST'])
def yandex_map_api():
    form = MapRequestForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        map.coordinates = form.coordinates.data
        map.size = form.size.data
        map.type = form.type.data
        db_sess.add(map)
        db_sess.commit()
        return redirect('/yandex_api_map')
    return render_template('map_request.html', title='Запрос карты', form=form)


@app.route('/yandex_api_map', methods=['GET', 'POST'])
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
        return render_template('map_show.html', title='Запрос карты', way=None,
                               message='Ошибка запроса карты: неправильные данные или нет ответа от сервера')
    map_file = "static/images/{}_{}_{}.png".format(coords, size, type_map)
    with open(map_file, "wb") as file:
        file.write(response.content)
    return render_template('map_show.html', title='Запрос карты',
                           way=map_file, message='координаты:{} размер:{} тип:{}'.format(coords, size, type_map))


@app.route("/")
def index():
    posts = 'Новости пользователей'
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter((News.is_private != True))
    return render_template("index.html", news=news, posts=posts)


@app.route("/article_earth", methods=['GET', 'POST'])
def earth():
    return article(1)


@app.route("/article_water", methods=['GET', 'POST'])
def water():
    return article(2)


@app.route("/article_fire", methods=['GET', 'POST'])
def fire():
    return article(3)


@app.route("/article_air", methods=['GET', 'POST'])
def air():
    return article(4)


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
def logout():
    if current_user.is_authenticated:
        logout_user()
        return redirect("/")
    return render_template('error.html', message='Вы не вошли в аккаунт')


@app.route('/news', methods=['GET', 'POST'])
def add_news():
    if current_user.is_authenticated:
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
    return render_template('error.html', message='Вы не вошли в аккаунт')


@app.route('/profile')
def profile_redirect():
    if current_user.is_authenticated:
        return redirect('/profile/{}'.format(current_user.id))
    return render_template('error.html', message='Вы не вошли в аккаунт')


@app.route('/profile/<id>')
def profile_page(id):
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        id_user = db_sess.query(User).filter(
            User.id == id).first()
        if id_user is not None:
            db_sess = db_session.create_session()
            news = db_sess.query(News).filter(
                (News.user_id == id))
            if id != current_user.id:
                news = news.filter(News.is_private is not True)
            return render_template('profile.html', title='Профиль', form=(id_user, news))
        return render_template('error.html', message='Такого пользователя не существует')
    return render_template('error.html', message='Вы не вошли в аккаунт')


@app.errorhandler(404)
def not_found():
    return render_template('error.html', message='Неизвестная ошибка')


@app.errorhandler(500)
def not_found():
    return render_template('error.html', message='такой страницы не существует')


if __name__ == '__main__':
    main()
