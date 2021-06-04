import requests
from dotenv import load_dotenv
from os import getenv

load_dotenv()
TOKEN = getenv("TOKEN")

for i in range(5):
    request = requests.get("https://pixels.pythondiscord.com/get_pixels", headers={"Authorization": f"Bearer {TOKEN}"})
    print(request.headers)
