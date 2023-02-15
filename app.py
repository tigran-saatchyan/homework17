from flask import Flask, request
from flask_restx import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Director(db.Model):
    __tablename__ = 'director'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))

    def __repr__(self):
        return f"Director: {self.id}. {self.name}"


class DirectorSchema(Schema):
    id = fields.Int()
    name = fields.Str()


class Genre(db.Model):
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))

    def __repr__(self):
        return f"Genre: {self.id}. {self.name}"


class GenreSchema(Schema):
    id = fields.Int()
    name = fields.Str()


class Movie(db.Model):
    __tablename__ = 'movie'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.String(255))
    trailer = db.Column(db.String(255))
    year = db.Column(db.Integer)
    rating = db.Column(db.Float)
    genre_id = db.Column(db.Integer, db.ForeignKey("genre.id"))
    genre = db.relationship("Genre")
    director_id = db.Column(db.Integer, db.ForeignKey("director.id"))
    director = db.relationship("Director")

    def __repr__(self):
        return f"Movie: {self.title}({self.year})"


class MovieSchema(Schema):
    id = fields.Int()
    title = fields.Str()
    description = fields.Str()
    trailer = fields.Str()
    year = fields.Int()
    rating = fields.Float()
    genre = fields.Pluck(GenreSchema, "name")
    director = fields.Pluck(DirectorSchema, "name")


api = Api(app)

# Movies CBV

movies_ns = api.namespace("movies", description='Movies operations')
movies_schema = MovieSchema(many=True)
movie_schema = MovieSchema()


@movies_ns.route('/')
class MoviesView(Resource):
    @staticmethod
    def get():
        all_movies = db.session.query(Movie).order_by(Movie.id.asc())

        if not all_movies:
            return "", 404

        page = request.args.get('page')
        per_page = request.args.get('per_page')
        director_id = request.args.get('director_id')
        genre_id = request.args.get('genre_id')

        if per_page:
            if page:
                if int(page) < 1:
                    return "", 404
                all_movies = all_movies.offset(
                    int(per_page) * int(page) - int(per_page)
                )
            all_movies = all_movies.limit(int(per_page))

        if director_id:
            all_movies = all_movies.filter(Movie.director_id == director_id)

        if genre_id:
            all_movies = all_movies.filter(Movie.genre_id == genre_id)

        all_movies = all_movies.all()

        if not all_movies:
            return "", 404

        all_movies = movies_schema.dump(all_movies)
        all_movies.append(
            {
                "page": page,
                "per_page": per_page
            }
        )
        return all_movies, 200

    @staticmethod
    def post():
        new_movie = request.json
        movie = Movie(**new_movie)
        db.session.add(movie)
        db.session.commit()
        return "", 201


@movies_ns.route('/<int:movie_id>')
class MovieView(Resource):
    @staticmethod
    def get(movie_id):
        one_movie = db.session.query(Movie).get(movie_id)
        if not one_movie:
            return "", 404
        return movie_schema.dump(one_movie)

    @staticmethod
    def put(movie_id):
        one_movie = db.session.query(Movie).get(movie_id)
        if not one_movie:
            return "", 404
        movie_dict = request.json

        table_keys = list(one_movie.__table__.columns.keys())
        table_keys.remove('id')

        if set(movie_dict.keys()) != set(table_keys):
            return "", 204

        for column, value in movie_dict.items():
            if column in one_movie.__table__.columns:
                setattr(one_movie, column, value)
        db.session.add(one_movie)
        db.session.commit()
        return "", 200

    @staticmethod
    def patch(movie_id):
        one_movie = db.session.query(Movie).get(movie_id)
        if not one_movie:
            return "", 404
        movie_json = request.json
        for column, value in movie_json.items():
            if column in one_movie.__table__.columns:
                setattr(one_movie, column, value)
        db.session.add(one_movie)
        db.session.commit()
        return "", 200

    @staticmethod
    def delete(movie_id):
        one_movie = db.session.query(Movie).get(movie_id)
        if not one_movie:
            return "", 404

        db.session.delete(one_movie)
        db.session.commit()
        return "", 204


