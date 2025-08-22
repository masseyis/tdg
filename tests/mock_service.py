"""
Standalone mock service for testing generated API tests.

This service reads an OpenAPI spec and creates mock endpoints that return
appropriate responses for testing.
"""

import json
import sys
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import yaml
import threading
import time


class MockAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler that serves mock API endpoints"""
    
    def __init__(self, *args, spec_data=None, **kwargs):
        self.spec_data = spec_data
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        self._handle_request('GET')
    
    def do_POST(self):
        """Handle POST requests"""
        self._handle_request('POST')
    
    def do_PUT(self):
        """Handle PUT requests"""
        self._handle_request('PUT')
    
    def do_DELETE(self):
        """Handle DELETE requests"""
        self._handle_request('DELETE')
    
    def do_PATCH(self):
        """Handle PATCH requests"""
        self._handle_request('PATCH')
    
    def _handle_request(self, method):
        """Handle all HTTP requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        # Serve OpenAPI spec
        if path == '/openapi.json':
            self._send_json_response(self.spec_data, 200)
            return
        
        # Handle API endpoints
        if path in self.spec_data.get('paths', {}):
            path_item = self.spec_data['paths'][path]
            if method.lower() in path_item:
                self._handle_api_endpoint(path, method, path_item[method.lower()])
                return
        
        # Default response for unknown endpoints
        self._send_json_response({"error": "Not found"}, 404)
    
    def _handle_api_endpoint(self, path, method, operation):
        """Handle specific API endpoint based on OpenAPI spec"""
        
        # Read request body for POST/PUT/PATCH
        content_length = int(self.headers.get('Content-Length', 0))
        body = None
        if content_length > 0:
            body = self.rfile.read(content_length).decode('utf-8')
        
        # Generate appropriate mock response based on method
        if method.upper() == 'GET':
            response_data = self._generate_get_response(operation)
            self._send_json_response(response_data, 200)
        elif method.upper() == 'POST':
            response_data = self._generate_post_response(operation, body)
            self._send_json_response(response_data, 201)
        elif method.upper() == 'PUT':
            response_data = self._generate_put_response(operation, body)
            self._send_json_response(response_data, 200)
        elif method.upper() == 'DELETE':
            response_data = self._generate_delete_response(operation)
            self._send_json_response(response_data, 204)
        else:
            response_data = {"message": "mock response"}
            self._send_json_response(response_data, 200)
    
    def _generate_get_response(self, operation):
        """Generate mock response for GET requests"""
        # Try to get response schema from OpenAPI spec
        responses = operation.get('responses', {})
        if '200' in responses:
            response_spec = responses['200']
            if 'content' in response_spec:
                content = response_spec['content']
                if 'application/json' in content:
                    schema = content['application/json'].get('schema', {})
                    return self._generate_from_schema(schema)
        
        # Default response
        return {"id": 1, "name": "test", "status": "available"}
    
    def _generate_post_response(self, operation, body):
        """Generate mock response for POST requests"""
        # Try to parse the request body
        request_body = None
        if body:
            try:
                request_body = json.loads(body)
            except:
                pass
        
        # Generate response based on request
        if request_body and 'name' in request_body:
            return {"id": 123, "name": request_body['name'], "created": True}
        else:
            return {"id": 123, "created": True}
    
    def _generate_put_response(self, operation, body):
        """Generate mock response for PUT requests"""
        return {"id": 123, "updated": True}
    
    def _generate_delete_response(self, operation):
        """Generate mock response for DELETE requests"""
        return {"deleted": True}
    
    def _generate_from_schema(self, schema):
        """Generate mock data from JSON schema"""
        if schema.get('type') == 'array':
            return [self._generate_from_schema(schema.get('items', {}))]
        elif schema.get('type') == 'object':
            result = {}
            properties = schema.get('properties', {})
            for prop_name, prop_schema in properties.items():
                result[prop_name] = self._generate_from_schema(prop_schema)
            return result
        elif schema.get('type') == 'string':
            return "mock_string"
        elif schema.get('type') == 'integer':
            return 123
        elif schema.get('type') == 'number':
            return 123.45
        elif schema.get('type') == 'boolean':
            return True
        else:
            return "mock_value"
    
    def _send_json_response(self, data, status_code):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, PATCH, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        response_body = json.dumps(data, indent=2)
        self.wfile.write(response_body.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to reduce logging noise"""
        pass


class MockService:
    """Mock API service that serves endpoints based on OpenAPI spec"""
    
    def __init__(self, spec_path: Path, port: int = 8081):
        self.spec_path = spec_path
        self.port = port
        self.server = None
        self.spec_data = None
        self.server_thread = None
    
    def load_spec(self):
        """Load and parse the OpenAPI spec"""
        with open(self.spec_path, 'r') as f:
            if self.spec_path.suffix in ['.yaml', '.yml']:
                self.spec_data = yaml.safe_load(f)
            else:
                self.spec_data = json.load(f)
        
        print(f"Loaded OpenAPI spec with {len(self.spec_data.get('paths', {}))} endpoints")
    
    def start(self):
        """Start the mock service"""
        self.load_spec()
        
        # Create custom handler with spec data
        class Handler(MockAPIHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, spec_data=self.spec_data, **kwargs)
        
        # Start server in a separate thread
        self.server = HTTPServer(('localhost', self.port), Handler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # Wait a moment for server to start
        time.sleep(1)
        
        print(f"Mock service started on http://localhost:{self.port}")
        print(f"OpenAPI spec available at http://localhost:{self.port}/openapi.json")
    
    def stop(self):
        """Stop the mock service"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            print("Mock service stopped")


def main():
    """Main function to run the mock service"""
    if len(sys.argv) != 3:
        print("Usage: python mock_service.py <spec_file> <port>")
        sys.exit(1)
    
    spec_path = Path(sys.argv[1])
    port = int(sys.argv[2])
    
    if not spec_path.exists():
        print(f"Spec file not found: {spec_path}")
        sys.exit(1)
    
    service = MockService(spec_path, port)
    
    try:
        service.start()
        print("Mock service running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping mock service...")
        service.stop()


if __name__ == "__main__":
    main()
