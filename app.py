from typing import Tuple
import requests
from PIL import Image, ImageTk
import tkinter as tk
from tkinter.colorchooser import askcolor
from tkinter.ttk import Progressbar
import logging
import threading
import math
import time
from dotenv import load_dotenv
from os import getenv, write
from tqdm import tqdm

#Get your API key at https://pixels.pythondiscord.com/authorize
writeQueue = []

load_dotenv()
UPSCALE_FACTOR = int(getenv("UPSCALE_FACTOR"))
TOKEN = getenv("TOKEN")
logging.basicConfig(level=logging.INFO)

def getSize() -> Tuple[int, int]:
    """Get the size of the Pixels canvas"""
    request = requests.get("https://pixels.pythondiscord.com/get_size")
    logging.debug(request.json())
    request.raise_for_status()
    return (request.json()["width"], request.json()["height"])

def getCanvas() -> Image.Image:
    """Get the canvas as a PIL Image"""
    request = requests.get("https://pixels.pythondiscord.com/get_pixels", headers={"Authorization": f"Bearer {TOKEN}"})
    try:
        if request.json()["message"] == "Endpoint unavailable":
            logging.info("Get canvas endpoint is currently down.")
            return Image.new("RGB", (getSize()[0] * UPSCALE_FACTOR, getSize()[1] * UPSCALE_FACTOR)), 10000
    except:
        pass
    request.raise_for_status()
    logging.info("%s/%s get canvas requests used. This limit will reset in %ss", int(request.headers["requests-limit"]) - int(request.headers["requests-remaining"]), request.headers["requests-limit"], request.headers["requests-reset"])
    request.raise_for_status()
    size = getSize()
    data = request.content
    canvas = Image.frombytes("RGB", size, data)
    return canvas

def setPixel(x: int, y: int, color: str):
    """set a pixel no duh"""
    request = requests.post("https://pixels.pythondiscord.com/set_pixel", headers={"Authorization": f"Bearer {TOKEN}"}, json={"x": x, "y": y, "rgb": color})
    logging.debug(request.json())
    logging.info("%s/%s set pixel requests used. This limit will reset in %ss", int(request.headers["requests-limit"]) - int(request.headers["requests-remaining"]), request.headers["requests-limit"], request.headers["requests-reset"])
    if request.status_code == 200:
        return True
    else:
        return request.status_code

def canvasToTk(canvas: Image.Image):
    """Turn a canvas into Tk compatible"""
    size = getSize()
    tkImage = ImageTk.PhotoImage(canvas.resize((size[0] * UPSCALE_FACTOR, size[1] * UPSCALE_FACTOR), Image.NEAREST))
    return tkImage



window = tk.Tk()
window.geometry(f"{getSize()[0] * UPSCALE_FACTOR}x{getSize()[1] * UPSCALE_FACTOR + 10}")

canvas = getCanvas()
tkCanvas = canvasToTk(canvas)
label = tk.Label(image=tkCanvas, background="black")

def addToQueue(x, y, color):
    global writeQueue
    writeQueue.append({"x": x, "y": y, "color": color})

def click(event: tk.Event):
    global canvas, tkCanvas
    x = event.x
    y = event.y
    imageX = math.floor(x / UPSCALE_FACTOR)
    imageY = math.floor(y / UPSCALE_FACTOR)
    pixelColor = canvas.getpixel((imageX, imageY))
    logging.debug("Click at (%s, %s) on the image, at the color %s", imageX, imageY, pixelColor)
    newColor = askcolor(pixelColor)
    logging.info("Requested pixel at coords: (%s, %s), color: %s", x, y, newColor)
    if newColor == None:
        return
    addToQueue(imageX, imageY, newColor[1].replace("#", "", 1).upper())

label.grid(row=0, column=0)
label.bind("<Button-1>", click)

progressBar = Progressbar()
progressBar.grid(column=0, row=1)


def updateQueueLoop():
    global canvas, tkCanvas, progressBar, writeQueue
    for i in writeQueue:
        timeLeft = requests.head("https://pixels.pythondiscord.com/set_pixel", headers={"Authorization": f"Bearer {TOKEN}"})
        try:
            if int(timeLeft.headers["Requests-Remaining"]) > 1:
                #run the process
                success = setPixel(i["x"], i["y"], i["color"])
                if success == True:
                    writeQueue.remove(i)
                else:
                    logging.warn("Set Pixel request x: %s, y: %s, color: %s, failed.", i["x"], i["y"], i["color"])
            else:
                break
        except:
            pass
    window.after(1000, updateQueueLoop)




def updateImage():
    global canvas, tkCanvas
    canvas = getCanvas()
    tkCanvas = canvasToTk(canvas)
    label["image"] = tkCanvas



def updateImageLoop():
    timeLeft = requests.head("https://pixels.pythondiscord.com/get_pixels", headers={"Authorization": f"Bearer {TOKEN}"})
    try:
        if timeLeft.headers["requests-reset"] == 0 and int(timeLeft.headers["requests-remaining"]) < 3:
            #run the process
            try:
                updateImage()
            except:
                logging.warn("Get Pixels request failed.")

    except:
        pass
    window.after(1000, updateImageLoop)

updateQueueLoop()
updateImageLoop()

window.mainloop()
