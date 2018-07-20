import hashlib
import logging
import pprint
from collections import OrderedDict

import ntpath
import os
import os.path

pp = pprint.PrettyPrinter(indent=4)

logger = logging.getLogger('dupDestroyer')


def log_msg(**kwargs):
    msg = "\n\t\t"
    for k, v in kwargs.iteritems():
        if isinstance(v, dict) or isinstance(v, list):
            v = "\n" + pp.pformat(v)
        msg += '%s: %s\n' % (k, v)
    return msg


def normalize_pics_root(fix_list, pics_root=None, appl_pics_root=None):
    paths = tuple()
    for path in fix_list:
        path = path.replace(pics_root + '\\', "")
        path = path.replace(appl_pics_root + '\\', "")
        paths = paths + (path,)
    return paths


class DataMinder(object):
    """
    Provides:
        create_entry(file_hash=file_hash, dir_name=dir_name, file_path=path)
        flash_entries()
        get_dirs_with_dups()
        get_files_bydir(dir_list=dir_list)
        del_by_list_of_files(files_to_move)
    """

    def __init__(self, search_dir=None, pics_root=None):
        self.short_parent_folder = search_dir.replace(pics_root + '\\', "")
        self.dir_list = dict()
        self.by_hash_dir_file = {}
        self.all_hashes = set(' ')  # must be created with at least one element

    def gen_spt_data(self):
        """
        Only called once by DupDestroyer.DataMinder#flash_entries
        to compile statistics and persistent data structures
        """
        self.by_dir_file = {}
        self.by_file_hash = {}
        self.by_hash_files = {}
        for file_hash, v in self.by_hash_dir_file.iteritems():
            for dir_name, file_path_list in v.iteritems():
                if dir_name not in self.dir_list:
                    self.dir_list[dir_name] = []
                    self.create_show_dirs(
                        cur_dir=dir_name,
                        root=self.short_parent_folder
                    )
                for file_path in file_path_list:
                    self.new_dir_file(dir_name=dir_name, file_path=file_path)
                    self.new_hash_file(file_hash=file_hash, file_path=file_path)
                    self.new_file_hash(file_hash=file_hash, file_path=file_path)
        self.num_uniq_files = len(self.by_hash_dir_file)
        self.num_dirs_reviewed = len(self.by_dir_file)

    def new_dir_file(self, dir_name=None, file_path=None):
        """
        Only called once by DupDestroyer.DataMinder#gen_spt_data
        Creates self.by_dir_file - a dict of all filepaths in a directory
        """
        if dir_name not in self.by_dir_file.keys():
            self.by_dir_file[dir_name] = []
        try:
            self.by_dir_file[dir_name].append(file_path)
        except KeyError:
            logger.error(log_msg(
                dir_name_k=dir_name,
                file_path_v=file_path,
                err_msg='Unable to append path to dir'))
            pass

    def new_hash_file(self, file_hash=None, file_path=None):
        """
        Only called once by DupDestroyer.DataMinder#gen_spt_data
        Creates self.by_hash_files - a dict of all filepaths by hash
        """
        if file_hash not in self.by_hash_files.keys():
            self.by_hash_files[file_hash] = []
        try:
            self.by_hash_files[file_hash].append(file_path)
        except KeyError:
            logger.error(log_msg(
                file_hash_k=file_hash,
                file_path_v=file_path,
                err_msg='Unable to append path to hash'))
            pass

    def new_file_hash(self, file_hash=None, file_path=None):
        """
        Only called once by DupDestroyer.DataMinder#gen_spt_data
        Creates self.by_file_hash - a dict of hashes by file_path
        """
        try:
            self.by_file_hash[file_path] = file_hash
        except KeyError:
            logger.error(log_msg(
                file_path_k=file_path,
                file_hash_v=file_hash,
                err_msg='Unable to append hash to path'))
            pass

    def create_entry(self, file_hash=None, dname=None, file_path=None, dir_name=None):
        """
            Places all found hashes-files-dirs into multiple data structures.
            The multiple data structures are post-processed to keep id'd dups.
            Creates the by_hash_dir_file which is a dict - dict - list.
            self.by_hash_dir_file[file_hash][dir_name] = list(file_path)s
        """

        self.all_hashes.add(file_hash)
        if file_hash not in self.by_hash_dir_file.keys():
            self.by_hash_dir_file[file_hash] = {}
        if dir_name not in self.by_hash_dir_file[file_hash]:
            self.by_hash_dir_file[file_hash][dir_name] = []
        try:
            self.by_hash_dir_file[file_hash][dir_name].append(file_path)
        except KeyError:
            logger.error(log_msg(
                file_hash_k1=file_hash,
                dir_name_k2=dir_name,
                file_path_v=file_path,
                err_msg='Unable to append path to hash/dir'))
            pass

    def flash_entries(self):
        """
        {hash: {dir: [files]}}
        the following is necessary to strip out hashes that only contain
        one result within a dir, there should be > 1 files
        if a hash has > 1 dir then that too is a keeper
        DupDestroyer.DataMinder#gen_spt_data is called to compile all statistics
        """
        tmp_dict = {out_k: {in_k: in_v for in_k, in_v in out_v.items()
                            if (len(out_v) == 1 and len(in_v) > 1)
                            or len(out_v) > 1}
                    for out_k, out_v in self.by_hash_dir_file.items()}
        """
        this next step removes all the empty entries
        ... this is the only way I can think to do it
        """
        self.by_hash_dir_file = {k: v for k, v in tmp_dict.iteritems()
                                 if len(v) > 0}
        self.gen_spt_data()

    def create_show_dirs(self, cur_dir=None, root=None):
        '''
        create the directory hierarchy for each dup dir
        you basically walk the path back to the root dir
        '''
        path, base = os.path.split(cur_dir)
        parent = path
        if path == root or cur_dir == root:
            parent = '#'
        self.dir_list[cur_dir] = [cur_dir, parent, base]
        if parent == '#':
            return
        else:
            self.create_show_dirs(cur_dir=path, root=root)

    def get_files_byhash(self, dir_list=None):
        files_byhash = {}
        for dir_name in dir_list:
            dir_name = str(dir_name)
            tmp_dict = {k: v for k, v in self.by_hash_files.iteritems()
                        if any(dir_name in s for s in v)}
            files_byhash.update(tmp_dict)
        OrderedDict(sorted(files_byhash.items(), key=lambda t: len(t[1])))
        return files_byhash

    def del_by_list_of_files(self, files_to_move=None):
        """
            this updates the list in memory and all dependent data structures
        """
        for file_path in files_to_move:
            file_hash = self.by_file_hash[file_path]
            dir_name = ntpath.dirname(file_path)
            if file_path in self.by_hash_dir_file[file_hash][dir_name]:
                self.by_hash_dir_file[file_hash][dir_name].remove(file_path)
        self.flash_entries()

    def get_dirs_with_dups(self):
        dup_dirs = self.by_dir_file.keys()
        dup_dirs.sort()
        return dup_dirs


