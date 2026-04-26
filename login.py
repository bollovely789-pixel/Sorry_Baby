from playwright.sync_api import sync_playwright
import json
import os
import time

class YouTubeLoginChecker:
    
    def __init__(self):
        self.cookies_dir = "cookies"
        
    def clean_cookie(self, cookie):
        """Remove problematic fields from cookie"""
        # Fields that cause issues in Playwright
        forbidden_fields = ['partitionKey', 'partitionKeyPercentEncoded', 'id', 'storeId', 'sameParty']
        
        cleaned_cookie = {}
        for key, value in cookie.items():
            if key not in forbidden_fields:
                # Fix sameSite value
                if key == 'sameSite':
                    if value not in ['Strict', 'Lax', 'None']:
                        value = 'Lax'
                # Ensure domain starts with dot for YouTube
                if key == 'domain' and value and not value.startswith('.'):
                    if 'youtube.com' in value:
                        value = '.' + value
                cleaned_cookie[key] = value
        
        return cleaned_cookie
    
    def load_and_clean_cookies(self, file_path):
        """Load and clean cookies from file"""
        try:
            with open(file_path, 'r') as f:
                cookies = json.load(f)
            
            cleaned_cookies = []
            for cookie in cookies:
                cleaned_cookie = self.clean_cookie(cookie)
                cleaned_cookies.append(cleaned_cookie)
            
            return cleaned_cookies
        except Exception as e:
            print(f"❌ Error loading cookies: {e}")
            return None
    
    def check_login(self, account_file):
        """Check if account is logged in"""
        print(f"\n{'='*50}")
        print(f"🔍 កំពុងពិនិត្យអាខោន: {account_file}")
        print(f"{'='*50}")
        
        file_path = f"{self.cookies_dir}/{account_file}"
        
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"❌ រកមិនឃើញឯកសារ: {file_path}")
            return False
        
        # Check file size
        file_size = os.path.getsize(file_path)
        print(f"📄 ទំហំឯកសារ: {file_size} bytes")
        
        # Load and clean cookies
        cookies = self.load_and_clean_cookies(file_path)
        if not cookies:
            print(f"❌ មិនអាចផ្ទុកខូគីបាន")
            return False
        
        print(f"🍪 ចំនួនខូគី: {len(cookies)}")
        
        # Check for important YouTube cookies
        important_cookies = ['SAPISID', 'APISID', 'SSID', 'HSID', 'LOGIN_INFO']
        found_cookies = []
        for cookie in cookies:
            if cookie.get('name') in important_cookies:
                found_cookies.append(cookie.get('name'))
        
        if found_cookies:
            print(f"✅ រកឃើញខូគីសំខាន់ៗ: {', '.join(found_cookies)}")
        else:
            print(f"⚠️ មិនឃើញខូគីសំខាន់ៗ (អាចនឹងមិនអាច login បាន)")
        
        # Test login with browser
        print("\n🌐 កំពុងសាកល្បងចូលប្រព័ន្ធ...")
        
        try:
            with sync_playwright() as p:
                # Launch browser
                browser = p.firefox.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                
                # Add cleaned cookies
                context.add_cookies(cookies)
                
                # Create page and go to YouTube
                page = context.new_page()
                page.goto("https://www.youtube.com", wait_until="domcontentloaded")
                time.sleep(3)
                
                # Check login status
                login_score = 0
                
                # Method 1: Check for avatar button
                try:
                    page.wait_for_selector("button#avatar-btn, ytd-topbar-menu-button-renderer button", timeout=5000)
                    print("✅ 1. រកឃើញប៊ូតុងរូបតំណាង")
                    login_score += 1
                except:
                    print("❌ 1. មិនឃើញប៊ូតុងរូបតំណាង")
                
                # Method 2: Check for subscriptions link
                try:
                    page.goto("https://www.youtube.com/feed/subscriptions", wait_until="domcontentloaded")
                    time.sleep(2)
                    if "subscriptions" in page.url:
                        print("✅ 2. អាចចូលមើល Subscriptions បាន")
                        login_score += 1
                    else:
                        print("❌ 2. មិនអាចចូល Subscriptions")
                except:
                    print("❌ 2. មិនអាចចូល Subscriptions")
                
                # Method 3: Check for sign out option
                try:
                    page.goto("https://www.youtube.com", wait_until="domcontentloaded")
                    time.sleep(2)
                    page.click("button#avatar-btn, ytd-topbar-menu-button-renderer button", timeout=3000)
                    time.sleep(1)
                    if page.locator("text=Sign out").count() > 0:
                        print("✅ 3. រកឃើញប៊ូតុង Sign out")
                        login_score += 1
                    else:
                        print("❌ 3. មិនឃើញ Sign out")
                except:
                    print("❌ 3. មិនអាចបើកម៉ឺនុយ")
                
                # Get account info
                try:
                    # Try to get channel name
                    channel_name = page.evaluate("""
                        () => {
                            const elements = document.querySelectorAll('#avatar-btn, yt-formatted-string');
                            for (let el of elements) {
                                if (el.textContent && el.textContent.trim().length > 0) {
                                    return el.textContent.trim();
                                }
                            }
                            return null;
                        }
                    """)
                    if channel_name:
                        print(f"📝 ឈ្មោះគណនី: {channel_name[:50]}")
                except:
                    pass
                
                browser.close()
                
                # Final verdict
                print(f"\n{'='*50}")
                if login_score >= 2:
                    print(f"✅ RESULT: {account_file} អាចប្រើបាន (ពិន្ទុ: {login_score}/3)")
                    return True
                elif login_score >= 1:
                    print(f"⚠️ RESULT: {account_file} ប្រើបានកម្រិតមធ្យម (ពិន្ទុ: {login_score}/3)")
                    return True
                else:
                    print(f"❌ RESULT: {account_file} មិនអាចប្រើបាន (ពិន្ទុ: {login_score}/3)")
                    return False
                    
        except Exception as e:
            print(f"❌ មានបញ្ហាក្នុងការសាកល្បង: {e}")
            return False
    
    def fix_cookie_file(self, account_file):
        """Fix cookie file by removing problematic fields"""
        print(f"\n🔧 កំពុងជួសជុលឯកសារ: {account_file}")
        
        file_path = f"{self.cookies_dir}/{account_file}"
        
        try:
            # Load original cookies
            with open(file_path, 'r') as f:
                cookies = json.load(f)
            
            # Clean each cookie
            cleaned_cookies = []
            for cookie in cookies:
                cleaned_cookie = self.clean_cookie(cookie)
                cleaned_cookies.append(cleaned_cookie)
            
            # Backup original
            backup_path = f"{file_path}.backup"
            with open(backup_path, 'w') as f:
                json.dump(cookies, f, indent=2)
            print(f"💾 បានបម្រុងទុកឯកសារដើម: {backup_path}")
            
            # Save cleaned cookies
            with open(file_path, 'w') as f:
                json.dump(cleaned_cookies, f, indent=2)
            print(f"✅ បានជួសជុលឯកសារ: {account_file}")
            print(f"🍪 ចំនួនខូគីដើម: {len(cookies)} → ខូគីថ្មី: {len(cleaned_cookies)}")
            
            return True
            
        except Exception as e:
            print(f"❌ មិនអាចជួសជុលបាន: {e}")
            return False
    
    def check_all_accounts(self, auto_fix=True):
        """Check all accounts in cookies directory"""
        print("\n" + "="*60)
        print("🤖 YOUTUBE LOGIN CHECKER")
        print("="*60)
        
        # Get all account files
        if not os.path.exists(self.cookies_dir):
            print(f"❌ ថត {self.cookies_dir} មិនទាន់មាន")
            os.makedirs(self.cookies_dir)
            print(f"✅ បានបង្កើតថត {self.cookies_dir}")
            return []
        
        account_files = [f for f in os.listdir(self.cookies_dir) if f.endswith('.json') and not f.endswith('.backup')]
        
        if not account_files:
            print(f"❌ រកមិនឃើញឯកសារ .json ក្នុងថត {self.cookies_dir}")
            return []
        
        print(f"\n📋 រកឃើញអាខោនចំនួន: {len(account_files)}")
        for i, acc in enumerate(account_files, 1):
            print(f"   {i}. {acc}")
        
        # Check each account
        results = {}
        working_accounts = []
        broken_accounts = []
        
        for account_file in account_files:
            print(f"\n{'='*50}")
            print(f"📌 កំពុងពិនិត្យ {account_file}")
            print(f"{'='*50}")
            
            # Check if login works
            is_working = self.check_login(account_file)
            
            if is_working:
                working_accounts.append(account_file)
                results[account_file] = "✅ WORKING"
            else:
                broken_accounts.append(account_file)
                results[account_file] = "❌ BROKEN"
                
                # Try to fix if auto_fix is True
                if auto_fix:
                    print(f"\n🔧 ព្យាយាមជួសជុល {account_file}...")
                    if self.fix_cookie_file(account_file):
                        print(f"✅ បានជួសជុលរួច សូមសាកល្បងម្តងទៀត")
                        # Test again after fix
                        is_fixed = self.check_login(account_file)
                        if is_fixed:
                            working_accounts.append(account_file)
                            results[account_file] = "✅ FIXED"
                            broken_accounts.remove(account_file)
            
            # Wait a bit between checks
            time.sleep(2)
        
        # Print summary
        print("\n" + "="*60)
        print("📊 សង្ខេបលទ្ធផល")
        print("="*60)
        print(f"📋 សរុបអាខោន: {len(account_files)}")
        print(f"✅ ប្រើបាន: {len(working_accounts)}")
        print(f"❌ ប្រើមិនបាន: {len(broken_accounts)}")
        
        print("\n📝 បញ្ជីលម្អិត:")
        for account, status in results.items():
            print(f"   {status} - {account}")
        
        if working_accounts:
            print(f"\n💡 អាខោនដែលប្រើបាន: {', '.join(working_accounts)}")
        
        if broken_accounts:
            print(f"\n⚠️ អាខោនដែលមិនប្រើបាន: {', '.join(broken_accounts)}")
            print("💡 សូមដកស្រង់ខូគីថ្មីសម្រាប់អាខោនទាំងនេះ")
        
        print("="*60)
        
        return working_accounts
    
    def export_working_accounts(self, working_accounts):
        """Save list of working accounts to file"""
        if working_accounts:
            with open("working_accounts.txt", "w") as f:
                for account in working_accounts:
                    f.write(f"{account}\n")
            print(f"\n✅ បានរក្សាទុកបញ្ជីអាខោនដែលប្រើបានក្នុងឯកសារ working_accounts.txt")

