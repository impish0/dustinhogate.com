#!/usr/bin/env python3
"""Development server with automatic rebuilding on file changes"""
import os
import sys
import time
import threading
import subprocess
import http.server
import socketserver
import socket
import signal
from pathlib import Path

# Configuration
PORT = 8000
WATCH_DIRS = ['posts', 'images', 'tailoza']  # tailoza includes all assets
WATCH_FILES = ['config.json', 'build.py', 'serve.py']
CHECK_INTERVAL = 1  # seconds
ROOT_DIR = None  # Will be set to the root directory before changing to output

class FileWatcher:
    """Watch for file changes and trigger rebuilds"""
    
    def __init__(self):
        self.last_modified = {}
        self.running = True
        self._scan_files()
    
    def _scan_files(self):
        """Scan all watched files and directories"""
        timestamps = {}
        
        # Watch specific files (from ROOT_DIR)
        for file_path in WATCH_FILES:
            full_path = os.path.join(ROOT_DIR, file_path)
            if os.path.exists(full_path):
                timestamps[file_path] = os.path.getmtime(full_path)
        
        # Watch directories
        for dir_name in WATCH_DIRS:
            dir_path = os.path.join(ROOT_DIR, dir_name)
            if os.path.exists(dir_path):
                for root, dirs, files in os.walk(dir_path):
                    # Skip hidden directories
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    
                    for file in files:
                        # Skip hidden and temporary files
                        if not file.startswith('.') and not file.endswith('~'):
                            file_path = os.path.join(root, file)
                            # Store relative to ROOT_DIR for consistency
                            rel_path = os.path.relpath(file_path, ROOT_DIR)
                            timestamps[rel_path] = os.path.getmtime(file_path)
        
        return timestamps
    
    def check_changes(self):
        """Check if any files have changed"""
        current = self._scan_files()
        
        # First run - initialize
        if not self.last_modified:
            self.last_modified = current
            return False
        
        # Check for changes
        changed = False
        
        # Check for modified or new files
        for file_path, mtime in current.items():
            if file_path not in self.last_modified or self.last_modified[file_path] != mtime:
                print(f"\n✓ Detected change in: {file_path}")
                changed = True
        
        # Check for deleted files
        for file_path in self.last_modified:
            if file_path not in current:
                print(f"\n✓ Detected deletion of: {file_path}")
                changed = True
        
        self.last_modified = current
        return changed
    
    def watch(self):
        """Main watch loop"""
        print("👀 Watching for changes...")
        
        while self.running:
            if self.check_changes():
                print("🔨 Rebuilding site...")
                try:
                    # Run build.py from ROOT_DIR
                    result = subprocess.run([sys.executable, 'build.py'], 
                                         capture_output=True, 
                                         text=True,
                                         cwd=ROOT_DIR)
                    
                    if result.returncode == 0:
                        print("✅ Build successful!")
                        if result.stdout:
                            print(result.stdout)
                    else:
                        print("❌ Build failed!")
                        if result.stderr:
                            print(result.stderr)
                        if result.stdout:
                            print(result.stdout)
                
                except Exception as e:
                    print(f"❌ Build error: {e}")
                
                print("\n👀 Watching for changes...")
            
            time.sleep(CHECK_INTERVAL)
    
    def stop(self):
        """Stop watching"""
        self.running = False

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with custom 404 page support"""
    
    def __init__(self, *args, directory=None, **kwargs):
        """Initialize with explicit directory to avoid getcwd() issues"""
        # Set directory to output folder explicitly
        if directory is None:
            directory = os.path.join(ROOT_DIR, 'output')
        super().__init__(*args, directory=directory, **kwargs)
    
    def log_message(self, format, *args):
        # Only log errors (status codes >= 400)
        if len(args) >= 3 and isinstance(args[1], str) and args[1].startswith(('4', '5')):
            super().log_message(format, *args)
    
    def do_GET(self):
        """Handle GET requests with directory index and custom 404 page"""
        try:
            # Remove leading slash and decode URL
            file_path = self.path.lstrip('/')
            full_path = os.path.join(self.directory, file_path)

            # Handle root path
            if self.path == '/':
                self.path = '/index.html'
                return super().do_GET()

            # If path is a directory, look for index.html inside
            if os.path.isdir(full_path):
                index_path = os.path.join(full_path, 'index.html')
                if os.path.isfile(index_path):
                    # Rewrite path to include index.html
                    self.path = self.path.rstrip('/') + '/index.html'
                    return super().do_GET()

            # Check if file exists directly
            if os.path.isfile(full_path):
                return super().do_GET()

            # File doesn't exist, serve custom 404 page
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            # Read and serve the 404.html page
            try:
                notfound_path = os.path.join(self.directory, '404.html')
                with open(notfound_path, 'rb') as f:
                    self.wfile.write(f.read())
            except FileNotFoundError:
                # Fallback to simple 404 message if 404.html doesn't exist
                self.wfile.write(b'<html><body><h1>404 - Page Not Found</h1><p>The requested page could not be found.</p></body></html>')
                
        except Exception as e:
            # Handle any errors gracefully
            self.send_error(500, f"Internal server error: {e}")
    
    def handle(self):
        """Handle requests but suppress BrokenPipeError"""
        try:
            super().handle()
        except BrokenPipeError:
            # This happens when clients disconnect early (browser cancels, etc)
            # It's normal and can be safely ignored
            pass
        except Exception:
            # Let other exceptions propagate
            raise

def serve():
    """Start the development server"""
    global ROOT_DIR
    
    # Store the root directory before changing to output
    ROOT_DIR = os.getcwd()
    
    # First, build the site
    print("🔨 Building site...")
    try:
        result = subprocess.run([sys.executable, 'build.py'], 
                              capture_output=True, 
                              text=True)
        
        if result.returncode != 0:
            print("❌ Initial build failed!")
            if result.stderr:
                print(result.stderr)
            if result.stdout:
                print(result.stdout)
            return
        
        print("✅ Initial build successful!")
        if result.stdout:
            print(result.stdout)
    
    except Exception as e:
        print(f"❌ Build error: {e}")
        return
    
    # Don't change directory - keep working from ROOT_DIR
    # The HTTP handler will use the output directory explicitly
    
    # Start file watcher in a separate thread
    watcher = FileWatcher()
    watcher_thread = threading.Thread(target=watcher.watch)
    watcher_thread.daemon = True
    watcher_thread.start()
    
    # Start HTTP server
    Handler = CustomHTTPRequestHandler

    # Create a server subclass that sets socket reuse options before binding
    class ReusableTCPServer(socketserver.TCPServer):
        allow_reuse_address = True
        def server_bind(self):
            # Set socket options before bind so the OS allows quick reuse
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                # SO_REUSEPORT may be available on some systems and allows multiple
                # sockets to bind to the same port (useful during restarts)
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except Exception:
                pass
            return super().server_bind()

    try:
        with ReusableTCPServer(("", PORT), Handler) as httpd:
            print(f"\n🚀 Server running at http://localhost:{PORT}")
            print("   Press Ctrl+C to stop\n")

            # Graceful shutdown on SIGINT/SIGTERM
            def _shutdown(signum, frame):
                print("\n\n🛑 Signal received, shutting down server...")
                watcher.stop()
                # Call shutdown from a separate thread to avoid deadlocks in signal handler
                threading.Thread(target=httpd.shutdown, daemon=True).start()

            signal.signal(signal.SIGINT, _shutdown)
            signal.signal(signal.SIGTERM, _shutdown)

            try:
                httpd.serve_forever()
            finally:
                # Ensure we always stop watcher and close the server socket
                print("\n\n🛑 Shutting down server...")
                watcher.stop()
                try:
                    httpd.shutdown()
                except Exception:
                    pass
                try:
                    httpd.server_close()
                except Exception:
                    pass
                # Give watcher thread a moment to stop
                watcher_thread.join(timeout=2)
    
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {PORT} is already in use. Please try a different port or stop the other server.")
        else:
            print(f"❌ Server error: {e}")

if __name__ == "__main__":
    # Make sure we're in the right directory
    if not os.path.exists('build.py'):
        print("❌ Error: serve.py must be run from the root directory of your blog")
        sys.exit(1)
    
    serve()