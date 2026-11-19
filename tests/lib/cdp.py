"""Minimal Chrome DevTools Protocol client (standard library only) for tests.
The app is started with --remote-debugging-port=<port>; connect() picks the page whose URL contains `match`.
Usage: import cdp; s = cdp.connect(9333); cdp.ev(s, 'expression')['result']['result']['value']"""
import socket, base64, os, json, struct, sys, time, urllib.request
def connect(port=9333, match='api/documents', wait=60):
    # the debug port and the editor page appear a little after the window does: retry
    end=time.time()+wait
    while True:
        try:
            tabs=json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json'))
            t=[x for x in tabs if match in x['url']][0]
            break
        except Exception:
            if time.time()>end: raise
            time.sleep(1)
    path=t['webSocketDebuggerUrl'].split(f':{port}',1)[1]
    s=socket.create_connection(('127.0.0.1',port))
    key=base64.b64encode(os.urandom(16)).decode()
    s.sendall((f'GET {path} HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n').encode())
    buf=b''
    while b'\r\n\r\n' not in buf: buf+=s.recv(4096)
    return s
def send(s,obj):
    d=json.dumps(obj).encode(); m=os.urandom(4)
    h=bytearray([0x81]); n=len(d)
    if n<126: h.append(0x80|n)
    elif n<65536: h.append(0x80|126); h+=struct.pack('>H',n)
    else: h.append(0x80|127); h+=struct.pack('>Q',n)
    s.sendall(bytes(h)+m+bytes(b^m[i%4] for i,b in enumerate(d)))
def recv(s):
    def rn(n):
        b=b''
        while len(b)<n: b+=s.recv(n-len(b))
        return b
    out=b''
    while True:
        h=rn(2); op=h[0]&15; n=h[1]&127
        if n==126: n=struct.unpack('>H',rn(2))[0]
        elif n==127: n=struct.unpack('>Q',rn(8))[0]
        out+=rn(n)
        if h[0]&0x80: return json.loads(out)
_id=[0]
def ev(s,expr):
    _id[0]+=1
    send(s,{'id':_id[0],'method':'Runtime.evaluate','params':{'expression':expr,'returnByValue':True,'awaitPromise':True}})
    while True:
        r=recv(s)
        if r.get('id')==_id[0]: return r
def value(s, expr):
    r = ev(s, expr)['result']
    if 'exceptionDetails' in r:
        raise RuntimeError(r['exceptionDetails'].get('exception', {}).get('description', 'js error'))
    return r['result'].get('value')
if __name__ == '__main__':
    # usage: cdp.py <js expression> [url-substring]   (default page: the editor; 'onlyoffice://plugin' = the start screen)
    s = connect(match=sys.argv[2]) if len(sys.argv) > 2 else connect()
    print(json.dumps(value(s, sys.argv[1]), ensure_ascii=False)[:3000])
