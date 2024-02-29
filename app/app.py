#!/usr/bin/env python3
import os
from flask_cors import CORS
from flask import Flask, jsonify, request, render_template
from flask_migrate import Migrate
from models import db, Restaurant, Pizza, RestaurantPizza

# export DATABASE_URL=postgresql://morgan:uRmATMYHWLmA4Gt2IZVPinYmPAFCuAz7@dpg-cngb178l5elc739651ig-a.oregon-postgres.render.com/pizzas_3pv0
# SHOULD RUN ON PORT 5000


def create_app():
    
    app = Flask(
        __name__,
        static_url_path='',
        static_folder='../client/build',
        template_folder='../client/build'
    )
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # CORS(app, resources={r"/*": {"origins": "https://pizzas-sdfw-onrender.onrender.com", "methods": ["GET", "POST", "DELETE"], "allow_headers": ["Content-Type"]}})

    CORS(app)
    
    db.init_app(app)
    migrate = Migrate(app, db)

    class ValidationError(Exception):
        def __init__(self, errors):
            self.errors = errors

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        response = jsonify({"errors": error.errors})
        response.status_code = 400
        return response

    @app.errorhandler(404)
    def not_found(e):
        return render_template("index.html")

    @app.route('/')
    def home():
        return ''

    @app.route('/restaurants', methods=['GET'])
    def get_restaurants():
        restaurants = Restaurant.query.all()
        data = [
            {
                'id': restaurant.id,
                'name': restaurant.name,
                'address': restaurant.address
            } for restaurant in restaurants
        ]
        return jsonify(data)

    @app.route('/restaurants/<int:id>', methods=['GET'])
    def get_restaurant(id):
        restaurant = Restaurant.query.get(id)
        if restaurant:
            data = [{
                'id': restaurant.id,
                'name': restaurant.name,
                'address': restaurant.address,
                'pizzas': [
                    {
                        'id': pizza.id,
                        'name': pizza.name,
                        'ingredients': pizza.ingredients
                    } for pizza in restaurant.pizzas]
            }]
            return jsonify(data)
        else:
            return jsonify({'error': 'Restaurant not found'}), 404

    @app.route('/restaurants/<int:id>', methods=['DELETE'])
    def delete_restaurant(id):
        restaurant = Restaurant.query.get(id)
        if restaurant:
            RestaurantPizza.query.filter_by(restaurant_id=id).delete()
            db.session.delete(restaurant)
            db.session.commit()
            return '', 204
        else:
            return jsonify({'error': 'Restaurant not found'}), 404

    @app.route('/pizzas', methods=['GET'])
    def get_pizzas():
        pizzas = Pizza.query.all()
        data = [
            {
                'id': pizza.id,
                'name': pizza.name,
                'ingredients': pizza.ingredients
            } for pizza in pizzas
        ]
        return jsonify(data)

    @app.route('/restaurant_pizzas', methods=['POST'])
    def create_restaurant_pizza():
        data = request.json
        if data.get('price') is None or not 1 <= data.get('price') <= 30:
            raise ValidationError({'price': 'Price must be between 1 and 30.'})

        restaurant_pizza = RestaurantPizza(**data)
        db.session.add(restaurant_pizza)
        try:
            db.session.commit()
            pizza = Pizza.query.get(data['pizza_id'])
            if pizza:
                return jsonify(
                    {
                        'id': pizza.id,
                        'name': pizza.name,
                        'ingredients': pizza.ingredients
                    }), 201
            else:
                return jsonify({'error': 'Pizza not found'}), 404
        except:
            db.session.rollback()
            return {'errors': ['validation errors']}, 400

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
