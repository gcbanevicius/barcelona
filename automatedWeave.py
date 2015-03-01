#!/usr/bin/env python

import sys
import subprocess
import re
import os

def validateFileName(fileName, pattern):
    match = re.search(pattern, fileName)
    if match:
        return True
    else:
        return False


def main():
    apkFileName = sys.argv[1] 

    ret = validateFileName(apkFileName, "^.+\.apk$")
    if ret == False:
        print "Please specify a valid APK file as input"
        exit(1)

    # rename and unzip the apk
    zipFileName = re.sub("\.apk$", ".zip", apkFileName)
    print apkFileName, zipFileName
    if os.path.isfile(zipFileName):
        print "Trying to copy to a file that already exists. Please delete or rename %s" % zipFileName
        exit(1)
    subprocess.call("cp %s %s" % (apkFileName, zipFileName), shell=True)

    # unzip to a dir
    unzipDirName = re.sub("\.zip$", "Unzipped", zipFileName)
    print unzipDirName
    subprocess.call("unzip %s -d %s" % (zipFileName, unzipDirName), shell=True)

    # check for dex2jar scripts


    # invoke dex2jar



    # do your work!




    # invoke jar2dex




    # rezip the project and rename as apk




    # sign the resulting apk






# parse the arguments








if __name__ == "__main__":
    main()