# Directors CBV

director_ns = api.namespace("directors", description='Directors operations')
directors_schema = DirectorSchema(many=True)
director_schema = DirectorSchema()


@director_ns.route('/')
class DirectorsView(Resource):
    @staticmethod
    def get():
        all_directors = db.session.query(Director).all()
        if not all_directors:
            return "", 404
        return directors_schema.dump(all_directors), 200

    @staticmethod
    def post():
        new_director = request.json
        director = Director(**new_director)
        db.session.add(director)
        db.session.commit()
        return "", 201


@director_ns.route('/<int:director_id>')
class DirectorView(Resource):
    @staticmethod
    def get(director_id):
        director = db.session.query(Director).get(director_id)
        if not director:
            return "", 404
        return director_schema.dump(director)

    @staticmethod
    def put(director_id):
        director = db.session.query(Director).get(director_id)
        if not director:
            return "", 404
        movie_dict = request.json

        table_keys = list(director.__table__.columns.keys())
        table_keys.remove('id')

        if set(movie_dict.keys()) != set(table_keys):
            return "", 204

        for column, value in movie_dict.items():
            if column in director.__table__.columns:
                setattr(director, column, value)
        db.session.add(director)
        db.session.commit()
        return "", 200

    @staticmethod
    def patch(director_id):
        director = db.session.query(Director).get(director_id)
        if not director:
            return "", 404
        director_dict = request.json

        for column, value in director_dict.items():
            if column in director.__table__.columns:
                setattr(director, column, value)
        db.session.add(director)
        db.session.commit()
        return "", 200

    @staticmethod
    def delete(director_id):
        director = db.session.query(Director).get(director_id)
        if not director:
            return "", 404
        db.session.delete(director)
        db.session.commit()
        return "", 204


# Genres CBV

genre_ns = api.namespace("genres", description='Genres operations')
genres_schema = GenreSchema(many=True)
genre_schema = GenreSchema()


@genre_ns.route('/')
class GenresView(Resource):
    @staticmethod
    def get():
        all_genres = db.session.query(Genre).all()
        if not all_genres:
            return "", 404
        return genres_schema.dump(all_genres), 200

    @staticmethod
    def post():
        new_genre = request.json
        genre = Genre(**new_genre)
        db.session.add(genre)
        db.session.commit()
        return "", 201


@genre_ns.route('/<int:genre_id>')
class GenreView(Resource):
    @staticmethod
    def get(genre_id):
        genre = db.session.query(Genre).get(genre_id)
        if not genre:
            return "", 404
        return genre_schema.dump(genre)

    @staticmethod
    def put(genre_id):
        genre = db.session.query(Genre).get(genre_id)
        if not genre:
            return "", 404
        genre_dict = request.json

        table_keys = list(genre.__table__.columns.keys())
        table_keys.remove('id')

        if set(genre_dict.keys()) != set(table_keys):
            return "", 204

        for column, value in genre_dict.items():
            if column in genre.__table__.columns:
                setattr(genre, column, value)
        db.session.add(genre)
        db.session.commit()
        return "", 200

    @staticmethod
    def patch(genre_id):
        genre = db.session.query(Genre).get(genre_id)
        if not genre:
            return "", 404
        genre_dict = request.json

        for column, value in genre_dict.items():
            if column in genre.__table__.columns:
                setattr(genre, column, value)
        db.session.add(genre)
        db.session.commit()
        return "", 200

    @staticmethod
    def delete(genre_id):
        genre = db.session.query(Genre).get(genre_id)
        if not genre:
            return "", 404
        db.session.delete(genre)
        db.session.commit()
        return "", 204


if __name__ == '__main__':
    app.run(debug=True)
