import requests
import json


class Requesters:

    def get(self, url, headers={}, payload={}):
        try:
            return requests.request("GET", url, headers=headers, data=payload)
        except:
            return {"status_code": 410, "errorMsg": "Failed to fetch data"}

    def head(self, url, payload={}, headers={}):
        try:
            return requests.request("HEAD", url, headers=headers, data=payload)
        except:
            return {"status_code": 410, "errorMsg": "Failed to fetch data"}

    def post(self, url, headers={}, payload={}):
        if(type(payload)!=str):
            payload = json.dumps(payload)
        try:
            return requests.request(
                "POST", url, headers=headers, data=payload
            )
        except:
            return {"status_code": 410, "errorMsg": "Failed to fetch data"}
