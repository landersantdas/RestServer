'''
Code edited from https://gist.github.com/tliron/8e9757180506f25e46d9
'''

import sys, os, re, shutil, json, urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse, http.server
import imp

here = os.path.dirname(os.path.realpath(__file__))

records = {}

def get_records(handler):
    return records

def get_record(handler):
    key = urllib.parse.unquote(handler.path[8:])
    return records[key] if key in records else None

def set_record(handler):
    key = urllib.parse.unquote(handler.path[8:])
    payload = handler.get_payload()
    records[key] = payload
    return records[key]

def delete_record(handler):
    key = urllib.parse.unquote(handler.path[8:])
    del records[key]
    return True # anything except None shows success

def rest_call_json(url, payload=None, with_payload_method='PUT'):
    'REST call with JSON decoding of the response and JSON payloads'
    if payload:
        if not isinstance(payload, str):
            payload = json.dumps(payload)
        # PUT or POST
        response = urllib.request.urlopen(MethodRequest(url, payload, {'Content-Type': 'application/json'}, method=with_payload_method))
    else:
        # GET
        response = urllib.request.urlopen(url)
    response = response.read().decode()
    return json.loads(response)

class MethodRequest(urllib.request.Request):
    'See: https://gist.github.com/logic/2715756'
    def __init__(self, *args, **kwargs):
        if 'method' in kwargs:
            self._method = kwargs['method']
            del kwargs['method']
        else:
            self._method = None
        return urllib.request.Request.__init__(self, *args, **kwargs)

    def get_method(self, *args, **kwargs):
        return self._method if self._method is not None else urllib.request.Request.get_method(self, *args, **kwargs)

class RESTRequestHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.routes = {
            r'^/$': {'file': 'web/index.html', 'media_type': 'text/html'},
            r'^/records$': {'GET': get_records, 'media_type': 'application/json'},
            r'^/record/': {'GET': get_record, 'PUT': set_record, 'DELETE': delete_record, 'media_type': 'application/json'}}
        
        return http.server.BaseHTTPRequestHandler.__init__(self, *args, **kwargs)
    
    def do_HEAD(self):
        self.handle_method('HEAD')
    
    def do_GET(self):
        self.handle_method('GET')

    def do_POST(self):
        self.handle_method('POST')

    def do_PUT(self):
        self.handle_method('PUT')

    def do_DELETE(self):
        self.handle_method('DELETE')
    
    def get_payload(self):
        payload_len = int(self.headers.get('content-length'))
        payload = self.rfile.read(payload_len)
        payload = payload.decode('utf-8').replace("'" , "\"")
        payload = json.loads(payload)
        return payload
        
    def handle_method(self, method):
        route = self.get_route()
        if route is None:
            self.send_response(404)
            self.end_headers()
            self.wfile.write('Route not found\n'.encode('utf-8'))
        else:
            if method == 'HEAD':
                self.send_response(200)
                if 'media_type' in route:
                    self.send_header('Content-type', route['media_type'])
                self.end_headers()
            else:
                if 'file' in route:
                    if method == 'GET':
                        try:
                            f = open(os.path.join(here, route['file']))
                            try:
                                self.send_response(200)
                                if 'media_type' in route:
                                    self.send_header('Content-type', route['media_type'])
                                self.end_headers()
                                shutil.copyfileobj(f, self.wfile.encode('utf-8'))
                            finally:
                                f.close()
                        except:
                            self.send_response(404)
                            self.end_headers()
                            self.wfile.write('File not found\n'.encode('utf-8'))
                    else:
                        self.send_response(405)
                        self.end_headers()
                        self.wfile.write('Only GET is supported\n')
                else:
                    if method in route:
                        content = route[method](self)
                        if content is not None:
                            self.send_response(200)
                            if 'media_type' in route:
                                self.send_header('Content-type', route['media_type'])
                            self.end_headers()
                            if method != 'DELETE':
                                self.wfile.write(json.dumps(content).encode("utf-8"))
                        else:
                            self.send_response(404)
                            self.end_headers()
                            self.wfile.write('Not found\n')
                    else:
                        self.send_response(405)
                        self.end_headers()
                        self.wfile.write(method + ' is not supported\n')
                    
    
    def get_route(self):
        for path, route in self.routes.items():
            if re.match(path, self.path):
                return route
        return None

def rest_server(port):
    'Starts the REST server'
    http_server = http.server.HTTPServer(('', port), RESTRequestHandler)
    print('Starting HTTP server at port %d' % port)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass
    print('Stopping HTTP server')
    http_server.server_close()

def main(argv):
    rest_server(8888)

if __name__ == '__main__':
    main(sys.argv[1:])
