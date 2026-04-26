import subprocess
import json
import os
import time
import random
import requests
import glob
import socket
import re
from threading import Lock


class V2RayManager:
    def __init__(self, config_pattern="v2ray_*.json"):
        self.config_pattern = config_pattern
        self.configs = []
        self.current_config = None
        self.current_config_file = None
        self.v2ray_process = None
        self.lock = Lock()
        self.socks_port = 10808
        self.http_port = 10809
        self.v2ray_cmd = None
        self.load_all_configs()
        self.detect_v2ray_command()
    
    def detect_v2ray_command(self):
        """Detect available V2Ray command (v2ray or xray)"""
        try:
            result = subprocess.run(['v2ray', '--version'], capture_output=True, timeout=3)
            if result.returncode == 0:
                self.v2ray_cmd = 'v2ray'
                print("✅ Found V2Ray")
                return
        except:
            pass
        
        try:
            result = subprocess.run(['xray', '--version'], capture_output=True, timeout=3)
            if result.returncode == 0:
                self.v2ray_cmd = 'xray'
                print("✅ Found Xray (alternative to V2Ray)")
                return
        except:
            pass
        
        self.v2ray_cmd = None
        print("❌ V2Ray/Xray not found! Please install: pkg install v2ray")
    
    def load_all_configs(self):
        """Load all V2Ray configurations from v2ray_1.json, v2ray_2.json, etc."""
        try:
            config_files = glob.glob(self.config_pattern)
            config_files.sort()
            
            if not config_files:
                print(f"⚠️ រកមិនឃើញឯកសារ {self.config_pattern}")
                print("💡 សូមបង្កើតឯកសារ v2ray_1.json, v2ray_2.json, ...")
                return
            
            self.configs = []
            for config_file in config_files:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    config['_file'] = config_file
                    match = re.search(r'v2ray_(\d+)\.json', config_file)
                    config['_index'] = int(match.group(1)) if match else 0
                    
                    # Extract remark from config
                    if 'remarks' in config:
                        config['remark'] = config['remarks']
                    elif 'remark' not in config:
                        config['remark'] = f"V2Ray Config {config['_index']}"
                    
                    # Extract server and protocol info
                    try:
                        if 'outbounds' in config and len(config['outbounds']) > 0:
                            outbound = config['outbounds'][0]
                            config['protocol'] = outbound.get('protocol', 'unknown')
                            if 'settings' in outbound and 'vnext' in outbound['settings']:
                                vnext = outbound['settings']['vnext'][0]
                                config['server'] = vnext.get('address', 'unknown')
                                config['port'] = vnext.get('port', 0)
                    except:
                        pass
                    
                    self.configs.append(config)
            
            print(f"✅ បានផ្ទុក V2Ray configs {len(self.configs)} ឯកសារ:")
            for cfg in self.configs:
                print(f"   📁 {cfg['_file']} - {cfg.get('remark', 'Unknown')}")
                
        except Exception as e:
            print(f"❌ មិនអាចផ្ទុក V2Ray configs: {e}")
            self.configs = []
    
    def parse_config(self, config):
        """Parse config and extract connection info"""
        try:
            outbound = config["outbounds"][0]
            protocol = outbound["protocol"]
            
            vnext = outbound["settings"]["vnext"][0]
            user = vnext["users"][0]
            
            parsed = {
                "protocol": protocol,
                "address": vnext["address"],
                "port": vnext["port"],
                "uuid": user["id"],
                "encryption": user.get("encryption", "none"),
                "streamSettings": outbound.get("streamSettings", {})
            }
            
            # For VMESS, add security
            if protocol == "vmess":
                parsed["security"] = user.get("security", "auto")
            else:
                parsed["security"] = "none"
            
            return parsed
        except Exception as e:
            print(f"❌ Parse config error: {e}")
            return None
    
    def build_runtime_config(self, parsed):
        """Build clean V2Ray runtime configuration"""
        user_config = {
            "id": parsed["uuid"],
            "encryption": parsed["encryption"]
        }
        
        if parsed["protocol"] == "vmess":
            user_config["security"] = parsed.get("security", "auto")
        
        outbound = {
            "protocol": parsed["protocol"],
            "settings": {
                "vnext": [
                    {
                        "address": parsed["address"],
                        "port": parsed["port"],
                        "users": [user_config]
                    }
                ]
            },
            "streamSettings": parsed["streamSettings"]
        }
        
        return {
            "log": {"loglevel": "warning"},
            "inbounds": [
                {
                    "listen": "127.0.0.1",
                    "port": self.socks_port,
                    "protocol": "socks",
                    "settings": {"auth": "noauth", "udp": True}
                },
                {
                    "listen": "127.0.0.1",
                    "port": self.http_port,
                    "protocol": "http",
                    "settings": {"auth": "noauth"}
                }
            ],
            "outbounds": [outbound, {"protocol": "freedom", "tag": "direct"}]
        }
    
    def start_v2ray_with_config(self, config):
        """Start V2Ray with specific config"""
        with self.lock:
            self.stop_v2ray()
            
            if not self.v2ray_cmd:
                print("❌ V2Ray/Xray not installed!")
                return False
            
            self.current_config = config
            self.current_config_file = config.get('_file')
            
            parsed = self.parse_config(config)
            if not parsed:
                return False
            
            print(f"🔄 កំពុងប្រើ V2Ray: {config.get('_file')} - {config.get('remark', 'Unknown')}")
            print(f"   Server: {parsed['address']}:{parsed['port']}")
            print(f"   Protocol: {parsed['protocol']}")
            
            runtime = self.build_runtime_config(parsed)
            
            with open('/tmp/v2ray_config.json', 'w') as f:
                json.dump(runtime, f, indent=2)
            
            try:
                self.v2ray_process = subprocess.Popen(
                    [self.v2ray_cmd, 'run', '-config', '/tmp/v2ray_config.json'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                time.sleep(3)
                
                if self.check_port():
                    print(f"   ✅ V2Ray started successfully!")
                    return True
                else:
                    print(f"   ⚠️ V2Ray started but port not open")
                    return True
                    
            except FileNotFoundError:
                print("❌ V2Ray not found! Please install V2Ray first.")
                print("   Termux: pkg install v2ray")
                print("   Ubuntu: sudo apt install v2ray")
                return False
            except Exception as e:
                print(f"❌ Failed to start V2Ray: {e}")
                return False
    
    def start_v2ray_for_account(self, account_file):
        """Start V2Ray based on account file name (acc1.json -> v2ray_1.json)"""
        match = re.search(r'acc(\d+)\.json', account_file)
        if match:
            index = int(match.group(1))
            for cfg in self.configs:
                if cfg.get('_index') == index:
                    return self.start_v2ray_with_config(cfg)
        
        # If no match, try all configs
        for cfg in self.configs:
            if self.start_v2ray_with_config(cfg):
                return True
        
        print(f"⚠️ No V2Ray config found for {account_file}")
        return False
    
    def start_random_v2ray(self):
        """Start V2Ray with random config"""
        if not self.configs:
            return False
        return self.start_v2ray_with_config(random.choice(self.configs))
    
    def stop_v2ray(self):
        """Stop V2Ray process"""
        if self.v2ray_process:
            try:
                self.v2ray_process.terminate()
                time.sleep(1)
                if self.v2ray_process.poll() is None:
                    self.v2ray_process.kill()
                self.v2ray_process = None
                print("   🛑 V2Ray stopped")
            except:
                pass
    
    def check_port(self):
        """Check if proxy port is open"""
        try:
            s = socket.create_connection(("127.0.0.1", self.socks_port), timeout=3)
            s.close()
            return True
        except:
            return False
    
    def get_direct_ip(self):
        """Get direct IP (without proxy)"""
        try:
            response = requests.get('https://api.ipify.org', timeout=10)
            return response.text
        except:
            return "Unknown"
    
    def get_current_ip(self):
        """Get current IP address through proxy"""
        try:
            proxies = {
                'http': f'socks5://127.0.0.1:{self.socks_port}',
                'https': f'socks5://127.0.0.1:{self.socks_port}'
            }
            response = requests.get('https://api.ipify.org', proxies=proxies, timeout=10)
            return response.text
        except:
            return "Unknown"
    
    def test_proxy(self):
        """Test if proxy is working"""
        direct = self.get_direct_ip()
        proxy = self.get_current_ip()
        
        print(f"   🌍 Direct IP: {direct}")
        print(f"   🌐 Proxy IP: {proxy}")
        
        if proxy != direct and proxy != "Unknown" and proxy != "ERROR":
            print("   ✅ IP CHANGED SUCCESS")
            return True
        else:
            print("   ❌ IP NOT CHANGED")
            return False
    
    def get_proxy_dict(self):
        """Get proxy dictionary for Playwright"""
        return {
            'server': f'socks5://127.0.0.1:{self.socks_port}'
        }
    
    def get_proxy_string(self):
        """Get proxy string for curl/wget"""
        return f'socks5://127.0.0.1:{self.socks_port}'
    
    def rotate_ip(self):
        """Rotate to a different V2Ray config"""
        if len(self.configs) <= 1:
            print("⚠️ Only one config available, cannot rotate")
            return False
        
        current_index = 0
        if self.current_config:
            for i, cfg in enumerate(self.configs):
                if cfg.get('_file') == self.current_config.get('_file'):
                    current_index = i
                    break
        
        new_index = current_index
        while new_index == current_index:
            new_index = random.randint(0, len(self.configs) - 1)
        
        print(f"🔄 Rotating IP: switching to config {new_index + 1}")
        return self.start_v2ray_with_config(self.configs[new_index])
    
    def get_all_configs_summary(self):
        """Get summary of all configs"""
        summary = []
        for cfg in self.configs:
            summary.append({
                'file': cfg.get('_file'),
                'index': cfg.get('_index'),
                'remark': cfg.get('remark'),
                'server': cfg.get('server', 'Unknown'),
                'protocol': cfg.get('protocol', 'Unknown')
            })
        return summary
    
    def is_running(self):
        """Check if V2Ray is currently running"""
        return self.v2ray_process is not None and self.v2ray_process.poll() is None
    
    def cleanup(self):
        """Clean up V2Ray process"""
        self.stop_v2ray()