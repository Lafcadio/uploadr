import flickr_api as flickr
import os.path
import sys
import operator
from glob import glob
from itertools import groupby
import argparse

KEY    = "63fc8ff7f59e7a40d344be4574471d0c"
SECRET = "d58873849eec23fa"
ROOT   = "/data/Pictures/" # Default root to use
TOKEN = ".uploadr_token"

# Permissions (0 or 1)
PUBLIC = 0
FRIEND = 1
FAMILY = 1

class Uploadr(object):
    def __init__(self, key, secret, root):
        flickr.set_keys(key, secret)
        self.authorize(root)
        self.user = flickr.test.login()

    def authorize(self, path):
        root = path
        while not os.path.exists(os.path.join(root, TOKEN)) and root is not "/":
            root = os.path.dirname(root)
        token_path = os.path.join(root, TOKEN)
        if os.path.exists(token_path):
            flickr.set_auth_handler(token_path)
        else:
            token_path = os.path.join(path, TOKEN)
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
                    photographs = list(photos)
                    photographs.sort(key = operator.attrgetter("title"))
                    return photoset, photographs
        return None, []

    def upload(self, path, photoset):
        picture = flickr.upload(photo_file = path, title = os.path.splitext(os.path.basename(path))[0], is_public = PUBLIC, is_friend = FRIEND, is_family = FAMILY)
        if photoset is None:
            photoset = flickr.Photoset.create(title = os.path.basename(os.path.dirname(path)), primary_photo = picture)
        else:
            photoset.addPhoto(photo = picture)
        return picture, photoset


def get_duplicates(photos):
    duplicates = []
    for k, g in groupby(photos, key = operator.attrgetter('title')):
        group = list(g)
        for duplicate in group[1:]:
            duplicates.append(duplicate)
    return duplicates

def delete_duplicates(duplicates):
    for duplicate in duplicates:
        print "Deleting %s" % duplicate.id
        duplicate.delete()

def get_photos(path):
    photos = []
    for extensions in ['jpg', 'JPG', 'jpeg', 'JPEG']:
        photos.extend( glob(os.path.join(path, "*.%s" % extensions)) )
    items = map(os.path.basename, photos)
    items.sort()
    return items

def sync(path, uploadr, action, delete, really = False):
    print path
    print "=" * len(path)
    photoset, remote = uploadr.load(os.path.basename(path))
    local = get_photos(path)

    print "Found %d local photos" % len(local)
    print "Found %d already uploaded photos" % len(remote)

    duplicates = get_duplicates(remote)
    if len(duplicates) > 0:
        print "Found %d duplicates" % len(duplicates)
        delete_duplicates(duplicates)


    remote_names = [item.title for item in remote]
    local_names  = [os.path.splitext(item)[0] for item in local]


    if action in ["sync", "push"] or delete:
        skipped = 0
        for item, title in zip(local, local_names):
            picture_path = os.path.join(path, item)
            if title in remote_names:
                skipped += 1
                continue
            if skipped > 0:
                print "Skipped %d remote images already %sed" % (skipped, action)
                skipped = 0

            if action in ["sync", "push"]:
                print "Uploading", picture_path
                if really:
                    picture, photoset = uploadr.upload(picture_path, photoset)
            elif delete:
                print "Deleting", picture_path
                if really:
                    os.remove(picture_path)
        if skipped > 0:
            print "Skipped %d local images already %sed" % (skipped, action)

    if action in ["sync", "pull"] or delete:
        skipped = 0
        for item in remote:
            if item.title in local_names:
                skipped += 1
                continue
            if skipped > 0:
                print "Skipped %d remote images already %sed" % (skipped, action)
                skipped = 0

            if action in ["sync", "pull"]:
                local_path = os.path.join(path, "%s.%s" % (item.title, "jpg"))
                print "Downloading", item.title, "as", local_path
                if really:
                    item.save(local_path, "Original")
            elif delete:
                print "Deleting", item.title
                if really:
                    item.delete()
        if skipped > 0:
            print "Skipped %d remote images already %sed" % (skipped, action)

    print "Done!"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Syncs directories with Flickr")
    parser.add_argument("path", nargs="*", help = "Specific directories to sync",
                        default = [path for path in glob(os.path.join(ROOT, "*")) \
                                       if os.path.isdir(path) and not os.path.exists(os.path.join(path, ".private"))])
    parser.add_argument("--action", dest="action", nargs=1, choices=["push", "pull", "sync"], default="push", help = "Push = upload (default), pull = download, sync = both")
    parser.add_argument("--delete-missing", dest="delete", action="store_true", default=False, help = "Whether or not to delete when a file at the destination is not at the source")
    parser.add_argument("--preview", dest="really", action="store_false", default=True, help = "Only pretend to do actions")
    args = parser.parse_args()
    args.path = [path.rstrip('/') for path in args.path]

    action = args.action[0]
    if action == "sync" and args.delete:
        print "The --delete-missing option makes no sense for the `sync` action"
        sys.exit(0)

    for path in args.path:
        if not os.path.exists(path):
            print "Error! `%s` does not exist" % path
            sys.exit(0)

    uploadr = Uploadr(KEY, SECRET, args.path[0])
    for path in args.path:
        sync(path, uploadr, action, args.delete, args.really)
        print ""



