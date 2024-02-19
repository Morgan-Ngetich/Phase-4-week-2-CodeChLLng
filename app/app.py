#!/usr/bin/env python3
# Import necessary modules
import os
from flask_cors import CORS
from flask import Flask, jsonify, request
from flask_migrate import Migrate
from models import db, Restaurant, Pizza, RestaurantPizza

# Define a function to create the Flask app
def create_app():
    # Create a Flask app instance
    app = Flask(__name__)
    # Set the database URI from the environment variable
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    # Disable track modifications to improve performance
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Enable CORS for specific origins, methods, and headers
    CORS(app, resources={r"/*": {"origins": "https://pizzas-in.netlify.app", "methods": ["GET", "POST", "DELETE"], "allow_headers": ["Content-Type"]}})

    # Initialize the database
    db.init_app(app)
    # Initialize the database migration engine
    migrate = Migrate(app, db)

    # Enable CORS for all routes
    CORS(app)

    # Define a custom exception class for validation errors
    class ValidationError(Exception):
        def __init__(self, errors):
            self.errors = errors

    # Define an error handler for validation errors
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        response = jsonify({"errors": error.errors})
        response.status_code = 400
        return response

    # Define the home route
    @app.route('/')
    def home():
        return ''

    # Define a route to get all restaurants
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

    # Define a route to get a specific restaurant by id
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

    # Define a route to delete a restaurant by id
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

    # Define a route to get all pizzas
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

    # Define a route to create a restaurant pizza association
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

    # Return the Flask app instance
    return app

# Run the app if this file is executed
if __name__ == '__main__':
    app = create_app()
    app.run(port=5555)
