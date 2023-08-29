#!/usr/bin/env python
import sys
import os
import subprocess
import shutil
import glob

from PIL import Image, ImageOps
from fontTools.ttLib import TTFont

# takes ttfs from the source directory and turns them into pngs in the dst_dir
# returns the number of ttfs processed
def convert_ttf(src_dir, dst_dir, force=False, verbose=False):
    DST_DIR = os.path.join(os.getcwd(), dst_dir)
    TEXTS_DIR = os.path.join(DST_DIR, "texts")
    IMAGES_DIR = os.path.join(DST_DIR, "images")
    SRC_DIR = os.path.join(os.getcwd(), src_dir)
    FONT_SIZE = "28"
    
    num_ttfs = len([name for name in os.listdir(SRC_DIR) if name.endswith(".ttf") or name.endswith(".otf")])
    
    # Remove output directories if it exist
    if os.path.exists(DST_DIR):
        if not force:
            num_pngs = len([name for name in os.listdir(DST_DIR) if name.endswith(".png")])
            if num_pngs == num_ttfs * 52:
                print("Images already processed. Exiting conversion")
                return num_ttfs
        shutil.rmtree(DST_DIR)
    os.makedirs(DST_DIR)
    os.makedirs(TEXTS_DIR)
    os.makedirs(IMAGES_DIR)
    #TODO remove dir only if non-full
    
    thumb_width = int(FONT_SIZE)
    # goes through each ttf file
    for file in os.listdir(SRC_DIR):
        if not (file.endswith(".ttf") or file.endswith(".otf")):
            print("Ignored", file)
            continue
        TTF_PATH = os.path.join(SRC_DIR, file)
        TTF_NAME, TTF_EXT = os.path.splitext(os.path.basename(TTF_PATH))
        ttf = TTFont(TTF_PATH)
        # Make temporary directories
        # Writing each individual font character to file as texts
        x = ttf["cmap"].tables[0]
        # for x in ttf["cmap"].tables:
        for y in x.cmap.items():
            char_unicode = chr(y[0])
            char_utf8 = char_unicode.encode('utf_8')
            char_name = y[1]
            if len(char_name) == 1:
                # write each character to a new txt file
                if (char_name >= 'a' and char_name <= 'z') or (char_name >= 'A' and char_name <= 'Z'):
                    upper = char_name.isupper()
                    case = '_upp' if upper else '_low'
                    f = open(os.path.join(TEXTS_DIR, char_name.lower() + case + '.txt'), 'wb')
                    f.write(char_utf8)
                    f.close()
        ttf.close()
        
        # Convert each txt file into a png
        files = os.listdir(TEXTS_DIR)
        for filename in files:
            name, ext = os.path.splitext(filename)
            input_txt = os.path.join(TEXTS_DIR, filename)
            output_png = os.path.join(IMAGES_DIR, TTF_NAME + "_" + name + ".png")
            subprocess.call(["convert", "-font", TTF_PATH, "-pointsize", FONT_SIZE, "label:@" + input_txt, output_png])
        
        # clear out the text directory since we are done with it
        shutil.rmtree(TEXTS_DIR)
        os.makedirs(TEXTS_DIR)

        # Normalizing the images to all be of the correct size
        files = glob.glob(os.path.join(IMAGES_DIR, '*.png'))
        for f in files:
            im = Image.open(f).convert('RGB')
            im = ImageOps.invert(im)
            im_thumb = im.resize((thumb_width, thumb_width), Image.LANCZOS)
            ftitle, fext = os.path.splitext(os.path.basename(f))
            im_thumb.save(os.path.join(DST_DIR, ftitle + fext))

        # done with the image directory
        shutil.rmtree(IMAGES_DIR)
        os.makedirs(IMAGES_DIR)
        if verbose:
          print("Processed", file)
    shutil.rmtree(TEXTS_DIR)
    shutil.rmtree(IMAGES_DIR)
    return num_ttfs