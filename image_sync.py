#!/usr/bin/env python
import sys
import subprocess
import logging
import ConfigParser
'''
Sync glance image between OpenStack Cluster
'''
LOG = logging.getLogger('glance-image-sync')
IMAGE_DIR = "/var/lib/glance/glance-image-sync"
CONFIG_PATH = "/etc/glance/glance-image-sync.conf"
RSYNC_COMMAND = (
     "rsync -apur --partial -e 'ssh -p 22 -c arcfour128'"
     " %(file)s %(user)s@%(host)s:%(target)s"
)

class FatalErrorInSyncProcess(Exception):
    def __init__(self, msg, cmd, rep):
        self.msg = (
        'Fatal Error While attempting to sync.'
        ' COMMAND: "%s"' % (cmd)
        )
    def __str__(self):
        return self.msg

def read_sync_config(CONFIG_PATH):
    image_sync_cfg = {}
    section = 'DEFAULT'
    config = ConfigParser.RawConfigParser()
    if config.read(CONFIG_PATH):
        image_sync_cfg['username'] = config.get(section, 'user')
        image_sync_cfg['host'] = config.get(section, 'host')
        image_sync_cfg['target_path'] = config.get(section, 'target_path')
    
    return image_sync_cfg


#sync_image
class SyncImage(object):
    def __init__(self, image_sync_cfg, cmd):
        self.image_sync_cfg = image_sync_cfg
        self.cmd = cmd
    
    def __reporter(message, log_level='INFO'):
        if log_level == 'DEBUG':
            LOG.deubg(message)
        elif log_level == 'ERROR':
            LOG.error(message)
        else:
            LOG.info(message)
    
    def sync_image(self):
        self.image_filename = os.path.realpath(image_sync_cfg['datadir'])
        process_args = {
             'user':self.image_sync_cfg['username'],
             'host':self.image_sync_cfg['host'],
             'target':self.image_sync_cfg['target_path'],
             'file':self.image_filename
              }
        rsync = RSYNC_COMMAND % process_args
        try:
            return_code = subprocess.call(
            rsync, shell=True,
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
            )
            if return_code == 23:
                self.__reporter(
                        'This Sync was Aborted due to'
                        ' error code "%d" which was returned from RSYNC.'%(return_code)
                         )
        except FatalErrorInSyncProcess:
            self.__reporter('ERROR:Job is aborted', log_level='ERROR')


        
        
    


