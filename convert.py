import os
from wand.image import Image

findfile = '.HEIC'
basepaths = ['/user/folder1/images', '/user/folder2/images']
skipdirs  = ['.sync', '.git', '__pycache__']


def check_dir(path, file, level=0):

    for entry_path in os.listdir(path):
   
        if os.path.isdir(os.path.join(path, entry_path)):
            print("  "*level, "+", entry_path)

            if not entry_path in skipdirs:
                # check directory recursively 
                check_dir(os.path.join(path, entry_path), file, level+1)

            # find files in this directory
            for entry_file in os.listdir(os.path.join(path, entry_path)):
                if entry_file.endswith(file):
                    print("  "*(level+1), "-", entry_file)

                    file_source = os.path.join(path, entry_path) + "/" + entry_file
                    file_target = os.path.join(path, entry_path) + "/" + entry_file.replace(".HEIC", ".JPG")

                    if os.path.isfile(file_target) and os.path.getsize(file_target) > 0:
                        print("  "*(level+1), " ", "JPG file exists, skipped")

                    else:
                        print("  "*(level+1), " ", "converting...")

                        try:
                            img = Image(filename=file_source)
                            img.format = 'jpg'
                            img.save(filename=file_target)
                            img.close()
                            print("  "*(level+1), " ", f"saved to {file_target}")
                        except:
                            print("  "*(level+1), " ", "HEIC file error, skipped")


for basepath in basepaths:
    check_dir(basepath, findfile)
