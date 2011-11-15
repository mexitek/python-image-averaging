#!/usr/bin/python

__author__ = "Arlo Carreon <http://arlocarreon.com>"


# Purpose: 
#  generate an "average" image from local directory



import sys
import os
import re
import math
import Image
import time

# Type of extensions you are willing to accept
ext = "JPG|jpeg|jpg|png"
# Base path for source images and average destination
source_path = "./source/"
average_path = "./average/"


# Function grabs all images in a folder
def get_photos_from_directory( path ):
	listing = os.listdir(path)
	images = []
	regex_str = '.*\.['+ext+']'
	print "Looking for matching files: "+regex_str
	for infile in listing:
		if re.match( regex_str, infile, re.I|re.X ):
			images.append(infile)
	return images

def resize(im, screen, standard_area):
    
    (screen_width, screen_height) = screen
    (width, height) = im.size
    
    # resize here to all occupy about the same area on screen.
    area = width * height
    factor = math.sqrt( standard_area * 1.0 / area )
    width *= factor
    height *= factor
        
    # but stay within the maximum screen.
    if width > screen_width or height > screen_height:
        # landscape
        if width > height:   
            width = screen_width
            height *= screen_width / width
        # portrait
        else:       
            width *= screen_height / height
            height = screen_height
    
    width = int(width)
    height = int(height)
    
    return im.resize((width,height), Image.BICUBIC)


def create_average(screen, photos):
    
    debug("starting")

    # some geometry
    (screen_width, screen_height) = screen
    center_x = screen_width / 2;
    center_y = screen_height / 2;

    # we will resize all photos to have an area around this.
    phi = (1 + math.sqrt(5)) / 2
    standard_area = screen_width * (screen_width/phi)
    

    # prototype black screen all images get pasted onto. 
    black = Image.new("RGB", screen, "black")
    average = black.copy()

    
    for i in range(len(photos)):

        debug("processing >> %s" % photos[i])
        
        try:
            im = load_image(photos[i]);
        except: 
            debug("Bad Image? Script no likie.")
            continue
        
        im = resize(im, screen, standard_area);
        
        # paste photo in the center of a black screen. 
        (im_width, im_height) = im.size
        offset_x = center_x - im_width / 2;
        offset_y = center_y - im_height / 2;
       
        im_frame = black.copy()
        im_frame.paste(im, (offset_x,offset_y))
        
        # and blend this with our average 
        alpha = 1.0/(i+1)  # <-- clever part. Get average in constant memory.
                           # perhaps too clever. 
                           # images where most of the detail is just squished into one or two
                           # bits of depth. This may account for the slow darkening (?)
                           # may be better to combine images in a tree
        average = Image.blend(average, im_frame, alpha);

        # is this necessary? jclark had it.
        del im

    return average
        

def load_image(photo):
    im = Image.open(source_path+photo)
    return im
    

def debug(msg):
    sys.stderr.write(msg + "\n")

def main(*argv):
    from getopt import getopt, GetoptError

    try:
        (opts, args) = getopt(argv[1:], 'p:w:h:f:n:u', ['page', 'width', 'height', 'file', 'number','unique'])
    except GetoptError, e:
        print e
        print __doc__
        return 1

    file = average_path + str(time.time()) + '.jpg'
    width = 500
    height = 500
    n = 100
    unique_owners = False
    start_page = 0 
   
    for o, a in opts:
        if o in ('-w', '--width'):
            width = int(a)
        elif o in ('-h', '--height'):
            height = int(a)
        elif o in ('-f', '--file'):
            file = a
        elif o in ('-n', '--number'):
            n = int(a)
        elif o in ('-u', '--unique'):
           unique_owners = True
        elif o in ('-p', '--page'):
           start_page = int(a)
        else:
            print "Unknown argument: %s" % o
            print __doc__
            return 1

    # Set the screen
    screen = (width, height)


    photos = get_photos_from_directory(source_path)
    average = create_average(screen, photos)
    average.save(file)

if __name__ == '__main__':
    sys.exit(main(*sys.argv))