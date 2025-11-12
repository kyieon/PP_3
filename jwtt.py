import jwt
import datetime

token = jwt.encode(
    {"test": "hello", "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=5)},
    "testsecret",
    algorithm="HS256"
)
print(token)