class DupFinder(object):
    def __init__(self, acfg):
        search_dir = acfg['SEARCH_SCOPE']
        self.pics_root = acfg['PICS_ROOT']
        self.dm = DataMinder(search_dir=search_dir, pics_root=self.pics_root)
        self.dest_dir = acfg['FINAL_RESTING_PLACE']
        self.appl_root = acfg['APPL_ROOT']
        self.appl_pics_root = acfg['APPL_PICS_ROOT']
        self.web_pics_root = acfg['WEB_PICS_ROOT']
        self.num_files_moved = 0

        # if '#' not in self.dir_list:
        #     path, base = os.path.split(self.pics_root)
        #     self.dir_list['#'] = [self.pics_root, '#', base]

        self.find_dup(search_dir)
        self.num_dirs_reviewed = 0
        self.num_img_dups = 0
        self.num_files_confirmed = None

    def get_dirs_with_dups(self):
        """
        Called by the jQueryUI.DirTree.makeTree routine
        :return: List of all directories containing duplicates
        """
        # return self.dm.get_dirs_with_dups()
        return self.dm.dir_list.values()

    def find_dup(self, parent_folder):
        """
        searches for duplicate img files from the parent down
        :param parent_folder: directory to search for dups
        :return: None, loads two data structures:
            self.dups: format {hash:[list of file pathnames]}
            self.dir_has_dups: format {dirname:[list of hashes]}
        """
        img_types = ['.jpg', '.jpe', '.jpeg']
        for dname, subdirs, fileList in os.walk(parent_folder):
            if dname is not self.dest_dir:  # filter out dest dir
                for filename in fileList:
                    fname, fext = os.path.splitext(filename)
                    if fext in img_types:
                        path = os.path.join(dname, filename)
                        file_hash = hashlib.md5(
                            open(path, 'rb').read()).hexdigest()
                        path, dir_name = \
                            normalize_pics_root(
                                fix_list=[path, dname],
                                pics_root=self.pics_root,
                                appl_pics_root=self.appl_pics_root
                            )
                        self.dm.create_entry(
                            file_hash=file_hash,
                            dname=dname,
                            file_path=path,
                            dir_name=dir_name
                        )
        self.dm.flash_entries()

    def confirmer(self):
        results = []
        all_hashes = sorted(self.dm.all_hashes)
        self.num_files_confirmed = 0
        for dname, subdirs, fileList in os.walk(self.dest_dir):
            for filename in fileList:
                self.num_files_confirmed += 1
                path = os.path.join(dname, filename)
                file_hash = hashlib.md5(
                    open(path, 'rb').read()).hexdigest()
                # if file_hash not in self.dm.by_hash_files.keys():
                if file_hash in all_hashes:
                    # 'not in' construct does not seem to work
                    pass
                else:
                    path = path.replace(self.pics_root, self.web_pics_root)
                    path = path.replace('\\', '/')
                    results.append([path, filename])
        logger.debug(log_msg(
            dest_dir=self.dest_dir,
            results=results,
            num_files_confirmed=self.num_files_confirmed
        ))
        return results

    def get_img_urls(self, dir_list):
        """
        a list of dirs are passed in
        retrieve all urls for the duplicate images listed for those dirs
        {out_k: {in_k: [in_v]}} ... out_v is the {in_k: [in_v]} section
        self.dedups[file_hash][dir_name] = [list of dup img urls]
        """
        self.num_dirs_reviewed = len(dir_list)
        img_urls = self.dm.get_files_byhash(dir_list=dir_list)
        self.num_img_dups = len(img_urls)
        return img_urls

    def move_to_final_resting_place(self, pics_to_move):
        """
        A list of files are passed in but they are the displayed client values.
        The old path name and the new path name need to be constructed
        from the names passed in.

        pic_to_move:
        _from Otto\\_before pictures\\1990's\\1993\\19930115 - 09 - Copy.jpg

        old_pic_loc:
        acfg['APPL_PICS_ROOT'] \ pic_to_move
        C:\Users\Maste\_My Stuff\PycharmProjects\DupFinder\static\media\pics\
            _from Otto\_before pictures\1990's\1993\19930115 - 09 - Copy.jpg

        new_pic_loc:
        C:\Users\Maste\_My Stuff\PycharmProjects\DupFinder\static\media\pics\
            __delete these pictures, they are duplicates___\
           19930115 - 09 - Copy.jpg

        """
        self.num_files_moved = len(pics_to_move)
        for pic_to_move in pics_to_move:
            # pic_to_move = pic_to_move.replace('/', '\\')
            old_pic_loc = "{}\{}".format(self.appl_pics_root, pic_to_move)
            # old_pic_loc = old_pic_loc.replace('\\\', '\')
            old_pic_loc = os.path.abspath(old_pic_loc)
            new_pic_loc = "{}\{}".format(self.dest_dir, ntpath.basename(
                pic_to_move))
            new_pic_loc = os.path.abspath(new_pic_loc)
            # TODO check if file exists
            new_pic_loc = self.get_target_filename(new_pic_loc)
            try:
                os.rename(old_pic_loc, new_pic_loc)
            except WindowsError:
                logger.error(log_msg(
                    pic_to_move=pic_to_move,
                    old_pic_loc=old_pic_loc,
                    new_pic_loc=new_pic_loc,
                    err_msg='Problem renaming old to new filename'))
                base, ext = os.path.splitext(new_pic_loc)
                os.rename(new_pic_loc, base + '_' + ext)
                os.rename(old_pic_loc, new_pic_loc)
        self.dm.del_by_list_of_files(pics_to_move)

    def get_target_filename(self, target):
        while os.path.exists(target):
            logger.error(log_msg(
                msg='target filename exists',
                target=target
            ))
            base, ext = os.path.splitext(target)
            target = base + '_' + ext
        return target


