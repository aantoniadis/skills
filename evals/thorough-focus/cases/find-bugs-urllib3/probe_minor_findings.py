from urllib3 import PoolManager, HTTPSConnectionPool
pm=PoolManager()
a=pm.connection_from_host('ex%61mple.com'); b=pm.connection_from_host('example.com')
print('two pools:', a is not b, 'hosts', a.host, b.host)
p=HTTPSConnectionPool('ex%2fample.com'); print('host', p.host, 'tunnel', p._tunnel_host)
