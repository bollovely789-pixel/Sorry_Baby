#!/usr/bin/env python3
import subprocess
import json
import time
import requests
import glob
import re
import sys

class V2RayTester:
    def __init__(self):
        self.socks_port = 10808
        self.http_port = 10809
        self.v2ray_process = None
        self.v2ray_cmd = None
        self.detect_v2ray()
    
    def detect_v2ray(self):
        """Detect V2Ray or Xray command"""
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
                print("✅ Found Xray")
                return
        except:
            pass
        
        print("❌ V2Ray/Xray not found!")
        print("Please install: pkg install v2ray")
        sys.exit(1)
    
    def stop_v2ray(self):
        """Stop V2Ray process"""
        if self.v2ray_process:
            try:
                self.v2ray_process.terminate()
                time.sleep(1)
                if self.v2ray_process.poll() is None:
                    self.v2ray_process.kill()
            except:
                pass
            self.v2ray_process = None
    
    def start_v2ray(self, config_file):
        """Start V2Ray with specific config"""
        self.stop_v2ray()
        
        print(f"\n🔄 Starting V2Ray with: {config_file}")
        
        try:
            self.v2ray_process = subprocess.Popen(
                [self.v2ray_cmd, 'run', '-config', config_file],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(4)
            return True
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return False
    
    def get_ip_through_proxy(self):
        """Get IP address through proxy"""
        try:
            proxies = {
                'http': f'socks5://127.0.0.1:{self.socks_port}',
                'https': f'socks5://127.0.0.1:{self.socks_port}'
            }
            response = requests.get('https://api.ipify.org', proxies=proxies, timeout=10)
            return response.text
        except Exception as e:
            return f"ERROR"
    
    def get_direct_ip(self):
        """Get direct IP address (without proxy)"""
        try:
            response = requests.get('https://api.ipify.org', timeout=10)
            return response.text
        except:
            return "Unknown"
    
    def test_config(self, config_file):
        """Test a single V2Ray config"""
        print("\n" + "="*60)
        print(f"📡 Testing: {config_file}")
        print("="*60)
        
        # Get direct IP first
        direct_ip = self.get_direct_ip()
        print(f"🌍 Direct IP: {direct_ip}")
        
        # Start V2Ray with this config
        if not self.start_v2ray(config_file):
            print(f"   ❌ Failed to start V2Ray")
            return False
        
        # Get IP through proxy
        proxy_ip = self.get_ip_through_proxy()
        print(f"🌐 Proxy IP: {proxy_ip}")
        
        # Check if working
        if "ERROR" in proxy_ip:
            print(f"   ❌ Cannot connect through proxy")
            return False
        elif proxy_ip != direct_ip:
            print(f"   ✅ SUCCESS! IP changed from {direct_ip} to {proxy_ip}")
            return True
        else:
            print(f"   ❌ FAILED! IP not changed (still {direct_ip})")
            return False
    
    def test_all_configs(self):
        """Test all v2ray_*.json files"""
        config_files = glob.glob("v2ray_*.json")
        config_files.sort()
        
        if not config_files:
            print("❌ No v2ray_*.json files found!")
            return []
        
        print("\n" + "="*60)
        print("🔍 TESTING ALL V2RAY CONFIGS")
        print("="*60)
        print(f"Found {len(config_files)} config files\n")
        
        working_configs = []
        
        for config_file in config_files:
            # Extract remark from file
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    remark = config.get('remarks', config.get('remark', config_file))
            except:
                remark = config_file
            
            print(f"\n📁 Config: {config_file}")
            print(f"   Remark: {remark}")
            
            if self.test_config(config_file):
                working_configs.append(config_file)
            
            # Stop V2Ray before next test
            self.stop_v2ray()
            time.sleep(1)
        
        # Summary
        print("\n" + "="*60)
        print("📊 SUMMARY")
        print("="*60)
        print(f"Total configs: {len(config_files)}")
        print(f"Working configs: {len(working_configs)}")
        
        if working_configs:
            print("\n✅ Working configs:")
            for cfg in working_configs:
                print(f"   - {cfg}")
        else:
            print("\n❌ No working configs found!")
        
        return working_configs

if __name__ == "__main__":
    tester = V2RayTester()
    
    print("\n" + "="*60)
    print("🔧 V2RAY CONFIG TESTER")
    print("="*60)
    print("\nThis tool will test which V2Ray configs work")
    print("and can change your IP address.\n")
    
    tester.test_all_configs()
    
    # Cleanup
    tester.stop_v2ray()
    print("\n✅ Done!")
