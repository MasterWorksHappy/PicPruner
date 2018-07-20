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

def setup_dirs():
    for k, dn in config["dirs"].items():
        dnp = Path(dn)
        dnp.mkdir(exist_ok=True)

def hash_dir(dn=None):
    # hash the dir
    for fn in glob.glob("{}/**/*.jp*".format(Path(dn)), recursive=True):
        fn_hash = hashlib.md5(open(fn, 'rb').read()).hexdigest()
        if fn_hash in ph.md5:
            # retrieve the list of hash pics and append fn
            phr = ph.md5[fn_hash]
            if fn not in phr.dups_list:
                phr.dups_list.append(fn)
                # print("new file: {}".format(fn))
        else:
            # first pass
            phr = Pics_Hash_Rec()
            phr.dups_list.append(fn)
            phr.copied = False
            phr.mo, phr.yr = get_yr_mo(fn)
            ph.md5.setdefault(fn_hash, phr)

    pic_tot = sum(len(v.dups_list) for v in ph.md5.values())
    print("{} unique out of {} pictures".format(len(ph.md5), pic_tot))


def copy_pics():
    for hash, phr in ph.md5.items():
        for idx, fn in enumerate(phr.dups_list):
            if idx == 0:
                # copy only the first pic to good dir
                copy_pic(fn=fn, phr=phr, dest_dir=config["dirs"]["save"])
            else:
                # copy extra pics to duplicates dir
                copy_pic(fn=fn, phr=phr, dest_dir=config["dirs"]["dups"])


def copy_pic(fn=None, phr=None, dest_dir=None):
    fn_dest_dir = get_dest_dir(dn=dest_dir, fn=fn, mo=phr.mo, yr=phr.yr)
    fn_dest = fn_dest_dir / PurePath(fn).name
    if fn_dest.exists():
        # already in the save dir, check the duplicates dir
        fn_dest_dups_dir = get_dest_dir(dn=config["dirs"]["dups"], fn=fn, mo=phr.mo, yr=phr.yr)
        fn_dest = fn_dest_dups_dir / PurePath(fn).name
        if fn_dest.exists():
            # already in the duplicates dir, try jerry-rigging the fn
            new_dest = "_".join(PurePath(fn).parts)[4:]
            fn_dest = fn_dest_dups_dir / new_dest
    copy2(fn, fn_dest)


def get_dest_dir(dn=None, fn=None, mo=None, yr=None):
    fn_yr = dn / yr
    fn_yr.mkdir(exist_ok=True)
    fn_mo = dn / yr / mo
    fn_mo.mkdir(exist_ok=True)
    return fn_mo


def get_yr_mo(fn):

    def get_pic_yr_mo(f=None):
        try:
            img = Image.open(f)
            if img:
                if img.format not in ['png', 'PNG']:
                    img = img._getexif()
                    if img:
                        pic_dict = {TAGS.get(k, k) : v for k, v in img.items()}
                        dt_val = pic_dict.get('DateTime', None)
                        if dt_val:
                            yr, mo, rest = dt_val.split(':', 2)
                            return yr, mo
        except:
            print('Skipping unreadable image {}'.format(f))
        return None, None

    # print( "Processing {}".format(fn))
    fn_yr, fn_mo = get_pic_yr_mo(f=fn)
    if not fn_mo:
        # if no pic yr & mo then get file yr & mo
        fn_yr = datetime.fromtimestamp(os.path.getmtime(fn)).strftime("%Y")
        fn_mo = datetime.fromtimestamp(os.path.getmtime(fn)).strftime("%m")
    return fn_mo, fn_yr



if __name__ == '__main__':
    scan_dir = r"C:\Users\Maste\_My Stuff\Pictures"
        # r"C:\Users\Maste\_My Stuff\Pictures\_from NAS\Photos\2006\2006 - Pets - Copy"
    setup_dirs()
    hash_dir(dn=scan_dir)
    copy_pics()
    dups = config["dirs"]["dups"]
    print("Found {} files in {}".format(len(list(Path(dups).rglob('*.*'))), dups))
    save = config["dirs"]["save"]
    print("Found {} files in {}".format(len(list(Path(save).rglob('*.*'))), save))
