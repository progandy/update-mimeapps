#!/usr/bin/python
#
# update-mimeapps.py
#
# License: MIT License
#
# Copyright (c) 2018 A. Bosch
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
from configparser import ConfigParser
from pathlib import PosixPath
import sys

class DesktopEntry():
    def __init__(self, filename):
        c = ConfigParser(interpolation=None)
        c.read(filename)
        self.mime = c.get("Desktop Entry", "MimeType", fallback="")
        self.mime = [x.strip() for x in self.mime.split(";") if x.strip()]
        self.hidden = c.getboolean("Desktop Entry", "Hidden", fallback=False)

    def getHidden(self):
        return self.hidden

    def getMimeTypes(self):
        return self.mime

class DefaultMimeApps:
    def __init__(self, filename):
        self.section = "Default Applications"
        self.file = ConfigParser(interpolation=None)
        self.filename = filename
        self.file.read(self.filename)
        if not self.file.has_section(self.section):
            self.file.add_section(self.section)

    def append_desktop(self, mime, name):
        files = self.file.get(self.section, mime, fallback="")
        if files:
            files = [x.strip() for x in files.split(";")]
            if not name in files:
                files.append(name)
                self.file.set(self.section, mime, ";".join(files))
        else:
            self.file.set(self.section,mime,name)

    def apply_filter(self, falsefilter):
        for mime, dfiles in self.file.items(self.section):
            files = [x.strip() for x in dfiles.split(';') if falsefilter(mime, x.strip())]
            if len(files):
                self.file.set(self.section, mime, ";".join(files))
            else:
                self.file.remove_option(self.section, mime)

    def write(self, fileobject, space=True):
        return self.file.write(fileobject,  space_around_delimiters=space)

def main(argv):
    if len(argv) > 1:
        if "-h" in argv[1:]:
            print("""Usage: update-mimeapps.py [-h]

Maintains a stable order of default applications in /usr/share/applications/mimeapps.list""")
            return 0
        dryrun = "-d" in argv[1:]

    files={}
    for dfile in PosixPath("/usr/share/applications/").glob("*.desktop"):
        files[dfile.name] = DesktopEntry(dfile)

    MIMEAPPS_LIST = "/usr/share/applications/mimeapps.list"

    mimeapps = DefaultMimeApps(MIMEAPPS_LIST)

    # remove missing associations
    def valid_association(mime, desktop):
        if not desktop in files:
            return False
        df = files[desktop]
        return not df.getHidden() and mime in df.getMimeTypes();

    mimeapps.apply_filter(valid_association)

    # append new associations
    for name,desktop in sorted(files.items()):
        if not desktop.getHidden():
            for mime in desktop.getMimeTypes():
                mimeapps.append_desktop(mime, name)

    # TODO: write to MIMEAPPS_LIST
    mimeapps.write(sys.stdout,False)

sys.exit(main(sys.argv))
