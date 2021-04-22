import flask
from . import db_session
from .sql_forms import *

blueprint = flask.Blueprint(
    'api',
    __name__,
    template_folder='templates'
)


@blueprint.route('/api/news')
def get_news():
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.is_private != True)
    if news.first() is not None:
        return flask.jsonify(
            {
                'news':
                    [item.to_dict(only=('id', 'title', 'content', 'user.id'))
                     for item in news]
            }
        )
    return flask.jsonify(
        {
            'news':
                'нет доступных новостей'
        }
    )


@blueprint.route('/api/news/<id>')
def get_news_by_id(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(
        (News.id == id)).filter(News.is_private != True)
    if news.first() is not None:
        return flask.jsonify(
            {
                'news':
                    [item.to_dict(only=('id', 'title', 'content', 'user.id'))
                     for item in news]
            }
        )
    return flask.jsonify(
        {
            'news':
                'новость недоступна'
        }
    )


@blueprint.route('/api/profiles')
def get_profiles():
    db_sess = db_session.create_session()
    users = db_sess.query(User).all()
    if users is not None:
        return flask.jsonify(
            {
                'profiles':
                    [item.to_dict(only=('id', 'name', 'email', 'created_date'), )
                     for item in users]
            }
        )
    return flask.jsonify(
        {
            'profiles':
                'нет пользователей'
        }
    )


@blueprint.route('/api/profiles/<id>')
def get_profile_by_id(id):
    db_sess = db_session.create_session()
    users = db_sess.query(User).filter(
        (User.id == id))
    if users.first() is not None:
        news = db_sess.query(News).filter(
            (News.user_id == id)).filter(News.is_private != True)
        return flask.jsonify(
            dict(profile=[item.to_dict(only=('id', 'name', 'email', 'created_date',), )
                          for item in users],
                 profile_news=[item.to_dict(only=('id', 'title', 'content',), )
                               for item in news])
        )
    return flask.jsonify(
        {
            'profiles':
                'такого пользователя не существует'
        }
    )


@blueprint.route('/api/maps')
def get_maps():
    db_sess = db_session.create_session()
    maps = db_sess.query(Map).all()
    if maps is not None:
        return flask.jsonify(
            {
                'maps':
                    [item.to_dict(only=('id', 'coordinates', 'size', 'type'))
                     for item in maps]
            }
        )
    return flask.jsonify(
        {
            'maps':
                'нет запросов карт'
        }
    )


@blueprint.route('/api/maps/<id>')
def get_maps_by_id(id):
    db_sess = db_session.create_session()
    maps = db_sess.query(Map).filter(
        (Map.id == id))
    if maps.first() is not None:
        return flask.jsonify(
            {
                'map':
                    [item.to_dict(only=('id', 'coordinates', 'size', 'type'))
                     for item in maps]
            }
        )
    return flask.jsonify(
        {
            'maps':
                'такого запроса не существует'
        }
    )
