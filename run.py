from playwright.sync_api import sync_playwright
import json
import time
import random
import os
import socket
import re
import subprocess
import requests
from datetime import datetime

# Import V2RayManager from separate file
from v2ray_manager import V2RayManager


# =============================
# YOUTUBE BOT PRO CLASS
# =============================

class YouTubeBotPro:

    def __init__(self, settings_file="settings.json"):
        self.cookies_dir = "cookies"
        self.view_duration_min = 41
        self.view_duration_max = 60
        self.v2ray_manager = None
        self.load_settings(settings_file)
    
    def load_settings(self, settings_file):
        """Load settings from JSON file"""
        self.settings = {
            "total_views": 20,
            "view_duration_min": 41,
            "view_duration_max": 60,
            "wait_between_views_min": 30,
            "wait_between_views_max": 60,
            "like_chance": 0.3,
            "use_v2ray": True,
            "v2ray_config_pattern": "v2ray_*.json",
            "headless_mode": True,
            "browser_type": "firefox",
            "stealth_mode": True,
            "random_user_agent": True,
            "accounts_file": "working_accounts.txt",
            "video_urls_file": "link_video.txt"
        }
        
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    loaded = json.load(f)
                    self.settings.update(loaded)
                print(f"✅ បានផ្ទុកការកំណត់ពី {settings_file}")
            else:
                print(f"⚠️ រកមិនឃើញ {settings_file} ប្រើការកំណត់លំនាំដើម")
        except Exception as e:
            print(f"⚠️ មិនអាចផ្ទុក settings: {e}")
        
        self.view_duration_min = self.settings.get("view_duration_min", 41)
        self.view_duration_max = self.settings.get("view_duration_max", 60)
        
        if self.settings.get("use_v2ray", False):
            self.init_v2ray()
    
    def init_v2ray(self):
        """Initialize V2Ray manager"""
        try:
            config_pattern = self.settings.get("v2ray_config_pattern", "v2ray_*.json")
            self.v2ray_manager = V2RayManager(config_pattern)
            if not self.v2ray_manager.configs:
                print("⚠️ No V2Ray config files found. Disabling V2Ray.")
                self.settings["use_v2ray"] = False
            else:
                print(f"✅ V2Ray ready with {len(self.v2ray_manager.configs)} configs")
        except Exception as e:
            print(f"❌ Failed to initialize V2Ray: {e}")
            self.settings["use_v2ray"] = False
    
    def get_proxy_config(self):
        """Get proxy configuration for browser"""
        if self.settings.get("use_v2ray", False) and self.v2ray_manager and self.v2ray_manager.is_running():
            return self.v2ray_manager.get_proxy_dict()
        return None
    
    def check_internet(self):
        """Check if internet is available"""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

    def wait_for_internet(self):
        """Wait until internet is back"""
        print("⚠️ Internet ដាច់! កំពុងរង់ចាំ...")
        while not self.check_internet():
            time.sleep(5)
            print("🔄 កំពុងពិនិត្យ Internet...")
        print("✅ Internet បានត្រឡប់មកវិញ!")

    def get_random_viewport(self):
        """Get random viewport size"""
        viewports = [
            {'width': 1366, 'height': 768},
            {'width': 1920, 'height': 1080},
            {'width': 1536, 'height': 864},
            {'width': 1280, 'height': 720},
            {'width': 1440, 'height': 900},
            {'width': 1600, 'height': 900}
        ]
        return random.choice(viewports)

    def get_random_timezone(self):
        """Get random timezone"""
        timezones = [
            'America/New_York', 'America/Los_Angeles', 'America/Chicago',
            'Europe/London', 'Europe/Paris', 'Asia/Tokyo', 'Asia/Singapore',
            'Australia/Sydney', 'Asia/Bangkok', 'Asia/Phnom_Penh'
        ]
        return random.choice(timezones)

    def get_random_locale(self):
        """Get random locale"""
        locales = ['en-US', 'en-GB', 'en-CA', 'en-AU', 'fr-FR', 'de-DE', 'es-ES']
        return random.choice(locales)

    def add_stealth_scripts(self, page):
        """Add stealth scripts to avoid detection"""
        if not self.settings.get("stealth_mode", True):
            return
            
        stealth_script = """
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        window.chrome = { runtime: {}, loadTimes: function() {}, csi: function() {}, app: {} };
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        Object.defineProperty(navigator, 'headless', { get: () => false });
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) return 'Intel Inc.';
            if (parameter === 37446) return 'Intel Iris OpenGL Engine';
            return getParameter(parameter);
        };
        """
        page.add_init_script(stealth_script)

    def random_human_behavior(self, page):
        """Human-like behavior"""
        actions = [
            lambda: page.mouse.wheel(0, random.randint(100, 500)),
            lambda: page.mouse.move(random.randint(100, 800), random.randint(100, 600)),
            lambda: page.keyboard.press('ArrowDown'),
            lambda: page.keyboard.press('ArrowUp'),
            lambda: time.sleep(random.uniform(0.5, 2)),
            lambda: page.evaluate("window.scrollBy(0, 100)"),
            lambda: page.evaluate("window.scrollBy(0, -50)")
        ]
        for _ in range(random.randint(1, 3)):
            if random.random() > 0.6:
                random.choice(actions)()
                time.sleep(random.uniform(0.5, 1.5))

    def random_mouse_movement(self, page):
        """Simulate realistic mouse movement"""
        for _ in range(random.randint(2, 5)):
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            page.mouse.move(x, y)
            time.sleep(random.uniform(0.1, 0.5))

    def get_real_user_agent(self):
        """Generate real user agent"""
        if not self.settings.get("random_user_agent", True):
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        return random.choice(user_agents)

    def get_available_accounts(self):
        """Get list of existing account files"""
        available_accounts = []
        if os.path.exists(self.cookies_dir):
            for file in os.listdir(self.cookies_dir):
                if file.endswith('.json') and not file.endswith('.backup') and not file.endswith('.session'):
                    available_accounts.append(file)
        return available_accounts

    def clean_cookie(self, cookie):
        """Clean cookie fields"""
        forbidden_fields = ['partitionKey', 'partitionKeyPercentEncoded', 'id', 'storeId', 'sameParty']
        cleaned_cookie = {}
        for key, value in cookie.items():
            if key not in forbidden_fields:
                if key == 'sameSite' and value not in ['Strict', 'Lax', 'None']:
                    value = 'Lax'
                if key == 'domain' and value and not value.startswith('.') and 'youtube.com' in value:
                    value = '.' + value
                cleaned_cookie[key] = value
        return cleaned_cookie

    def load_cookies(self, context, file):
        """Load and clean cookies from file"""
        try:
            with open(f"{self.cookies_dir}/{file}", 'r') as f:
                cookies = json.load(f)
            cleaned_cookies = [self.clean_cookie(c) for c in cookies]
            context.add_cookies(cleaned_cookies)
            print(f"🍪 បានផ្ទុកខូគី {len(cleaned_cookies)} ពី {file}")
            return True
        except Exception as e:
            print(f"⚠️ មិនអាចផ្ទុកខូគីពី {file}: {e}")
            return False

    def verify_login(self, page):
        """Verify login status"""
        try:
            page.wait_for_selector("button#avatar-btn, ytd-topbar-menu-button-renderer button", timeout=8000)
            print("✓ រកឃើញប៊ូតុងគណនី")
            return True
        except:
            print("✗ មិនឃើញប៊ូតុងចូលប្រព័ន្ធ")
            return False

    def verify_video_playing(self, page):
        """Verify video is playing"""
        try:
            page.wait_for_selector("video", timeout=10000)
            t1 = page.evaluate("() => document.querySelector('video')?.currentTime || 0")
            time.sleep(3)
            t2 = page.evaluate("() => document.querySelector('video')?.currentTime || 0")
            if t2 > t1:
                print(f"▶️ កំពុងចាក់វីដេអូ ({t1:.1f} → {t2:.1f})")
                return True
            else:
                page.evaluate("() => { const v = document.querySelector('video'); if(v) v.play(); }")
                return True
        except Exception as e:
            print(f"⚠️ វីដេអូ: {e}")
            return False

    def watch_video(self, page, url, account_name):
        """Watch video with full protection"""
        view_duration = random.randint(self.view_duration_min, self.view_duration_max)
        print(f"⏱️ រយៈពេលមើល: {view_duration} វិនាទី")

        if not self.check_internet():
            self.wait_for_internet()

        if 'youtu.be' in url:
            video_id = url.split('/')[-1].split('?')[0]
            url = f"https://www.youtube.com/watch?v={video_id}"
            print(f"🔄 បានប្តូរ URL: {url}")

        time.sleep(random.uniform(1, 3))

        for attempt in range(3):
            try:
                print(f"📺 កំពុងបើកវីដេអូ...")
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                break
            except Exception as e:
                print(f"⚠️ បរាជ័យលើកទី {attempt+1}: {e}")
                if attempt < 2:
                    if not self.check_internet():
                        self.wait_for_internet()
                    else:
                        time.sleep(5)
                else:
                    return False

        for _ in range(random.randint(1, 3)):
            page.mouse.wheel(0, random.randint(200, 500))
            time.sleep(random.uniform(0.5, 1))

        time.sleep(3)
        page.evaluate("() => { const v = document.querySelector('video'); if(v) v.play(); }")
        time.sleep(random.uniform(1, 2))
        self.verify_video_playing(page)

        watched = 0
        start_time = time.time()

        while watched < view_duration:
            if not self.check_internet():
                self.wait_for_internet()
                page.reload()
                time.sleep(5)
                page.evaluate("() => { const v = document.querySelector('video'); if(v) v.play(); }")
            
            if random.random() > 0.5:
                self.random_human_behavior(page)
            
            if random.random() > 0.7:
                self.random_mouse_movement(page)
            
            sleep_time = random.randint(4, 8)
            time.sleep(sleep_time)
            watched += sleep_time
            elapsed = int(time.time() - start_time)
            print(f"⏱ កំពុងមើល: {elapsed}s / {view_duration}s")

        if random.random() > (1 - self.settings.get("like_chance", 0.3)):
            try:
                time.sleep(random.uniform(1, 3))
                page.click("button[aria-label*='like']", timeout=3000)
                print(f"👍 {account_name} បានចុច Like")
            except:
                pass

        for _ in range(random.randint(1, 2)):
            page.mouse.wheel(0, random.randint(100, 300))
            time.sleep(random.uniform(0.5, 1))

        print(f"✅ {account_name} បានមើលវីដេអូចប់!")
        return True

    def run_account(self, playwright, account_file, url, view_number):
        """Run bot for a single account"""
        print(f"\n📱 កំពុងប្រើអាខោន: {account_file}")
        
        if self.settings.get("use_v2ray", False) and self.v2ray_manager:
            print(f"🔄 Starting V2Ray for {account_file}...")
            if self.v2ray_manager.start_v2ray_for_account(account_file):
                time.sleep(2)
                current_ip = self.v2ray_manager.get_current_ip()
                direct_ip = self.v2ray_manager.get_direct_ip()
                print(f"   Direct IP: {direct_ip}")
                print(f"   Proxy IP: {current_ip}")
                if current_ip != direct_ip and current_ip != "Unknown":
                    print(f"   ✅ IP CHANGED successfully!")
                else:
                    print(f"   ⚠️ IP not changed. V2Ray may not be working properly.")
            else:
                print(f"   ⚠️ Failed to start V2Ray for {account_file}")

        if not self.check_internet():
            self.wait_for_internet()

        time.sleep(random.uniform(2, 5))

        proxy_config = self.get_proxy_config()
        browser_type = self.settings.get("browser_type", "firefox")
        
        browser_args = [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled'
        ]
        
        if proxy_config:
            print(f"🌐 Using proxy: {proxy_config.get('server')}")
            if browser_type == "firefox":
                browser = playwright.firefox.launch(
                    headless=self.settings.get("headless_mode", True),
                    args=browser_args,
                    proxy=proxy_config
                )
            elif browser_type == "chromium":
                browser = playwright.chromium.launch(
                    headless=self.settings.get("headless_mode", True),
                    args=browser_args,
                    proxy=proxy_config
                )
            else:
                browser = playwright.webkit.launch(
                    headless=self.settings.get("headless_mode", True)
                )
        else:
            if browser_type == "firefox":
                browser = playwright.firefox.launch(
                    headless=self.settings.get("headless_mode", True),
                    args=browser_args
                )
            elif browser_type == "chromium":
                browser = playwright.chromium.launch(
                    headless=self.settings.get("headless_mode", True),
                    args=browser_args
                )
            else:
                browser = playwright.webkit.launch(
                    headless=self.settings.get("headless_mode", True)
                )

        real_user_agent = self.get_real_user_agent() if self.settings.get("random_user_agent", True) else None
        
        context_options = {
            'viewport': self.get_random_viewport(),
            'locale': self.get_random_locale(),
            'timezone_id': self.get_random_timezone(),
            'ignore_https_errors': True,
            'java_script_enabled': True,
            'extra_http_headers': {
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        }
        
        if real_user_agent:
            context_options['user_agent'] = real_user_agent
        
        context = browser.new_context(**context_options)
        
        if not self.load_cookies(context, account_file):
            browser.close()
            return False

        page = context.new_page()
        self.add_stealth_scripts(page)
        self.random_mouse_movement(page)
        
        if not self.check_internet():
            self.wait_for_internet()
        
        print("🌐 កំពុងបើក YouTube...")
        time.sleep(random.uniform(1, 3))
        
        for attempt in range(3):
            try:
                page.goto("https://www.youtube.com", wait_until="domcontentloaded", timeout=30000)
                time.sleep(random.uniform(3, 6))
                break
            except Exception as e:
                print(f"⚠️ បរាជ័យលើកទី {attempt+1}: {e}")
                if attempt < 2:
                    if not self.check_internet():
                        self.wait_for_internet()
                    else:
                        time.sleep(5)
                else:
                    browser.close()
                    return False

        self.random_human_behavior(page)
        self.random_mouse_movement(page)

        if not self.verify_login(page):
            print(f"❌ {account_file} ចូលប្រព័ន្ធមិនជោគជ័យ")
            browser.close()
            return False

        print(f"✅ {account_file} បានចូលប្រព័ន្ធដោយជោគជ័យ")
        time.sleep(random.uniform(2, 4))
        
        success = self.watch_video(page, url, account_file)
        
        time.sleep(random.uniform(2, 5))
        browser.close()
        return success

    def get_video_url(self):
        """Read video URL from file"""
        video_urls_file = self.settings.get("video_urls_file", "link_video.txt")
        try:
            if os.path.exists(video_urls_file):
                with open(video_urls_file, 'r') as f:
                    urls = [line.strip() for line in f.readlines() if line.strip()]
                valid_urls = []
                for url in urls:
                    if 'youtu.be' in url or 'youtube.com' in url:
                        if '?' in url:
                            url = url.split('?')[0]
                        valid_urls.append(url)
                if valid_urls:
                    selected_url = random.choice(valid_urls)
                    print(f"📹 បានរកឃើញ URL {len(valid_urls)} បន្ទាត់")
                    print(f"🎯 ជ្រើសរើស URL: {selected_url}")
                    return selected_url
            return None
        except Exception as e:
            print(f"❌ មិនអាចអាន URL: {e}")
            return None

    def get_working_accounts(self):
        """Get list of working accounts"""
        accounts_file = self.settings.get("accounts_file", "working_accounts.txt")
        if os.path.exists(accounts_file):
            with open(accounts_file, 'r') as f:
                accounts = [line.strip() for line in f.readlines() if line.strip()]
            if accounts:
                print(f"📋 ប្រើបញ្ជីអាខោនពី {accounts_file}: {len(accounts)} អាខោន")
                return accounts
        
        all_accounts = self.get_available_accounts()
        print(f"📋 រកឃើញអាខោនសរុប: {len(all_accounts)}")
        return all_accounts

    def cleanup(self):
        """Clean up resources"""
        if self.v2ray_manager:
            self.v2ray_manager.cleanup()
            print("✅ V2Ray cleaned up")

    def run(self):
        """Main execution loop"""
        total_views = self.settings.get("total_views", 20)
        
        print("="*60)
        print("🤖 YOUTUBE VIEW BOT")
        print("="*60)
        print(f"🛡️ Anti-Bot: {'ON' if self.settings.get('stealth_mode', True) else 'OFF'}")
        print(f"🌐 Browser: {self.settings.get('browser_type', 'firefox')}")
        print(f"🔌 V2Ray: {'ON' if self.settings.get('use_v2ray', False) else 'OFF'}")
        print(f"🎯 Total Views: {total_views}")
        print("="*60)
        
        if self.settings.get("use_v2ray", False) and self.v2ray_manager:
            print("\n📡 V2Ray Configs Available:")
            for cfg in self.v2ray_manager.get_all_configs_summary():
                print(f"   {cfg['file']} -> {cfg['server']}:{cfg['protocol']}")
        
        video_url = self.get_video_url()
        if not video_url:
            print("\n❌ មិនអាចបន្តដំណើរការបានដោយសារគ្មាន URL វីដេអូ")
            print("💡 សូមបង្កើតឯកសារ link_video.txt ដែលមាន URL វីដេអូ")
            return
        
        available_accounts = self.get_working_accounts()
        
        if not available_accounts:
            print("❌ រកមិនឃើញអាខោនណាមួយ!")
            print("💡 សូមប្រាកដថាមានឯកសារ .json ក្នុងថត cookies/")
            return
        
        print(f"\n📋 អាខោនដែលអាចប្រើបាន: {len(available_accounts)}")
        for i, acc in enumerate(available_accounts[:10], 1):
            print(f"   {i}. {acc}")
        if len(available_accounts) > 10:
            print(f"   ... និង {len(available_accounts) - 10} អាខោនផ្សេងទៀត")
        
        selected_accounts = []
        for i in range(total_views):
            selected_accounts.append(available_accounts[i % len(available_accounts)])
        
        print("\n" + "="*60)
        print("🚀 ចាប់ផ្តើមដំណើរការ...")
        print("="*60)
        
        try:
            with sync_playwright() as p:
                success = 0
                fail = 0
                account_stats = {}
                
                for i, account_file in enumerate(selected_accounts[:total_views], 1):
                    print("\n" + "="*50)
                    print(f"🎯 VIEW {i}/{total_views}")
                    print(f"👤 អាខោន: {account_file}")
                    
                    rotation_count = (i - 1) // len(available_accounts)
                    if rotation_count > 0:
                        print(f"🔄 វដ្តទី: {rotation_count + 1}")
                    
                    start_time = time.time()
                    result = self.run_account(p, account_file, video_url, i)
                    elapsed_time = int(time.time() - start_time)
                    
                    if result:
                        success += 1
                        account_stats[account_file] = account_stats.get(account_file, 0) + 1
                        print(f"✅ View {i} បានសម្រេច (ចំណាយពេល {elapsed_time}s)")
                    else:
                        fail += 1
                        print(f"❌ View {i} បរាជ័យ (ចំណាយពេល {elapsed_time}s)")
                    
                    if i < total_views:
                        wait_min = self.settings.get("wait_between_views_min", 30)
                        wait_max = self.settings.get("wait_between_views_max", 60)
                        wait = random.randint(wait_min, wait_max)
                        print(f"\n⏳ រង់ចាំ {wait} វិនាទី មុនបន្ត...")
                        time.sleep(wait)
                
                print("\n" + "="*60)
                print("📊 លទ្ធផលចុងក្រោយ")
                print("="*60)
                print(f"✅ ជោគជ័យ: {success}/{total_views} views")
                print(f"❌ បរាជ័យ: {fail}/{total_views} views")
                print(f"📈 អត្រាជោគជ័យ: {(success/total_views)*100:.1f}%")
                
                if success > 0 and account_stats:
                    print(f"\n📝 ស្ថិតិតាមអាខោន:")
                    for account, count in sorted(account_stats.items(), key=lambda x: x[1], reverse=True):
                        print(f"   {account}: {count} views")
                
                print("="*60)
                
        finally:
            self.cleanup()


# =============================
# RUN
# =============================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("📌 YOUTUBE VIEW BOT WITH V2RAY IP ROTATION")
    print("="*60)
    print("\nមុនពេលចាប់ផ្តើម សូមប្រាកដថា:")
    print("   1. មានឯកសារ link_video.txt ដែលមាន URL វីដេអូ")
    print("   2. មានថត cookies/ ដែលមាន acc1.json, acc2.json, ...")
    print("   3. មានឯកសារ v2ray_1.json, v2ray_2.json, ...")
    print("   4. V2Ray បានដំឡើងរួច: pkg install v2ray")
    print("="*60)
    
    bot = YouTubeBotPro()
    
    confirm = y print("បានបោះបង់ការដំណើរការ!")