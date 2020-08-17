#!/usr/bin/python
from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from functools import wraps
import jwt
import random
from GroceriesDB import GroceriesDB

db = GroceriesDB()

app = Flask(__name__)
api = Api(app)


class GetStores(Resource):
    def get(self):
        args = request.args
        lat = args["lat"]
        lng = args["lng"]
        radius = args["radius"]
        return jsonify(db.get_nearby_stores(lat=lat, lng=lng, radius=radius))


class GetStoresAndInventory(Resource):
    def get(self):
        args = request.args
        lat = args["lat"]
        lng = args["lng"]
        radius = args["radius"]
        nearby_stores = db.get_nearby_stores(lat=lat, lng=lng, radius=radius)
        return jsonify(db.get_stores_inventory(nearby_stores))

class GetStore(Resource):
    def get(self):
        args = request.args
        place_id = args["place_id"]
        return jsonify(db.get_single_store(place_id))


class PostInventory(Resource):
    def post(self):
        json_data = request.get_json(force=True)
        try:
                submitted = db.update_inventory(json_data)
        except Exception as e:
                with open("./grocery.logs", "a+") as f:
                        f.write("{0}\n".format(str(e)))
                return jsonify({"pass":False,"message":str(e)})
        return jsonify(submitted)

class UpsertInventory(Resource):
    def post(self):
        json_data = request.get_json(force=True)
        if "data" not in json_data.keys():
            return jsonify({"pass":False,"message":"Failed API call for missing key"})

        return jsonify(db.upsert_inventory(json_data["data"]))

api.add_resource(GetStores, "/getstores")
api.add_resource(GetStore, "/getstore")
api.add_resource(GetStoresAndInventory, "/getstoresinventory")
api.add_resource(PostInventory, "/postinventory")
api.add_resource(UpsertInventory, "/upsertinventory")

if __name__ == "__main__":
    app.run(port=80, debug=True)
