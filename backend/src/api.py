import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
from sqlalchemy.sql.elements import AsBoolean

from .database.models import (db_drop_and_create_all,
                              setup_db, Drink)
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)


db_drop_and_create_all()

# ROUTES


@app.route("/drinks", methods=["GET"])
def get_drinks():
    return jsonify({
        "success": True,
        "drinks": [Drink.short(drink)
                   for drink in Drink.query.all()]
    })


@app.route("/drinks-detail", methods=["GET"])
@requires_auth("get:drinks-detail")
def get_drinks_details(payload):
    return jsonify({
        "success": True,
        "drinks": [Drink.long(drink)
                   for drink in Drink.query.all()]
    })


def noneChecker(value):
    return value is None


def drink_serilizer(body):
    if body is None:
        abort(400)
    title = body.get("title", None)
    recipe = body.get("recipe", None)
    print(recipe)

    is_not_valid = any(
        [noneChecker(title), noneChecker(recipe)])

    if is_not_valid:
        abort(400)

    return Drink(title=title, recipe=json.dumps(recipe))


@app.route("/drinks", methods=["POST"])
@requires_auth("post:drinks")
def create_drink(payload):

    try:
        body = request.get_json()
        drink = drink_serilizer(body)
        drink.insert()
        return jsonify({
            "success": True,
            "drinks": [drink.long()]
        })
    except Exception as e:
        print(e)
        abort(422)


@app.route("/drinks/<id>", methods=["PATCH"])
@requires_auth("patch:drinks")
def update_drink(payload, id):
    try:
        drink = Drink.query.get_or_404(id)
        body = request.get_json()

        title = body.get("title", None)
        if not noneChecker(title):
            drink.title = title

        recipe = body.get("recipe", None)
        if not noneChecker(recipe):
            drink.recipe = json.dumps(recipe)

        drink.update()

        return jsonify({
            "success": True,
            "drinks": [drink.long()]
        })
    except Exception as e:
        print(e)
        abort(422)


@app.route("/drinks/<id>", methods=["DELETE"])
@requires_auth("delete:drinks")
def delete_drink(payload, id):
    drink = Drink.query.get_or_404(id)
    deleted_id = drink.id
    drink.delete()

    return jsonify({
        "success": True,
        "delete": deleted_id,
    })


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "Not found"
    }), 404


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "Unable to process"
    }), 422


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "Bad request"
    }), 400


@app.errorhandler(AuthError)
def auth_error_handler(e):
    return jsonify({
        "success": False,
        "error": e.status_code,
        "message": e.error
    }), e.status_code
