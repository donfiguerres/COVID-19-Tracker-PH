""" Handles deployment of generated artifacts."""

import os
import sys
import logging
import getpass
import shutil
import traceback
from ftplib import FTP, error_perm


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TRACKER_DIR = CHART_OUTPUT = os.path.join(SCRIPT_DIR, "tracker")


def store_files(ftp, path):
    for name in os.listdir(path):
        localpath = os.path.join(path, name)
        if os.path.isfile(localpath):
            logging.info(f"STOR {name} {localpath}")
            ftp.storbinary('STOR ' + name, open(localpath,'rb'))
        elif os.path.isdir(localpath):
            logging.info(f"MKD {name}")
            try:
                ftp.mkd(name)
            # ignore "directory already exists"
            except error_perm as e:
                if not e.args[0].startswith('550'):
                    raise
            logging.info(f"CWD {name}")
            ftp.cwd(name)
            store_files(ftp, localpath)
            logging.info(f"CWD ..")
            ftp.cwd("..")


def deploy_ftp(source):
    ftp = FTP('ftpupload.net')
    user = input("username: ")
    passwd = getpass.getpass("password: ")
    ftp.login(user=user, passwd=passwd)
    ftp.cwd("htdocs")
    store_files(ftp, source)
    ftp.quit()
    return
    dest = os.path.join(TRACKER_DIR, "charts")
    for filename in os.listdir(source):
        fullpath = os.path.join(source, filename)
        logging.info(f"Copying {filename}")
        shutil.copy(fullpath, dest)

def main():
    logging.basicConfig(level=logging.DEBUG)
    deploy_ftp("_site")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logging.error(e)
        logging.error(traceback.format_exc())
        sys.exit(1)