if __name__ == '__main__':
    # search_scope = r"\_from Otto\_before pictures\1990's"
    # df = DupDestroyer(search_dir=r"C:\Users\Michele\Pictures" + search_scope,
    #                dest_dir='/static/media/pics/__delete these pictures, they are duplicates___',
    #                appl_root='C:/Users/Michele/PycharmProjects/DupDestroyer'
    #                )
    # df.get_dirs_with_dups()

    # for dname, subdirs, fileList in os.walk(r"C:\Users\Michele\Pictures"):
    #     print "hello"

    root = r"C:\Users\Michele\Pictures"
    for item in os.listdir(root):
        ritem = os.path.join(root, item)
        if os.path.isdir(ritem):
            print
            ritem

    # print "dedups ({}):\n".format(len(df.dedups))
    # pp.pprint(df.dedups)
    #
    # pics_to_move = [ "_from Otto\\_before pictures\\1990's\\1995\\1995 0301 08.jpg",
    #                   "_from Otto\\_before pictures\\1990's\\1993\\19930115 - 11.jpg",
    #                   "_from Otto\\_before pictures\\1990's\\1993\\199304 - Becky & Gina - Copy.jpg"]
    # df.del_dedup_entry(pics_to_move)

    # dups = df.dups
    # print "Dups type/len : ", type(dups), "/", len(dups)
    # print "Dups: ", df.pp.pprint(dups)
    #
    # dhd = df.dir_has_dups
    # print "Dir has Dups type/len : ", type(dhd), "/", len(dhd)
    # print "Dir has Dups: ", df.pp.pprint(dhd)
    #
    # dwd = df.dirs_with_dups()
    # print "Dirs with Dups type/len : ", type(dwd), "/", len(dwd)
    # print "Dirs with Dups: ", df.pp.pprint(dwd)