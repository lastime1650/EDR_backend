import pickle

import requests, json


'''data = {
    "NAME": "test",
    "MODEL_TYPE": "chatgpt",
    "METADATA": {
        "model": "gpt-4o-mini",
        "temperature": "0.7",
        "openai_api_key": "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"
    }
}
url = "http://127.0.0.1:4060/api/LLM_Register"

r = requests.get(url, params={"input_JSON": json.dumps(data) }).text
print(r)


data ={
    "NAME": "test"
}
url = "http://127.0.0.1:4060/api/LLM_Remove"

r = requests.get(url, params={"input_JSON": json.dumps(data) }).text
print(r)'''

'''url = "http://192.168.0.1:4060/api/LLM_QUESTION"
data = {
    "question_id": "123",
    "instance_id": "904af439be31e1501899237b7addb1d0a1d2db32ecd4872d807d7600d7d3cac8",
    "question": "그러면 이거는 무시할 까? "
}
print(
    requests.get(url,params={"input_JSON": json.dumps(data)}).text
)'''
