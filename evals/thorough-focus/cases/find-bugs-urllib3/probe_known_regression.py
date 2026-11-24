import urllib3
from urllib3 import HTTPConnectionPool, PoolManager
from urllib3.util.url import parse_url
def t(label, f):
    try: print(label, '->', repr(f()))
    except Exception as e: print(label, '-> raises', type(e).__name__, str(e)[:90])
# R1: unbracketed scoped IPv6 host to a connection pool
t('pool host fe80::1%eth0', lambda: HTTPConnectionPool('fe80::1%eth0').host)
t('pool host fe80::1%25eth0', lambda: HTTPConnectionPool('fe80::1%25eth0').host)
t('pool _tunnel_host fe80::1%Eth0', lambda: HTTPConnectionPool('fe80::1%Eth0')._tunnel_host)
t('pool host [fe80::1%25Eth0]', lambda: HTTPConnectionPool('[fe80::1%25Eth0]').host)
# zone case: distinct zones share a pool?
pm = PoolManager()
t('pools for %25Eth0 vs %25eth0 same?', lambda: pm.connection_from_url('http://[fe80::1%25Eth0]/') is pm.connection_from_url('http://[fe80::1%25eth0]/'))
# R2/R3: repeated normalization of a percent-encoded zone
t('parse once  [fe80::1%2525]', lambda: parse_url('http://[fe80::1%2525]/').host)
t('parse twice [fe80::1%2525]', lambda: parse_url(parse_url('http://[fe80::1%2525]/').url).host)
t('parse once  [fe80::1%25en%2530]', lambda: parse_url('http://[fe80::1%25en%2530]/').host)
t('parse twice [fe80::1%25en%2530]', lambda: parse_url(parse_url('http://[fe80::1%25en%2530]/').url).host)
