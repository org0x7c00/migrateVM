from keystoneclient.v2_0 import client as keystone_client
from keystoneclient import session
from keystoneclient.auth.identity import v2
from novaclient.v1_1 import client as nova_client
from glanceclient.v1 import client as glance_client
import subprocess
from cinderclient.v1 import client as cinder_client
import time
class Credit(object):
    def __init__(self, username, password, tenant_name,auth_url):
        self.client = keystone_client.Client(username=username,
                                             password = password,
                                             tenant_name = tenant_name,
                                             auth_url = auth_url)
        

    def get_token(self):
        return self.client.auth_token
    def get_endpoint(self,service_type,endpoint_type="publicURL"):
        catalog = self.client.service_catalog.get_endpoints()
        return catalog[service_type][0][endpoint_type]
    def get_project_id(self):
        return self.client.tenant_id

class GlanceManager(object):
    def __init__(self, token, endpoint, imageID):
        self.client = glance_client.Client(
                                          endpoint=endpoint, 
                                          token=token 
                                          )
        self.imageID = imageID
    def download_image(self, owner=None, is_public=None):
        tenant_images = self.client.images.list(owner=owner, is_public=is_public)
        snapshots = list()
        images = list()
        for image in tenant_images:
            if 'image_type' in image.properties :
                if image.properties['image_type'] == 'snapshot':
                    snapshots.append(image)
            else:
                images.append(image)
        print "-------image-------"
        print image
        print '>>>>>>snapshots>>>>>>>>'
        print snapshots
        print '>>>>>>>>>>>>>>>'
        for v_image in images:
            if v_image.id == self.imageID and v_image.status == 'active':
                print "Start download {name}".format(name=v_image.name)
                download_command = ['glance','image-download','{}'.format(v_image.id),
                                '--file','{name}-{id}'.format(name=v_image.name, id=v_image.id)]
                download_status = subprocess.Popen(download_command,
                                               stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE).communicate()
                print "Name:{name},   ID:{id},    Status:{status}".format(name=v_image.name, id=v_image.id,
                                                                      status = download_status)
                
class NovaManager(object):
    def __init__(self, username,password,tenant_name,auth_url):
        self.client = nova_client.Client(username, password, tenant_name, auth_url)

    def server_list(self):
        self.serverObjectList = self.client.servers.list()
        return self.serverObjectList
    def create_server_image(self,vm_index=0):
        self.serverObject = self.server_list()[vm_index-1]
        print self.serverObject.name
        self.image_name = self.serverObject.name + self.serverObject.id[:6] + time.strftime("_%Y%m%d%H%M%S",time.localtime())
        self.imageID = self.client.servers.create_image(self.serverObject, self.image_name)
        return self.imageID
    def get_attached_volumes(self,serverObject):
        self.volumesID = self.client.volumes.get_server_volumes(serverObject.id)
        return self.volumesID

class CinderManager(object):
    def __init__(self,username,password,tenant_name,auth_url):
        self.client = cinder_client.Client(username,password,tenant_name,auth_url)    
    
    def create_vol_snapshot(self, volumeObject):
        vol_snapshot_id = list()
        self.snapshotObjectlist = list()
        for vol_obj in volumeObject:
            snapshotObject = self.client.volume_snapshots.create(vol_obj.id,force=True)
            if snapshotObject:
                vol_snapshot_id.append(snapshotObject.id)
                self.snapshotObjectlist.append(snapshotObject)
        return vol_snapshot_id
    
    def create_vol_based_on_snapshot(self,self.snapshotObjectlist):
        for snapshotObject in self.snapshotObjectlist:
            self.vol_id = self.client.volumes.create(snapshotObject.size, snapshotObject.id, snapshotObject.display_name)
        return self.vol_id
    
    def upload_to_image(self,volumeObject, image_name):
        vol_image = self.client.volumes.upload_to_image(volumeObject, image_name)
        self.imageID = vol_image[1]['os-volume_upload_image']['image_id']
        return self.imageID

def main():
    auth = {'username':'admin','password':'admin','tenant_name':'admin','auth_url':'http://172.16.101.2:5000/v2.0/'}
    token = Credit(**auth).get_token()
    endpoint = Credit(**auth).get_endpoint('image',"publicURL")
    tenant_id = Credit(**auth).get_project_id()
    novamanager = NovaManager(**auth)   
    serverObjectList = novamanager.server_list()
    print serverObjectList
   # imageID = novamanager.create_server_image(2)
    #print "imageID",imageID
    serverObject = serverObjectList[1]
    print "server ID:",serverObject.id
    volumeObject = novamanager.get_attached_volumes(serverObject)
    print "Attached volume Object:",volumeObject
    cindermanager = CinderManager(**auth)
    vol_snapshot_id =  cindermanager.create_vol_snapshot(volumeObject) #a snapshot id list
    cindermanager.create_vol_based_on_snapshot(cindermanager.snapshotObjectlist)
    uploaded_imageID = cindermanager.upload_to_image(volumeObject, "image_name")
    imageID = uploaded_imageID
    #glancemanager = GlanceManager(token,endpoint,imageID)
    #glancemanager.download_image(owner=tenant_id,is_public=True)



if __name__ == "__main__":
    main()
