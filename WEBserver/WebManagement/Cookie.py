from typing import Optional, List

from fastapi import Request
from starlette.responses import  Response

class Cookie_Manager():
    def __init__(self):
        self.cookie_key = "EDR_COOKIE_KEY"
        self.cookie_session = {}

    def Check_Cookie(self, request: Request):
        if request.cookies.get(self.cookie_key):
            return True
        else:
            return False

    def Set_Cookie(self, response:Response):
        import datetime, hashlib, random
        from datetime import datetime, timedelta, timezone
        random_cookie_id = hashlib.sha256( (f"{datetime.now()}{random.Random().randint(15, 5346)}").encode() ).hexdigest()
        expires = datetime.now(timezone.utc) + timedelta(seconds=60*100)
        response.set_cookie(
            key=self.cookie_key,
            value=random_cookie_id,
            max_age=60*100, # 100분
            expires=expires,
        )

        self.cookie_session[random_cookie_id] = {
            "key": self.cookie_key,
            "value": random_cookie_id,
            "max_age": 60*100, # 분
        }

        return

    def Get_Cookie(self, request: Request)->Optional[str]:
        cookie_value = request.cookies.get(self.cookie_key)
        if cookie_value:
            return cookie_value
        else:
            return None