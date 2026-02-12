"""
SentinelAI Monitoring Agent
Runs on monitored laptops to collect behavioral events and send to backend
"""
import os
import sys
import time
import json
import socket
import requests
import psutil
import platform
import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Optional
import threading
import queue

class SentinelAgent:
    """
    Lightweight monitoring agent for real-time threat detection
    """
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the agent with configuration"""
        self.config = self._load_config(config_path)
        self.event_queue = queue.Queue()
        self.running = False
        self.isolated = False
        
        # Agent info
        self.employee_id = self.config.get('employee_id')
        self.backend_url = self.config.get('backend_url', 'http://localhost:8000')
        self.collection_interval = self.config.get('collection_interval', 60)  # seconds
        self.batch_size = self.config.get('batch_size', 10)
        
        # System info
        self.hostname = socket.gethostname()
        self.username = os.getenv('USERNAME') or os.getenv('USER')
        
        print(f"🔍 SentinelAI Agent initialized")
        print(f"   Employee ID: {self.employee_id}")
        print(f"   Backend: {self.backend_url}")
        print(f"   Hostname: {self.hostname}")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            # Default configuration
            return {
                'employee_id': None,
                'backend_url': 'http://localhost:8000',
                'collection_interval': 60,
                'batch_size': 10
            }
    
    def register(self) -> bool:
        """Register this agent with the backend"""
        try:
            # Get system information
            system_info = {
                'hostname': self.hostname,
                'username': self.username,
                'os': platform.system(),
                'os_version': platform.version(),
                'ip_address': self._get_local_ip()
            }
            
            response = requests.post(
                f"{self.backend_url}/api/agent/register",
                json=system_info,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.employee_id = data.get('employee_id')
                
                # Save employee_id to config
                self.config['employee_id'] = self.employee_id
                self._save_config()
                
                print(f"✅ Agent registered successfully! Employee ID: {self.employee_id}")
                return True
            else:
                print(f"❌ Registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False
    
    def _save_config(self):
        """Save configuration to file"""
        with open('config.json', 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def _get_local_ip(self) -> str:
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def _get_system_metrics(self) -> Dict[str, float]:
        """Get current system metrics"""
        try:
            return {
                'cpu_usage': psutil.cpu_percent(interval=None),
                'memory_usage': psutil.virtual_memory().percent
            }
        except:
            return {'cpu_usage': 0.0, 'memory_usage': 0.0}
    
    def collect_login_event(self):
        """Collect login event"""
        event = {
            'event_type': 'login',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'location': self._get_location(),
            'ip_address': self._get_local_ip(),
            'success': True,
            **self._get_system_metrics()
        }
        self.event_queue.put(event)
    
    def collect_file_access_events(self):
        """Collect recent file access events"""
        try:
            # Monitor recent file modifications in user directories
            user_dirs = [
                os.path.expanduser('~/Documents'),
                os.path.expanduser('~/Downloads'),
                os.path.expanduser('~/Desktop')
            ]
            
            for directory in user_dirs:
                if not os.path.exists(directory):
                    continue
                    
                for root, dirs, files in os.walk(directory):
                    # Check recent files (limit to 1000 to prevent performance issues in huge dirs)
                    for file in files[:1000]:
                        file_path = os.path.join(root, file)
                        try:
                            stat = os.stat(file_path)
                            # Check if modified in last collection interval
                            if time.time() - stat.st_mtime < self.collection_interval:
                                event = {
                                    'event_type': 'file_access',
                                    'timestamp': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                    'file_path': file_path,
                                    'action': 'write',
                                    'success': True,
                                    **self._get_system_metrics()
                                }
                                self.event_queue.put(event)
                        except:
                            continue
                    break  # Only check top level
                    
        except Exception as e:
            print(f"Error collecting file events: {e}")
    
    def collect_network_events(self):
        """Collect active network connections"""
        try:
            connections = psutil.net_connections(kind='inet')
            
            for conn in connections[:10]:  # Limit to 10 connections
                if conn.status == 'ESTABLISHED' and conn.raddr:
                    event = {
                        'event_type': 'network',
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'ip_address': conn.raddr.ip,
                        'port': conn.raddr.port,
                        'success': True,
                        **self._get_system_metrics()
                    }
                    self.event_queue.put(event)
                    
        except Exception as e:
            print(f"Error collecting network events: {e}")
    
    def collect_process_events(self):
        """Collect running process information"""
        try:
            for proc in psutil.process_iter(['name', 'username']):
                try:
                    if proc.info['username'] == self.username:
                        # Only log privilege escalation attempts (sudo/admin processes)
                        if 'admin' in proc.info['name'].lower() or 'sudo' in proc.info['name'].lower():
                            event = {
                                'event_type': 'privilege_escalation',
                                'timestamp': datetime.now(timezone.utc).isoformat(),
                                'action': proc.info['name'],
                                'success': True,
                                **self._get_system_metrics()
                            }
                            self.event_queue.put(event)
                except:
                    continue
                    
        except Exception as e:
            print(f"Error collecting process events: {e}")
    
    def _get_location(self) -> str:
        """Get approximate location based on IP"""
        # For hackathon, use simple location based on network
        # In production, use IP geolocation API
        return f"{self.hostname}_location"
    
    def send_events(self):
        """Send collected events to backend"""
        if self.event_queue.empty():
            return
        
        events = []
        while not self.event_queue.empty() and len(events) < self.batch_size:
            events.append(self.event_queue.get())
        
        if not events:
            return
        
        # Add employee_id to each event
        events_with_employee_id = []
        for event in events:
            event['employee_id'] = self.employee_id
            events_with_employee_id.append(event)
            print(f"   📄 Event: {event.get('event_type')} | CPU: {event.get('cpu_usage')}% | RAM: {event.get('memory_usage')}%")
        
        try:
            response = requests.post(
                f"{self.backend_url}/api/events/bulk",
                json=events_with_employee_id,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Sent {len(events)} events to backend")
            else:
                print(f"⚠️  Failed to send events: {response.status_code}")
                # Re-queue events (without employee_id to avoid duplication)
                for event in events:
                    if 'employee_id' in event:
                        del event['employee_id']
                    self.event_queue.put(event)
                    
        except Exception as e:
            print(f"❌ Error sending events: {e}")
            # Re-queue events (without employee_id to avoid duplication)
            for event in events:
                if 'employee_id' in event:
                    del event['employee_id']
                self.event_queue.put(event)
    
    def check_isolation_status(self):
        """Check if isolation command has been issued"""
        try:
            response = requests.get(
                f"{self.backend_url}/api/agent/{self.employee_id}/status",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                should_isolate = data.get('isolated', False)
                
                if should_isolate != self.isolated:
                    if should_isolate:
                        self.isolate_network()
                    else:
                        self.restore_network()
                        
        except Exception as e:
            print(f"Error checking isolation status: {e}")
    
    def isolate_network(self):
        """Isolate this machine from the network"""
        print("🚨 ISOLATION COMMAND RECEIVED - Disabling network...")
        
        try:
            if platform.system() == 'Windows':
                # Disable all network adapters
                subprocess.run([
                    'powershell',
                    'Get-NetAdapter | Disable-NetAdapter -Confirm:$false'
                ], check=True, capture_output=True)
                
            elif platform.system() == 'Linux':
                # Disable network interfaces
                subprocess.run(['sudo', 'ifconfig', 'eth0', 'down'], check=True)
                subprocess.run(['sudo', 'ifconfig', 'wlan0', 'down'], check=True)
            
            self.isolated = True
            print("✅ Network isolated successfully")
            
        except Exception as e:
            print(f"❌ Failed to isolate network: {e}")
    
    def restore_network(self):
        """Restore network connectivity"""
        print("✅ RESTORE COMMAND RECEIVED - Enabling network...")
        
        try:
            if platform.system() == 'Windows':
                # Enable all network adapters
                subprocess.run([
                    'powershell',
                    'Get-NetAdapter | Enable-NetAdapter -Confirm:$false'
                ], check=True, capture_output=True)
                
            elif platform.system() == 'Linux':
                # Enable network interfaces
                subprocess.run(['sudo', 'ifconfig', 'eth0', 'up'], check=True)
                subprocess.run(['sudo', 'ifconfig', 'wlan0', 'up'], check=True)
            
            self.isolated = False
            print("✅ Network restored successfully")
            
        except Exception as e:
            print(f"❌ Failed to restore network: {e}")
    
    def enforce_process_policy(self):
        """Enforce process execution policies (e.g. block .bat files)"""
        try:
            # We want to catch this fast, so we iterate processes
            # This can be resource intensive so we should be careful
            # We look for cmd.exe processes with .bat in command line
            blocked_extensions = ['.bat', '.cmd', '.vbs']
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    # Check cmdline arguments
                    cmdline = proc.info['cmdline']
                    if not cmdline:
                        continue
                        
                    # Flatten cmdline to string for search
                    cmd_str = ' '.join(cmdline).lower()
                    
                    # Check if any blocked extension is in the command line
                    for ext in blocked_extensions:
                        if ext in cmd_str:
                            print(f"🚨 POLICY VIOLATION DETECTED: Illegal process {proc.info['name']} running {ext} file")
                            print(f"   Command: {cmd_str}")
                            print("   ACTION: KILLING PROCESS TREE")
                            
                            try:
                                if platform.system() == 'Windows':
                                    # Force kill process and children (Tree)
                                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(proc.pid)], 
                                                 stdout=subprocess.DEVNULL, 
                                                 stderr=subprocess.DEVNULL)
                                else:
                                    # Linux/Mac
                                    parent = psutil.Process(proc.pid)
                                    for child in parent.children(recursive=True):
                                        child.kill()
                                    parent.kill()
                            except Exception as kill_err:
                                print(f"   Error killing process: {kill_err}")
                                # Fallback
                                try:
                                    proc.kill()
                                except:
                                    pass
                            
                            # Log the event
                            event = {
                                'event_type': 'policy_violation',
                                'timestamp': datetime.now(timezone.utc).isoformat(),
                                'description': f'Blocked execution of {ext} file',
                                'details': cmd_str,
                                'success': False, 
                                **self._get_system_metrics()
                            }
                            self.event_queue.put(event)
                            break
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
                    
        except Exception as e:
            print(f"Error enforcing policies: {e}")

    def collection_loop(self):
        """Main event collection loop"""
        print(f"🔄 Starting event collection (interval: {self.collection_interval}s)")
        print(f"🛡️  Real-time process enforcement active")
        
        last_collection = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # Enforce policies frequently (every cycle)
                self.enforce_process_policy()
                
                # Check for isolation commands
                self.check_isolation_status()
                
                # Collect events only on interval
                if current_time - last_collection >= self.collection_interval:
                    print(f"\n📊 Collecting events at {datetime.now().strftime('%H:%M:%S')}")
                    
                    self.collect_login_event()
                    self.collect_file_access_events()
                    self.collect_network_events()
                    self.collect_process_events()
                    self.send_events()
                    
                    last_collection = current_time
                
                # Sleep briefly to not eat CPU, but fast enough to catch processes
                time.sleep(1) # check every 1 second
                
            except KeyboardInterrupt:
                print("\n⚠️  Stopping agent...")
                break
            except Exception as e:
                print(f"❌ Error in collection loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def start(self):
        """Start the monitoring agent"""
        if not self.employee_id:
            print("❌ Agent not registered. Please run register() first.")
            return
        
        self.running = True
        
        print("\n" + "="*50)
        print("🚀 SentinelAI Agent Started")
        print("="*50)
        print(f"Employee ID: {self.employee_id}")
        print(f"Monitoring: {self.username}@{self.hostname}")
        print(f"Backend: {self.backend_url}")
        print("="*50 + "\n")
        
        try:
            self.collection_loop()
        except KeyboardInterrupt:
            print("\n⚠️  Agent stopped by user")
        finally:
            self.running = False
            print("👋 Agent shutdown complete")


def main():
    """Main entry point"""
    print("""
    ╔═══════════════════════════════════════╗
    ║      SentinelAI Monitoring Agent      ║
    ║   Real-Time Threat Detection System   ║
    ╚═══════════════════════════════════════╝
    """)
    
    agent = SentinelAgent()
    
    # Check if already registered
    if not agent.employee_id:
        print("📝 First time setup - registering with backend...")
        if not agent.register():
            print("❌ Failed to register. Please check backend connection.")
            return
    
    # Start monitoring
    agent.start()


if __name__ == "__main__":
    main()
