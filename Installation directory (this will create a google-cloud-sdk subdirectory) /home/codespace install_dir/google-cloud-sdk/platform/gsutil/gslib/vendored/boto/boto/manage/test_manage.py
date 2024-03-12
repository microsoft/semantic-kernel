from boto.manage.server import Server
from boto.manage.volume import Volume
import time

print('--> Creating New Volume')
volume = Volume.create()
print(volume)

print('--> Creating New Server')
server_list = Server.create()
server = server_list[0]
print(server)

print('----> Waiting for Server to start up')
while server.status != 'running':
    print('*')
    time.sleep(10)
print('----> Server is running')

print('--> Run "df -k" on Server')
status = server.run('df -k')
print(status[1])

print('--> Now run volume.make_ready to make the volume ready to use on server')
volume.make_ready(server)

print('--> Run "df -k" on Server')
status = server.run('df -k')
print(status[1])

print('--> Do an "ls -al" on the new filesystem')
status = server.run('ls -al %s' % volume.mount_point)
print(status[1])

