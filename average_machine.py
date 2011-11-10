#!/usr/bin/python
"""Usage: python average.py [OPTIONS] TAGS
TAGS is a space delimited list of tags

OPTIONS:
  -w screenwidth or --width   screenwidth
  -h screenheight or --height screenheight
  -f filename or --file       filename
  -n photos or --number       photos
  -u or --unique              unique users
  -p or --page                start collection at search page idx 
                                 0 = first page

Requires:
 - Python Imaging Library [http://www.pythonware.com/products/pil/]
 - Python >= 2.2

"""

# THIS SOFTWARE IS SUPPLIED WITHOUT WARRANTY OF ANY KIND, AND MAY BE
# COPIED, MODIFIED OR DISTRIBUTED IN ANY WAY, AS LONG AS THIS NOTICE
# AND ACKNOWLEDGEMENT OF AUTHORSHIP REMAIN.

__author__ = "Neil Kandalgaonkar <neilk(a)brevity.org>"


# Purpose: 
#  generate an "average" image from Flickr based on tags.
# 
# This may have to be completely rewritten. It's very buggy and has fits and starts,
# not to mention Flickr's occasional slowness. There is a problem with the image
# slowly converging on blackness.
# 
# We should really cache the images on disk (and the search results)
# and then have at them.



import sys
import urllib
import math
import Image
import flickr
import time

from flickr import FlickrError


# we want to get N photos that match the tag.
def get_photos_for_tags(tags, number=50, unique_owners=False, start_page=0):

    photos = []
    seen_owner = {}
    page = start_page
    need_more = True
    
    
    debug("starting to get photos...")
    
    while (need_more):
        page += 1
    
        debug("page %s of photo search" % page)
            
        for p in flickr.photos_search(tags=tags, tag_mode='all', page=page):
            debug ("photo id %s" % p.id)
            
            if unique_owners:
                
                # silly thing is unicode, although just a number.
                uid = p.owner.id.encode('ascii') 
                debug ("   photo has uid %s" % uid)

                if seen_owner.has_key(uid): continue
                seen_owner[uid] = 1
            
            photos.append(p)
            if (len(photos) == number):
                need_more = False
                break
        
    return photos



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

        debug("doing photo id %s" % photos[i].id)
        
        try:
            im = load_image(photos[i]);
        except FlickrError: 
            debug("FlickrError")
            continue
                
        im.save("orig/%03d.jpg" % i)
        
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
        
        if not (i % 10):
            average.save('progress-%03d.jpg' % i)

        # is this necessary? jclark had it.
        del im
        
        time.sleep(2) # be nice to their server

    return average
        

def load_image(photo):
    url = photo.getURL(size='Medium', urlType='source')
    file, mime = urllib.urlretrieve(url)
    im = Image.open(file)
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

    file = 'average.jpg'
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
        
    if len(args) == 0:
        print "You must specify at least one tag"
        print __doc__
        return 1
    
    tags = [item for item in args]
    
    screen = (width, height)


    photos = get_photos_for_tags(tags, n, unique_owners, start_page)
    average = create_average(screen, photos)
    average.save(file)

if __name__ == '__main__':
    sys.exit(main(*sys.argv))
