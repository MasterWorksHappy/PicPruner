from pathlib import Path, PurePath
import hashlib
import glob
import os
from datetime import datetime
from shutil import copy2
from PIL import Image
from PIL.ExifTags import TAGS
from pic_pruner.pics_hash import Pics_Hash
from pic_pruner.pics_hash_rec import Pics_Hash_Rec

ph = Pics_Hash()
config = {
    "dirs": {
        "base": Path(r"C:\Users\Maste\_PICS"),
        "save": Path(r"C:\Users\Maste\_PICS\1807 Organized Pics"),
        "dups": Path(r"C:\Users\Maste\_PICS\1807 Duplicate Pics")
    }
}
hash_result_dir = []

def hash_maker(dn=None):
    # hash the dir
    # for fn in glob.glob("{}/**/*.*".format(Path(dn)), recursive=True):
    #     hash_result_dir.append(hashlib.md5(open(fn, 'rb').read()).hexdigest())
    fnames = [fn for fn in glob.glob("{}/**/*.*".format(Path(dn)), recursive=True)]
    hash_result_dir = [hashlib.md5(open(fn, 'rb').read()).hexdigest() for fn in fnames]
    # hash_result_dir = [hashlib.md5(open(fn, 'rb').read()).hexdigest() for fn in glob.glob("{}/**/*.*".format(Path(dn)), recursive=True)]
    print("LEN HASH RESULT fnames: {}".format( len(fnames)))
    print("LEN HASH RESULT DIR: {}".format( len(hash_result_dir)))


def hash_checker(dn=None):
    # hash the dir
    for fn in glob.glob("{}/**/*.jp*".format(Path(dn)), recursive=True):
        fn_hash = hashlib.md5(open(fn, 'rb').read()).hexdigest()
        if fn_hash not in hash_result_dir:
            print("{}: {} missing.".format(fn_hash, fn))



if __name__ == '__main__':

    # find each hashed_file in the dest_dir_hash_list
    save_dir = r"C:\Users\Maste\_PICS\1807 Organized Pics"
    hash_maker(dn=save_dir)
    tgt_dir = r"C:\Users\Maste\_My Stuff\Pictures"
    # hash_checker(dn=tgt_dir)

