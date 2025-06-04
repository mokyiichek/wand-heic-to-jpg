import os
from wand.image import Image

findfile = '.HEIC'
basepaths = ['/user/folder1/images', '/user/folder2/images']
skipdirs  = ['.sync', '.git', '__pycache__']


def check_dir(path, file, level=0):
    # convert HEIC files in the current directory
    for entry_file in os.listdir(path):
        file_path = os.path.join(path, entry_file)
        if os.path.isfile(file_path) and entry_file.endswith(file):
            print("  "*level, "-", entry_file)

            file_source = file_path
            file_target = os.path.join(path, entry_file.replace(".HEIC", ".JPG"))

            if os.path.isfile(file_target) and os.path.getsize(file_target) > 0:
                print("  "*level, " ", "JPG file exists, skipped")

            else:
                print("  "*level, " ", "converting...")

                try:
                    img = Image(filename=file_source)
                    img.format = 'jpg'
                    img.save(filename=file_target)
                    img.close()
                    print("  "*level, " ", f"saved to {file_target}")
                except Exception:
                    print("  "*level, " ", "HEIC file error, skipped")

    # process subdirectories
    for entry_path in os.listdir(path):
        dir_path = os.path.join(path, entry_path)
        if os.path.isdir(dir_path):
            print("  "*level, "+", entry_path)

            if not entry_path in skipdirs:
                # check directory recursively
                check_dir(dir_path, file, level+1)


for basepath in basepaths:
    check_dir(basepath, findfile)
