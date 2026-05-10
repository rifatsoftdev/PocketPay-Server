import json

from app.constants.string import String



data = {
    "ignor": [
        String.INVALID_PASSWORD,
        String.INVALID_OTP
    ]
}


def config():
    return json.dumps(data, indent=4)




# if __name__ == "__main__":
#     print(config())

