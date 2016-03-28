#!/usr/bin/env python
import os
import sys
import argparse
import logging
import commands
import prettytable
import time
import subprocess
from novaclient import client
from cinderclient.v1 import client as cinder_client
from cinderclient import utils as cinder_utils
from glanceclient.v1 import client as glance_client
from glanceclient.common import utils as glance_utils
from keystoneclient.v2_0 import client as keystone_client
from neutronclient.v2_0 impport client as neutron_client
from novaclient.v1_1 import client as nova_client
from novaclient.v1_1 import shell as nova_shell
from novaclient import utils as nova_utils
import image_sync

logging.basicConfig(level=logging.ERROR)

class DoMigrate(object):
    def __init__(self,*os_creds,instanceID):
        self.nova = NovaManager(*os_creds, instanceID)
        self.glance = GlanceManager(*os_creds)
        self.cinder = CinderManager(*os_creds)

    def run(self):
        self.nova.server_create_image()


class NovaManager(object):
    def __init__(self, username, password, tenant_id, auth_url):
        self.client = nova_client.Client(username, password, tenant_id, auth_url)
    
    #return a list of serverObject    
    def server_list(self):
        return self.client.servers.list()
    
    #serverObject is from self.client.servers.list()
    def server_create_image(self,serverObject):
        self.image_name = serverObject.name + time.strftime("_%Y%m%d%H%M%S",time.localtime())
        self.imageID = self.client.servers.create_image(serverObject, image_name)   
        return self.imageID
  
    def get_imageObject(self.imageID):
        imageObject = self.client.images.get(self.imageID)
        return imageObject
    


class GlanceManager(object):
    def __init__(self, username, password, tenant_id,auth_url):
        keystone_mgr = Credit(username, 
                              password, 
                              tenant_name,
                              auth_url)
        self.client = glance_client.Client(
                      endpoint = keystone_mgr.get_endpoint("image"),
                      token = keystone_mgr.get_token(),
                      )
    #image_list() for download the image
    def image_list(self, owner=None, is_public=None)
        return self.client.images.list(owner=owner, is_public=is_public)

    def image_get(self, id):
        return self.client.images.get(id)
    
    def download_image(self,owner=None, is_public=None):
        tenant_images = self.client.list(owner=owner,is_public=is_public)
        snapshots = list()
        images = list()
        #not sure
        for image in tenant_images:
            if 'image_type' in image.properties:
                if image.properties['image_type'] == 'snapshot':
                    snapshot.append(image)
            else:
                images.append(image)
        for v_image in images:
            if v_image['status'] == "active"
            print "Start download {name}".format(name=v_image['name'])
            download_command = ['glance','image-download','{}'.format(v_image['id']),
                                '--file','{name}-{id}'.format(name=v_image['name'], id=v_image['id'])]
            download_status = subprocess.Popen(download_command, 
                                               stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE).communicate()
            print "Name:{name},   ID:{id},    Status:{status}".format(name=v_image['name'], id=v_image['id']
                                                                      status = download_status)

class CinderManager(object):
    #cinder = client.Client('1','admin','admin','admin','http://172.16.101.2:5000/v2.0/')
    def __init__(self, username, password, auth_url):
        self.client = cinder_client.Client(username,
                                           password,
                                           project,
                                           auth_url)
    def volume_list(self):
        return self.client.volumes.list()

    def create_vol_snapshot(self,volumeObject):
        #client.volume_snapshots
        snapshot_vol = "cinder snapshot-volume --force True --display-name %s %s"%(volumeObject.display_name,
                                                                                   volumeObject.id)
        ret = commands.getstatusoutput( snapshot_vol )
        status = "Taking snapshot done!"
 	if ret[0] == 0:
            return status
        
    def create_vol_based_on_snapshot(self, size, snapshot_id, volume_name):
        #create(self, size, snapshot_id=None, source_volid=None, display_name=None, display_description=None, volume_type=None, user_id=None, project_id=None, availability_zone=None, metadata=None, imageRef=None)
        size = size
        snapshot_id = snapshot_id
        display_name = volume_name
        self.vol_snap_create = self.client.volumes.create(self, size, snapshot_id=, display_name= )
        return self.volume_create.id

    def upload_to_image(self):
        image_from_vol = cinder.volumes.upload_to_image('70b3f348-4c1e-4f23-82bc-e0344652c5e9','True','upload_to_image','bare','qcow2')
        imageID = image_from_vol[1]['os-volume_upload_image']['image_id']
        #if upload is ok
        return imageID

class Credit(object):
    def __init__(self,username,password,tenant_name,auth_url):
        #USE Dict-type
        self.client = keystone_client.Client(username=username,
                                             password=password,
                                             tenant_name=tenant_name,
                                             auth_url=auth_url)
    def get_token(self):
        return self.client.auth_token
    
    def get_endpoint(self,service_type,endpoint_type="publicURL"):
        catalog = self.client.service_catalog.get_endpoints()
        return catalog[service_type][0][endpoint_type]

def main():
    desc = "Migrate VM instance between OpenStack Cluster"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("username",type=str, nargs=1,
                        help="Username to access the source cluster")
    parser.add_argument("password",type=str,nargs=1,
                        help="Username's password")
    parser.add_argument("tenant_id",type=str,nargs=1,
                        help="Name of tenant_id")
    parser.add_argument("auth_url",type=str,nargs=1,
                        help="Authentication URL")
    parser.add_argument("instanceID",type=str,nargs=1,
                        help="ID of VM instance")

    args = parser.parse_args()
    os_creds = (args.username[0], args.password[0],
                args.tenant_id[0],  args.auth_url[0])
    
    migrate = DoMigrate(*os_creds, args.instanceID[0])
    migrate.run()

if __name__ == "__main__":
    main()