# =============================
# MAIN
# =============================
if __name__ == "__main__":
    checker = YouTubeLoginChecker()
    
    print("\nជម្រើស:")
    print("1. ពិនិត្យអាខោនទាំងអស់ (នឹងជួសជុលដោយស្វ័យប្រវត្តិ)")
    print("2. ពិនិត្យតែអាខោនមួយ")
    print("3. ជួសជុលឯកសារខូគីតែប៉ុណ្ណោះ")
    
    choice = input("\nជ្រើសរើស (1/2/3): ").strip()
    
    if choice == "1":
        working = checker.check_all_accounts(auto_fix=True)
        checker.export_working_accounts(working)
        
    elif choice == "2":
        account = input("បញ្ចូលឈ្មោះអាខោន (ឧទាហរណ៍: acc1.json): ").strip()
        if checker.check_login(account):
            print(f"\n✅ {account} ប្រើបាន")
        else:
            print(f"\n❌ {account} ប្រើមិនបាន")
            fix = input("ចង់ជួសជុលឯកសារនេះទេ? (y/n): ").strip().lower()
            if fix == 'y':
                checker.fix_cookie_file(account)
                
    elif choice == "3":
        account = input("បញ្ចូលឈ្មោះអាខោនដែលចង់ជួសជុល: ").strip()
        checker.fix_cookie_file(account)
    
    else:
        print("ជម្រើសមិនត្រឹមត្រូវ!")