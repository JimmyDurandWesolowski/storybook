#!/usr/bin/env python3

"""
A program that generates storybook pages with Ollama and Stable Diffusion for the Inky Impression
"""

import argparse
import math
import pathlib
import requests
import subprocess
import tempfile
from PIL import Image, ImageDraw, ImageFont

GENERATION_INTERVAL = 1800 #seconds
DISPLAY_RESOLUTION = (448, 600)
TOTAL_LINES = 6
OLLAMA_API = 'http://localhost:11434/api/generate'
OLLAMA_MODEL = 'gemma:7b'
OLLAMA_PROMPT = '''Create text from the page of an illustrated children\'s fantasy book. 
This text should be around 20 words. If you desire, you can include a hero, monster, mythical 
creature or artifact. You can choose a random mood or theme. Be creative.'''.replace("\n", "")
SD_PROMPT = 'an illustration in a children\'s book for the following scene: '
SD_STEPS = 3
FONT_FILE = 'CormorantGaramond-Regular.ttf'
FONT_SIZE = 21

def get_story():
    r = requests.post(OLLAMA_API, timeout=600,
        json={
            'model': OLLAMA_MODEL,
            'prompt': OLLAMA_PROMPT,
            'stream':False
                      })
    data = r.json()
    return data['response'].lstrip()

# naive function to replace with newline next space after the offset
def replace_next_space_with_newline(text, offset):
    next_space = text.find(' ', offset)
    if next_space != -1:
        return text[:next_space] + '\n' + text[next_space + 1:]
    return text

# naive function to split text into TOTAL_LINES number of lines
def split_text(text):
    char_total = len(text)
    approx_line_len = math.ceil(char_total/TOTAL_LINES)
    for i in range(TOTAL_LINES):
        text = replace_next_space_with_newline(text,approx_line_len*(i+1))
    return text

def generate_page(args, page_idx):
    generated_text = get_story()
    print(f'text: {generated_text}')
    with tempfile.NamedTemporaryFile() as temp:
        subprocess.run(
            [
                args.sd_path,
                "--xl",
                "--turbo",
                "--rpi",
                "--models-path",
                args.sd_model,
                "--prompt",
                SD_PROMPT + f'"{generated_text}"',
                "--steps",
                f"{SD_STEPS}",
                "--output",
                temp.name,
            ],
            check=False,
        )
        generated_text = split_text(generated_text)
        canvas = Image.new(mode="RGB", size=DISPLAY_RESOLUTION, color="white")
        im2 = Image.open(temp.name)
    im2 = im2.resize((448,448))
    canvas.paste(im2)
    im3 = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(FONT_FILE, FONT_SIZE)
    im3.text((7, 450), generated_text, font=font, fill=(0, 0, 0))
    canvas.show()
    canvas.save(f'output-{page_idx}.png')
    canvas = canvas.rotate(90,expand=1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--onnxstream", "--onnxstream-path", required=True, type=pathlib.Path
    )
    parser.add_argument("--sd-path", required=True, type=pathlib.Path)
    parser.add_argument("--sd-model", required=True, type=pathlib.Path)
    args = parser.parse_args()
    _idx = 1
    while True:
        generate_page(args, _idx)
        _idx += 1

if __name__ == '__main__':
    main()
