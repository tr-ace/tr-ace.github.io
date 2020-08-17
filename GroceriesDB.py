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
