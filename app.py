from typing import Tuple
import requests
from PIL import Image, ImageTk
import tkinter as tk
from tkinter.colorchooser import askcolor
import asyncio
import logging
import math
import time
from dotenv import load_dotenv
from os import getenv
from tqdm import tqdm

load_dotenv()
UPSCALE_FACTOR = int(getenv("UPSCALE_FACTOR"))
TOKEN = getenv("TOKEN")
logging.basicConfig(level=logging.INFO)

def getSize() -> Tuple[int, int]:
    """Get the size of the Pixels canvas"""
    request = requests.get("https://pixels.pythondiscord.com/get_size")
    request.raise_for_status()
    return (request.json()["width"], request.json()["height"])

async def getCanvas() -> Image.Image:
    """Get the canvas as a PIL Image"""
    request = requests.get("https://pixels.pythondiscord.com/get_pixels", headers={"Authorization": f"Bearer {TOKEN}"})
    if "cooldown-reset" in request.headers:
        logging.warning("Waiting %ss", request.headers["cooldown-reset"])
        for i in tqdm(range(int(request.headers["cooldown-reset"]))):
            await asyncio.sleep(1)
        return await getCanvas()
    else:
        logging.info("%s/%s get canvas requests used. This limit will reset in %ss", int(request.headers["requests-limit"]) - int(request.headers["requests-remaining"]), request.headers["requests-limit"], request.headers["requests-reset"])
    request.raise_for_status()
    size = getSize()
    data = request.content
    canvas = Image.frombytes("RGB", size, data)
    return canvas

async def setPixel(x: int, y: int, color: str):
    """set a pixel no duh"""
    request = requests.post("https://pixels.pythondiscord.com/set_pixel", headers={"Authorization": f"Bearer {TOKEN}"}, json={"x": x, "y": y, "rgb": color})
    logging.debug(request.json())
    if "cooldown-reset" in request.headers:
        logging.warning("Waiting %ss", request.headers["cooldown-reset"])
        for i in tqdm(range(int(request.headers["cooldown-reset"]))):
            await asyncio.sleep(1)
        return asyncio.run(setPixel(x, y, color))
    else:
        logging.info("%s/%s set pixel requests used. This limit will reset in %ss", int(request.headers["requests-limit"]) - int(request.headers["requests-remaining"]), request.headers["requests-limit"], request.headers["requests-reset"])
    

def canvasToTk(canvas: Image.Image):
    """Turn a canvas into Tk compatible"""
    size = getSize()
    tkImage = ImageTk.PhotoImage(canvas.resize((size[0] * UPSCALE_FACTOR, size[1] * UPSCALE_FACTOR), Image.NEAREST))
    return tkImage



window = tk.Tk()

canvas = asyncio.run(getCanvas())
tkCanvas = canvasToTk(canvas)
label = tk.Label(image=tkCanvas, background="black")


def click(event: tk.Event):
    global canvas, tkCanvas
    x = event.x
    y = event.y
    imageX = math.floor(x / UPSCALE_FACTOR)
    imageY = math.floor(y / UPSCALE_FACTOR)
    pixelColor = canvas.getpixel((imageX, imageY))
    logging.info("Click at (%s, %s) on the image, at the color %s", imageX, imageY, pixelColor)
    newColor = askcolor(pixelColor)
    asyncio.run(setPixel(imageX, imageY, newColor[1].replace("#", "", 1).upper()))
    canvas = asyncio.run(getCanvas())
    tkCanvas = canvasToTk(canvas)
    label["image"] = tkCanvas

label.grid(row=0, column=0)
label.bind("<Button-1>", click)

def updateImage():
    global canvas, tkCanvas
    canvas = asyncio.run(getCanvas())
    tkCanvas = canvasToTk(canvas)
    label["image"] = tkCanvas
    window.after(11000, updateImage)

updateImage()
window.mainloop()
