## Edward Menser's ePortfolio

Welcome to my ePortfolio! Below you will be able to view my enhancements to locategroceries.com. This is a website I started in the midst of the ongoing COVID-19 pandemic to help people find groceries in their local areas. 

### Professional Self-Assessment

Completing my coursework throughout this capstone has challenged me signficiantly to improve the readability and functionality of my code. It has also showcased my strengths in overcoming problems that arise. The clever idea to "crowdsource" grocery stocking levels inspired this project, but my determination to learn React and help others brought the idea to fruition. 

The data structures and algorithms used in this project are some of the best I've developed. Managing the front-end, back-end, and everything in between has been a proud moment for me in the success of this website. While I was the only developer of this project, I had much input from friends and family. This represents my willingness to communicate and improve based on feedback.

The database artificat presented below informs the portfolio on my ability to work with APIs, and my understanding of CRUD applications. These can be complicated topics, but are foundational to web development. My wide range of knowledge with web development will allow me to successfully complete many projects in the future, whether solo or with a team.

### Code Review

My code review of the initial walkthrough of the codebase can be viewed [here](http://locategroceries.com/static/code_review.rar) (due to the size of the video file, it's been uploaded to AWS S3).

### Database Enhacement

This artifact is the REST API file that is used to interact with the MongoDB database for the website. This API performs all CRUD (Create, Read, Update, Delete) operations to the database. The other artifact is the GroceriesDB Python class that acts as a wrapper for the API. These files were created back in April of this year.

I included these items in my ePortfolio, because they demonstrate the CRUD operations, which are crucial to web development. These artifacts both prove my competence and skills in software development by demonstrating use of algorithms, data structures, and best practices. These artifacts were improved by renaming modules to be more readable, returning dictionary/JSON values, and increasing documentation.

Many of the challenges I faced with this portion were updating the inventory of a specific item. In the beginning, I faced an issue where the entire document would be inserted and updated causing a recursive loop. This was the biggest challenge to overcome, but necessary, because it would have been detrimental to the production version of the website.

The REST.py API contents can be viewed here: ''''
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

''''

The GroceriesDB.py class file can be viewed here: '''
#!/usr/bin/python
from pymongo import MongoClient
import pymongo
import requests
from datetime import datetime
import time
from collections import Counter

try:
    conn = MongoClient("localhost", 27017)
except:
    exit("Failed to conenct to DB")
db = conn.groceries


class GroceriesDB():
    def __init__(self):
        try:
            conn = MongoClient("localhost", 27017)
        except:
            exit("Failed to conenct to DB")
        self.db = conn.groceries
        self.api_key = "REMOVED"

    def get_nearby_stores(self, lng=-86.5959936, lat=30.405427199999995,  radius=2000):

        api_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?keyword=(mart) OR (grocery)&location={lat},{lng}&radius={radius}&key={api_key}"

        results = []

        url = api_url.format(
            lat=lat, lng=lng, radius=radius, api_key=self.api_key)
        r = requests.get(url)
        data = r.json()

        try:
            results = data["results"]
            return results

            # FIXME - get all page results
            cur_data = data
            max_gets = 4
            cur_gets = 1
            while "next_page_token" in cur_data.keys():
                if cur_gets > max_gets:
                    break
                next_url = "{0}&next_page_token={1}".format(
                    url, cur_data["next_page_token"])
                next_r = requests.get(next_url)
                next_data = next_r.json()
                for new_result in next_data["results"]:
                    if new_result not in results:
                        results.append(new_result)
                cur_data = next_data
                cur_gets += 1

            return results
        except:
            return []

    def get_single_store(self, place_id):
        return self.db.stores.find_one({"_id": place_id})

    def get_stores_inventory(self, stores):
        results = []
        for store in stores:
            place_id = store["place_id"]
            store_inventory = self.db.stores.find_one({"_id": place_id})
            store_copy = store
            if store_inventory:
                store_copy["inventory"] = store_inventory["inventory"]
            else:
                store_copy["inventory"] = {}
            results.append(store_copy)
        return results

    def update_inventory(self, data):
        dk = data.keys()
        if "store" not in dk or "inventory" not in dk or "timestamp" not in dk:
            return {"pass": False, "message": "Missing needed keys. Keys provided: {0}".format(data.keys())}

        if "place_id" not in data["store"].keys():
            return {"pass": False, "message": "Missing place_id"}

        place_id = data["store"]["place_id"]

        if db.stores.count_documents({"_id": place_id}, limit=1) != 0:
            # Existing store record
            try:

                doc = db.stores.find_one({"_id": place_id})
                doc["store"] = data["store"]

                inv_cats = doc["inventory"].keys()
                data_cats = data["inventory"].keys()
                # Beverages, Dairy, etc
                for d_cat in data_cats:
                    if d_cat in inv_cats:
                        #coffee/tea, etc
                        d_sub_cats = data["inventory"][d_cat].keys()

                        for d_sub_cat in d_sub_cats:
                            val = {"value": data["inventory"][d_cat][d_sub_cat], "timestamp": int(
                                data["timestamp"])}
                            if val["value"] == -1:
                                continue
                            doc["inventory"][d_cat][d_sub_cat].append(val)
                    else:
                        # Category like Beverages not exist
                        doc["inventory"][d_cat] = {}
                        d_sub_cats = data["inventory"][d_cat].keys()

                        for d_sub_cat in d_sub_cats:
                            val = {"value": data["inventory"][d_cat][d_sub_cat], "timestamp": int(
                                data["timestamp"])}
                            if val["value"] == -1:
                                continue
                            doc["inventory"][d_cat][d_sub_cat] = [val]

                # update the old record
                db.stores.replace_one({"_id": place_id}, doc, True)
            except Exception as e:
                return {"pass": False, "message": "ERROR: {0}".format(str(e))}

        else:
            # New store record
            record = {"_id": place_id, "store": data["store"], "inventory": {}}

            data_cats = data["inventory"].keys()
            for d_cat in data_cats:
                record["inventory"][d_cat] = {}
                d_sub_cats = data["inventory"][d_cat].keys()

                for d_sub_cat in d_sub_cats:
                    val = {"value": data["inventory"][d_cat][d_sub_cat], "timestamp": int(
                        data["timestamp"])}
                    if val["value"] == -1:
                        continue
                    record["inventory"][d_cat][d_sub_cat] = [val]

            # insert the new record
            db.stores.insert_one(record)

        return {"pass": True, "message": "Submitted"}

    def upsert_inventory(self, data):
        dk = data.keys()

        if "place_id" not in data.keys():
            return {"pass": False, "message": "Missing place_id"}

        place_id = data["place_id"]
        try:
            db.stores.update_one({"_id": place_id}, {
                                 "$set": data}, upsert=True)
            return {"pass": True, "message": "Submitted"}
        except Exception as e:
            return {"pass": Fail, "message": str(e)}

'''
