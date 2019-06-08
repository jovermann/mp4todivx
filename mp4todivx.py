#!/usr/bin/env python
#
# mp4todivx.py - Convert a directory tree full of *.mp4 video files to a directory tree full of *.avi video files containing DivX streams
#
# Copyright (C) 2019 by Johannes Overmann <Johannes.Overmann@joov.de>
#
# This file is licensed under the terms of the MIT license.  
# See file LICENSE or https://opensource.org/licenses/MIT.

import optparse
import sys
import glob
import os
import re


def isWindows():
    """Return true iff the host operating system is Windows.
    """
    return os.name == "nt"


def isdigit(char):
    """Return True iff char is a digit.
    """
    return char.isdigit()
    

def isalpha(char):
    """Return True iff char is a letter.
    """
    return char.isalpha()
    

class Error:
    """Generic error exception class, carrying a message.
    """
    def __init__(self, message):
        self.message = message
        
        
def writeStringToFile(fileName, s):
    """Write string to file.
    """
    f = open(fileName, "wb")
    f.write(s)
    f.close()
    
    
def readStringFromFile(fileName):
    """Read string from file and return it.
    """
    f = open(fileName, "rb")
    r = f.read()
    f.close()
    return r


def run(cmd):
    """Run command.
    """
    if options.verbose:
        print "Running " + cmd
    if isWindows():
        cmd = cmd.replace("/", "\\")
        cmd = cmd.replace("'", '"')
    if os.system(cmd):
        raise Error("Command failed: " + cmd)

        
def removeFiles(pattern):
    """Remove files matching glob pattern.
    """
    for f in glob.glob(pattern):
        os.remove(f)
    
        
def mkdir(path):
    """Make directory if it does not yet exist. Recursively.
    """
    if not path:
        return
    if os.path.isdir(path):
        return
    mkdir(os.path.dirname(path))
    os.mkdir(path)

    
def sanitizeFilename(path):
    """Sanitize filename so that it only contains alphanumeric characters, dots and underscores.
    
    In particular:
     - Replace spaces and dashes with underscores.    
     - Replace all german umlauts (in UTF-8 encoding) with their ASCII transliterations.
     - Erase everything else (e.g. braces, commas etc).
    """
    # German umlauts.
    r = path.replace("a\xcc\x88", "ae")
    r = path.replace("o\xcc\x88", "oe")
    r = path.replace("u\xcc\x88", "ue")
    r = path.replace("A\xcc\x88", "Ae")
    r = path.replace("O\xcc\x88", "Oe")
    r = path.replace("U\xcc\x88", "Ue")
    r = path.replace("\xc3\x9f", "ss")
    
    # Spaces and dashes.
    r = r.replace(" - ", "_")
    r = r.replace(" ", "_")
    r = r.replace("-", "_")
    
    # Erase everything else.
    r = re.sub("[^0-9a-zA-Z._/]", "", r)
    return r


def processFile(inpath, outpath):
    """Convert file to avi/DivX.
    
    ffmpeg -i in.mp4 -c:v mpeg4 -vtag xvid -b 2600k out.avi
    """
    # Ignore if outpath already exists.
    if os.path.exists(outpath):
        return

    print inpath, "->", outpath
    if options.dummy:
        return

    # Copy mp4 to filename without spaces.
    content = readStringFromFile(inpath)
    writeStringToFile("tmp.mp4", content)
    
    # Make outdir
    mkdir(os.path.dirname(outpath))
    
    # Convert.
    run("ffmpeg -i tmp.mp4 -c:v mpeg4 -vtag xvid -b:v 2600k " + outpath)
        

def main():
    global options
    usage = """Usage: %prog INDIR [OUTDIR]

Convert all *.mp4 files found in INDIR to *.avi files in OUTDIR (containing DivX streams).

This tool needs ffmpeg on the path.

To install ffmpeg on macOS do:
    brew install ffmpeg
"""
    version = "0.0.1"
    parser = optparse.OptionParser(usage=usage, version=version)
    parser.add_option("-d", "--dummy",  default=False, action="store_true", help="Dummy mode. Nothing changes on disk.")
    parser.add_option("-v", "--verbose",  default=0, action="count", help="Be more verbose.")
    (options, args) = parser.parse_args()

    if len(args) not in (1, 2):
	parser.error("Please specify INDIR [OUTDIR].")
    if len(args) < 2:
        args.append("avi_divx")
    indir = args[0]
    outdir = args[1]
        

    try:
        if os.path.isdir(indir):
            for root, dirs, files in os.walk(indir):
                subdir = root[len(indir) + 1:]
                for localfile in files:
                    if not localfile.lower().endswith(".mp4"):
                        continue
                    # Ignore macOS resource forks.
                    if localfile.startswith("._"):
                        continue
                    path = subdir + "/" + localfile
                    inpath = indir + "/" + path
                    outpath = outdir + "/" + path
                    outpath = sanitizeFilename(outpath)
                    outpath = re.sub("[.]mp4$", ".avi", outpath)
                    processFile(inpath, outpath)
        elif os.path.isfile(indir):
            inpath = indir
            path = os.path.basename(inpath)
            outpath = outdir + "/" + path
            outpath = sanitizeFilename(outpath)
            outpath = re.sub("[.]mp4$", ".avi", outpath)
            processFile(inpath, outpath)
        else:
            print "%s not found" % indir
  
        removeFiles("tmp.mp4")

    except Error as e:
        print "Error:", e.message
        sys.exit(1)
    
    

# call main()
if __name__ == "__main__":
    main()

