import flickr_api as flickr
import os.path
import sys
import operator
from glob import glob
from itertools import groupby

KEY    = "63fc8ff7f59e7a40d344be4574471d0c"
SECRET = "d58873849eec23fa"
ROOT   = "/data/Pictures/"

class Uploadr(object):
    def __init__(self, key, secret):
        flickr.set_keys(key, secret)
        self.authorize()
        self.user = flickr.test.login()
        self.photos = []
        self.photoset = None

    def authorize(self):
        token_path = os.path.join(ROOT, TOKEN)
        if os.path.exists(token_path):
            flickr.set_auth_handler(token_path)
        else:
            a = flickr.auth.AuthHandler()
            print "Please go to the following URL, and enter the oauth_verifier:"
            print "                                              --------------"
            print a.get_authorization_url("delete")
            print ""
            print "oauth_verifier:",
            code = raw_input()
            try:
                a.set_verifier(code)
            except:
                print "ERROR! Code was not accepted. Please try again."
                sys.exit(0)
            a.save(token_path)
            flickr.set_auth_handler(a)

    def load(self, set_name):
        """ Sets the current set to the "Uploading" set """
        sets = self.user.getPhotosets()
        for page in [self.user.getPhotosets(page = p) for p in range(sets.info.pages)]:
            for photoset in page:
                if photoset.title == set_name:
                    photos = photoset.getPhotos()
                    for page in range(photos.info.pages - 1):
                        photos.extend(photoset.getPhotos(page = page + 2))
                    self.photos = list(photos)
                    self.set = photoset
                    self.photos.sort(key = operator.attrgetter("title"))
                    print "Found %d previously uploaded photos" % len(self.uploading)
                    return
        print "Did not find any previously uploaded photos"
        self.photos = []
        self.photoset = None

    def get_duplicates(self):
        duplicates = []
        for k, g in groupby(self.uploading, key = operator.attrgetter('title')):
            group = list(g)
            for duplicate in group[1:]:
                duplicates.append(duplicate)

    def delete_duplicates(self, duplicates = None):
        if duplicates is None:
            duplicates = self.get_duplicates()
        for duplicate in duplicates:
            print "Deleting %s" % duplicate.id
            duplicate.delete()


if __name__ == "__main__":
    uploadr = Uploadr(KEY, SECRET)
    for path in glob(os.path.join(ROOT, "*")):
        if path is os.path.dir(path):
            if os.path.exists(os.path.join(path, ".private")):
                continue
            print path
            #uploadr.load(os.path.basename(path)




