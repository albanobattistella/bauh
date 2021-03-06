import glob
import logging
import os
import tarfile
import time
import traceback
from multiprocessing import Process
from pathlib import Path
from threading import Thread

import requests

from bauh.api.http import HttpClient
from bauh.gems.appimage import LOCAL_PATH, db


class DatabaseUpdater(Thread if bool(int(os.getenv('BAUH_DEBUG', 0))) else Process):

    URL_DB = 'https://raw.githubusercontent.com/vinifmor/bauh-files/master/appimage/dbs.tar.gz'
    COMPRESS_FILE_PATH = LOCAL_PATH + '/db.tar.gz'

    def __init__(self, http_client: HttpClient, logger: logging.Logger):
        super(DatabaseUpdater, self).__init__(daemon=True)
        self.http_client = http_client
        self.logger = logger
        self.enabled = bool(int(os.getenv('BAUH_APPIMAGE_DB_UPDATER', 1)))
        self.sleep = 60 * 20

    def _download_databases(self):
        self.logger.info('Retrieving AppImage databases')

        res = self.http_client.get(self.URL_DB)

        if res:
            Path(LOCAL_PATH).mkdir(parents=True, exist_ok=True)

            with open(self.COMPRESS_FILE_PATH, 'wb+') as f:
                f.write(res.content)

            self.logger.info("Database file saved at {}".format(self.COMPRESS_FILE_PATH))

            old_db_files = glob.glob(LOCAL_PATH + '/*.db')

            if old_db_files:
                self.logger.info('Deleting old database files')
                for f in old_db_files:
                    db.acquire_lock(f)
                    os.remove(f)
                    db.release_lock(f)

                self.logger.info('Old database files deleted')

            self.logger.info('Uncompressing {}'.format(self.COMPRESS_FILE_PATH))

            try:
                tf = tarfile.open(self.COMPRESS_FILE_PATH)
                tf.extractall(LOCAL_PATH)
                self.logger.info('Successfully uncompressed file {}'.format(self.COMPRESS_FILE_PATH))
            except:
                self.logger.error('Could not extract file {}'.format(self.COMPRESS_FILE_PATH))
                traceback.print_exc()
            finally:
                self.logger.info('Deleting {}'.format(self.COMPRESS_FILE_PATH))
                os.remove(self.COMPRESS_FILE_PATH)
                self.logger.info('Successfully removed {}'.format(self.COMPRESS_FILE_PATH))

        else:
            self.logger.warning('Could not download the database file {}'.format(self.URL_DB))

    def run(self):
        if self.enabled:
            while True:
                try:
                    self._download_databases()
                except requests.exceptions.ConnectionError:
                    self.logger.warning('The internet connection seems to be off.')

                self.logger.info('Sleeping')
                time.sleep(self.sleep)
        else:
            self.logger.warning('AppImage database updater disabled')
