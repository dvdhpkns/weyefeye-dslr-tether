from time import sleep
import os
import requests
from wireless import Wireless

HOST = 'http://10.98.32.1:8080'
STORAGE = 'DCIM'
DESTINATION_PATH = 'photos/'


class XSAlbum:
    """Album object, making it easier to get path to an album and list all files in an album"""
    def __init__(self, album_name, slot, host=HOST):
        self.album_name = album_name
        self.slot = slot
        self.host = host

    def get_album_path(self):
        """Path to album on WeyeFeye device"""
        return '%s/%s/%s' % (self.host, STORAGE, self.album_name)

    def _get_files(self, limit=1000, start=0):
        # ex. http://10.98.32.1:8080/DCIM/101CANON/?image=1&limit=264&start=0&slot=0
        url = '%s/?image=1&limit=%s&start=%s&slot=%s&image=1' % (self.get_album_path(), limit, start, self.slot)
        resp = xs_request(url)
        if resp.status_code == 404:
            print("Failed attempt to get recent files - is XS connected to camera?")
            return []
        # list images separated by \n, so split on that
        files = resp.text.split('\n')
        if '' in files:
            files.remove('')
        return files

    def get_all_files(self):
        """Get list of all files in a given album"""
        _files = []
        more = True
        start = 0
        limit = 1000
        while more:
            last_fetched = self._get_files(limit=limit, start=start)
            _files.extend(last_fetched)
            more = bool(len(last_fetched) == limit)
            if more:
                start += limit
        print("total files: %s" % len(_files))
        return _files

    def __repr__(self):
        return "Album(%s slot %s)" % (self.album_name, self.slot)

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(self, other.__class__):
            return self.__dict__ == other.__dict__
        return False

    def __ne__(self, other):
        """Overrides the default implementation (unnecessary in Python 3)"""
        return not self.__eq__(other)

    def __hash__(self):
        """Needed for adding to set. File path contains all differentiating characteristics, so has on that"""
        return hash((self.get_album_path() + self.slot))


class XSFile:
    def __init__(self, file_name, xs_album):
        self.album = xs_album
        self.file_name = file_name

    def get_file_path(self):
        return '%s/%s?slot=%s' % (self.album.get_album_path(), self.file_name, self.album.slot)

    def save_img(self):
        resp = xs_request(self.get_file_path())
        dest = self.get_dest_path()
        if not resp.ok:
            print("Failed to download image, status: %s" % resp.status_code)
            return
        img = resp.content
        with open(dest, 'wb+') as handle:
            print("Saving image %s to %s" % (self.get_file_path(), dest))
            handle.write(img)

    def get_dest_path(self):
        """Path where file is saved"""
        return DESTINATION_PATH + self.file_name

    def __repr__(self):
        """Use path for string representation"""
        return "File(%s)" % (self.get_file_path())

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(self, other.__class__):
            return self.__dict__ == other.__dict__
        return False

    def __ne__(self, other):
        """Overrides the default implementation (unnecessary in Python 3)"""
        return not self.__eq__(other)

    def __hash__(self):
        """Needed for adding to set. File path contains all differentiating characteristics, so has on that"""
        return hash((self.get_file_path()))


class XSConnectionException(Exception):
    """Exception to be thrown whenever connectivity to device fails"""
    def __init__(self):
        connected = is_connected_to_network()
        message = "Not connect to WeyeFeye Network" if not connected else \
            "Issue reading files - is XS properly connected to camera?"
        super(XSConnectionException, self).__init__(message)


def get_album_list(add_files=False):
    """Get list of all albums on device"""
    albums = []
    slots = [0, 1]
    card_found = False
    for slot in slots:
        # get list of albums in slots
        # ex. http://10.98.32.1:8080/DCIM/?quick=1&slot=0
        slot_resp = xs_request('%s/%s/?slot=%s&quick=1' % (HOST, STORAGE, slot))
        if slot_resp.status_code == 404:
            continue
        card_found = True
        # returns list separated by \n, so we split
        album_list = slot_resp.text.split('\n')
        for a in album_list:
            if a == '':
                continue
            xs_album = XSAlbum(a, slot)
            if add_files:
                xs_album.get_all_files()
            albums.append(xs_album)
    # if no camera is
    if not card_found:
        raise XSConnectionException
    return albums


def big_log(text):
    print("\n----- %s -----\n" % text)


def xs_request(url):
    """Helper method for requests to WeyeFeye that adds timeout and raises XSConnectionException on failure"""
    try:
        return requests.get(url, timeout=1.0)
    except requests.exceptions.Timeout, requests.exceptions.ConnectionError:
        raise XSConnectionException


def is_connected_to_network():
    """Check to see if connected to WeyeFeye network with name like 'WeyeFeyeb17d8a'"""
    w = Wireless()
    network_name = w.current()
    connected = bool(network_name and "WeyeFeye" in network_name)
    return connected


def get_all_files():
    """Get list of all files on device"""
    from datetime import datetime
    start = datetime.now()
    albums = get_album_list()
    files = []
    for album in albums:
        files.extend([XSFile(f_name, album) for f_name in album.get_all_files()])
    print(str(datetime.now() - start) + " to fetch all files")
    return files


def sync_photos(files):
    """Save any new photos on camera locally, remove any photos that were deleted on camera"""
    try:
        big_log("looking for file changes")
        current_files = set(get_all_files())
        # update only if there is a list of files
        if current_files:
            files_added = current_files - files
            removed_files = files - current_files
            print("%s files added, %s files removed" % (len(files_added), len(removed_files)))
            for f in files_added:
                f.save_img()
            for f in removed_files:
                if os.path.isfile(f.get_dest_path()):
                    os.remove(f.get_dest_path())
            files = current_files
    except XSConnectionException as e:
        big_log(e.message)

    return files


# ----------------- MAIN APPLICATION CODE ---------------------
def main():
    big_log("Starting WeyeFeye XS photo finder...")

    sync_enabled = True
    files = set()
    initialized = False

    while sync_enabled:
        if is_connected_to_network():
            if not initialized:
                big_log("initializing file list")
                files = set(get_all_files())
            else:
                files = sync_photos(files)
        else:
            big_log("Not connected to WeyeFeye network")
        sleep(5)


if __name__ == "__main__":
    main()
