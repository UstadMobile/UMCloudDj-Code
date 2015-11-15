'''
Created on Nov 9, 2015

@author: mike
'''
import zipfile
import tempfile
import os
import os.path
import shutil
import sys 

try:
    from PIL import Image
except:
    import Image
    

class EPUBResizer(object):
    '''
    classdocs
    '''
    
    IMAGE_EXTENSIONS = [".jpg", ".png", ".jpeg"]


    def __init__(self, src):
        '''
        Constructor
        '''
        self.src = src
        
        
    
    def resize(self, dst, max_width = -1, max_height = -1):
        '''
        Resize the src epub into a dst epub with the given
        max_width
        max_height
        '''
        
        input_zip = zipfile.ZipFile(self.src, "r")
        tmp_dir = tempfile.mkdtemp(prefix = "epubresizer")
        input_zip.extractall(tmp_dir)
        input_zip.close()
        
        for root, dirs, files in os.walk(tmp_dir, topdown = False):
            for name in files:
                filename, file_extension = os.path.splitext(name)
                if file_extension in EPUBResizer.IMAGE_EXTENSIONS:
                    img_abs_path = os.path.join(root, name) 
                    
                    try:
                        img = Image.open(img_abs_path)
                        scale_x = 1
                        scale_y = 1
                        
                        if max_width != -1 and img.size[0] > max_width:
                            scale_x = float(max_width) / float(img.size[0])
                            
                        if max_height != -1 and img.size[1] > max_height:
                            scale_y = float(max_height) / float(img.size[1])
                         
                        scale_fit = min(scale_x, scale_y)
                        if scale_fit != 1:
                            #needs resized
                            new_size = (int(img.size[0] * scale_fit),int(img.size[1] * scale_fit))
                            new_img = img.resize(new_size, Image.ANTIALIAS)
                            new_img.save(img_abs_path) 
                    except:
                        traceback = sys.exc_info()[2]
                        print "Unexpected error:", sys.exc_info()[0]
                        from traceback import print_tb
                        print_tb(traceback)
        
        dst_zip = zipfile.ZipFile(dst, "w")
        for root, subdirs, files in os.walk(tmp_dir):
            for filename in files:
                src_path = os.path.join(root, filename)
                archive_path = os.path.relpath(src_path, tmp_dir)
                dst_zip.write(src_path, archive_path, zipfile.ZIP_DEFLATED)
                print archive_path
            
            
        dst_zip.close()
        
        shutil.rmtree(tmp_dir)
    
    
    
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Resize EPUB assets")
    parser.add_argument("--src")
    parser.add_argument("--dst")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)

    args = parser.parse_args()
    all_args, leftovers = parser.parse_known_args()
    if all_args.src is None or all_args.dst is None \
        or all_args.width is None or all_args.height is None:
            print("Parameter is not mentioned. Use this usage: ")
            print("<> --src /path/to/source.epub --dst /path/to/dest.epub --width 42 --height 42")
            exit (1)
    print("Staring epub resize..");
    resizer = EPUBResizer(args.src)
    resizer.resize(args.dst, max_width = args.width, max_height = args.height)
    print "Resized epub written to %s" % args.dst


