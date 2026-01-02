# EvilGen - Universal Phishlet Generator

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Kali-lightgrey)
![Warning](https://img.shields.io/badge/WARNING-For%20Authorized%20Use%20Only-red)

**Author: Conscience Ekhomwandolor**  
**Tool Category: Security Research & Education**

> ⚠️ **ETHICAL BOUNDARY WARNING:** This tool is strictly for authorized security testing, education, and defensive research in controlled lab environments. Unauthorized use against systems you don't own or lack explicit written permission to test is illegal and unethical.

---

## 📋 Table of Contents
- [Overview](#overview)
- [⚠️ Critical Ethical Warning](#-critical-ethical-warning)
- [Features](#features)
- [Supported Evilginx Versions](#supported-evilginx-versions)
- [Installation](#installation)
- [Usage](#usage)
- [Tool Architecture](#tool-architecture)
- [Output Files](#output-files)
- [Detection & Defense](#detection--defense)
- [CEH Exam Relevance](#ceh-exam-relevance)
- [Legal & Compliance](#legal--compliance)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Disclaimer](#disclaimer)

---

## Overview

EvilGen is an advanced, universal phishlet generator that automates the analysis of login flows and creates compatible phishlets for Evilginx versions 1, 2, and 3. Built for ethical hackers, security researchers, and penetration testers, EvilGen transforms manual reconnaissance into an automated, intelligent process.

**Purpose:** To understand and document modern phishing techniques for defensive security research and authorized penetration testing.

---

## ⚠️ Critical Ethical Warning

### **STRICT USAGE BOUNDARIES:**

```text
████████████████████████████████████████████████████████████████████████████████
█                                                                              █
█  EVILGEN IS A DUAL-USE TOOL                                                  █
█                                                                              █
█  APPROVED USES:                                                              █
█  ✓ Authorized penetration testing with written consent                       █
█  ✓ Security research in isolated lab environments                            █
█  ✓ Defensive security training and education                                 █
█  ✓ Developing detection and prevention mechanisms                            █
█                                                                              █
█  PROHIBITED USES:                                                            █
█  ✗ Unauthorized testing of any system                                        █
█  ✗ Real-world phishing attacks                                               █
█  ✗ Testing systems you don't own or control                                  █
█  ✗ Bypassing organizational security policies                                █
█                                                                              █
█  LEGAL REQUIREMENTS:                                                         █
█  • Written authorization for ALL targets                                     █
█  • Isolated, controlled lab environments only                                █
█  • Ownership of ALL test accounts and systems                                █
█  • Compliance with local, national, and international laws                   █
█  • Full documentation and audit trails                                       █
█                                                                              █
████████████████████████████████████████████████████████████████████████████████
```

**By using EvilGen, you agree to:**
1. Use it only for authorized security testing
2. Never target systems without explicit written permission
3. Maintain comprehensive audit logs
4. Report any discovered vulnerabilities responsibly
5. Use knowledge gained to improve security defenses

---

## Features

### 🔬 **Advanced Analysis Capabilities**
- **Automated Login Flow Analysis**: Intelligently detects and analyzes authentication mechanisms
- **Multi-Version Support**: Generates phishlets for Evilginx 1.x, 2.x, and 3.x
- **Smart Field Detection**: Automatically identifies username, password, CSRF tokens, and 2FA fields
- **Traffic Interception**: Uses BrowserMob Proxy to capture real-time HTTP/HTTPS traffic
- **JavaScript Analysis**: Examines client-side authentication logic
- **Cookie Intelligence**: Detects session cookies, HttpOnly flags, and secure attributes

### 🛠️ **Tool Features**
- **Interactive Wizard**: User-friendly CLI interface with guided setup
- **Batch Processing**: Support for analyzing multiple targets
- **Auto-Installation**: One-click setup script for all dependencies
- **Compatibility Testing**: Built-in validation for generated phishlets
- **Defense Notes**: Includes detection methods and prevention strategies
- **Audit Trail**: Comprehensive logging for compliance and documentation

### 📊 **Output Generation**
- **Structured YAML**: Clean, well-commented phishlet files
- **Installation Guides**: Step-by-step instructions for each Evilginx version
- **Detection Rules**: Suricata/Snort rules to detect the attack
- **Summary Reports**: Detailed analysis of discovered vulnerabilities
- **Ethical Guidelines**: Built-in reminders and compliance documentation

---

## Supported Evilginx Versions

| Version | Status | Key Features Supported |
|---------|--------|------------------------|
| **Evilginx 1.x** | ✅ Fully Supported | Legacy format, simple configuration |
| **Evilginx 2.x** | ✅ Fully Supported | Sub-filters, advanced token capture |
| **Evilginx 3.x** | ✅ Fully Supported | Transformations, enhanced credentials |

---

## Installation

### Quick Install (Recommended)
```bash
# Clone the repository
git clone https://github.com/razielapps/evilgen.git
cd evilgen

# Run the installer
chmod +x install_evilgen.sh
sudo ./install_evilgen.sh
```

### Manual Installation
```bash
# 1. Install system dependencies
sudo apt update
sudo apt install python3 python3-pip chromium-driver default-jre wget unzip -y

# 2. Install Python packages
pip3 install selenium browsermob-proxy pyyaml colorama requests

# 3. Install Chrome and Chromedriver
./scripts/install_chrome.sh

# 4. Download BrowserMob Proxy
./scripts/install_browsermob.sh

# 5. Make scripts executable
chmod +x evilgen.py test_phishlet.py
```

### Verification
```bash
# Test installation
python3 evilgen.py --test

# Check dependencies
python3 scripts/check_dependencies.py
```

---

## Usage

### Interactive Mode (Recommended)
```bash
python3 evilgen.py
```
Follow the interactive prompts:
1. Enter target login URL
2. Select Evilginx version (1, 2, or 3)
3. Choose analysis depth (Basic, Standard, Advanced)
4. Let the tool analyze the login flow
5. Review and test the generated phishlet

### Command Line Mode
```bash
# Basic usage
python3 evilgen.py --url https://lab-target.com/login --version 2 --output target_phishlet.yaml

# Advanced options
python3 evilgen.py \
  --url https://target.com/auth \
  --version 3 \
  --depth advanced \
  --headless \
  --timeout 60 \
  --output results/
```

### Batch Processing
```bash
# Process multiple targets
python3 scripts/batch_process.py --targets targets.txt --version 2
```

### Testing Generated Phishlets
```bash
# Validate phishlet
python3 test_phishlet.py generated/target_com_v2.yaml

# Generate detection rules
python3 scripts/generate_rules.py generated/target_com_v2.yaml
```

---

## Tool Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      EvilGen Core Engine                    │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Target  │  │ Traffic  │  │   DOM    │  │  Cookie  │   │
│  │ Analyzer │  │  Capture │  │  Parser  │  │  Engine  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
├─────────────────────────────────────────────────────────────┤
│                  Version-Specific Generator                 │
│  ┌──────────┐      ┌──────────┐        ┌──────────┐       │
│  │   v1     │      │   v2     │        │   v3     │       │
│  │ Generator│      │ Generator│        │ Generator│       │
│  └──────────┘      └──────────┘        └──────────┘       │
├─────────────────────────────────────────────────────────────┤
│                     Output & Reporting                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  YAML    │  │  Audit   │  │ Detection│  │  Usage   │   │
│  │ Generator│  │   Logs   │  │  Rules   │  │  Guide   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Output Files

EvilGen generates the following files for each analysis:

### **Primary Output:**
- `target_com_v[version].yaml` - Generated phishlet
- `target_com_instructions.txt` - Installation guide
- `target_com_report.md` - Analysis summary

### **Security Files:**
- `detection_target_com.rules` - IDS/IPS rules
- `audit_log_target_com.json` - Compliance audit trail
- `defense_recommendations.md` - Mitigation strategies

### **Example Structure:**
```
evilgen_output/
├── target_com/
│   ├── target_com_v2.yaml
│   ├── target_com_instructions.txt
│   ├── detection_target_com.rules
│   └── audit_log.json
├── target2_org/
└── summary_report.md
```

---

## Detection & Defense

### **What EvilGen Helps You Understand:**
- Modern phishing techniques
- Session hijacking mechanisms
- 2FA bypass vulnerabilities
- Authentication flow weaknesses

### **Generated Defenses:**
```yaml
# Example Suricata rule generated by EvilGen
alert tcp any any -> any 443 (
    msg:"EVILGEN: Potential Evilginx Activity - target.com";
    flow:to_server,established;
    content:"target.com"; http_host;
    pcre:"/(login|auth|account)\.target\.com/i";
    classtype:web-application-attack;
    sid:1000000;
    rev:1;
)
```

### **Defensive Strategies Documented:**
1. **Technical Controls:**
   - Certificate pinning
   - FIDO2/WebAuthn implementation
   - Strict cookie policies
   - CSP headers
   - Subdomain monitoring

2. **User Training:**
   - URL inspection techniques
   - Phishing awareness
   - Reporting procedures

3. **Monitoring:**
   - Anomaly detection
   - Geographic login analysis
   - Session token monitoring

---

## CEH Exam Relevance

### **Demonstrated Skills:**
| CEH Domain | EvilGen Coverage | Exam Relevance |
|------------|------------------|----------------|
| **Reconnaissance** | Automated target analysis | Phase 1 techniques |
| **Scanning** | Protocol and service analysis | Tool proficiency |
| **Gaining Access** | Authentication bypass research | Attack vector understanding |
| **Maintaining Access** | Session hijacking analysis | Persistence mechanisms |
| **Covering Tracks** | Log analysis and evasion | Forensics awareness |

### **Key Exam Concepts:**
- **Phishing Frameworks**: Evilginx operational understanding
- **2FA Bypass**: Session cookie theft mechanisms
- **Social Engineering**: Credential harvesting techniques
- **Legal Compliance**: Testing boundaries and authorization
- **Defense Strategies**: Mitigation and prevention controls

**Portfolio Value:** Documenting EvilGen usage demonstrates advanced tool development skills and deep understanding of web authentication security.

---

## Legal & Compliance

### **Required Documentation:**
1. **Authorization Letters**: Written permission for all testing
2. **Scope Documentation**: Clearly defined testing boundaries
3. **Audit Logs**: Complete records of all activities
4. **Findings Reports**: Responsible vulnerability disclosure
5. **Compliance Checks**: Adherence to GDPR, HIPAA, PCI-DSS as applicable

### **Ethical Framework:**
```python
# Built-in ethical compliance checks
class EthicalCompliance:
    REQUIREMENTS = {
        "written_authorization": True,
        "scope_definition": True,
        "lab_environment": True,
        "owned_systems": True,
        "audit_logging": True,
        "responsible_disclosure": True
    }
    
    def verify_compliance(self):
        """Verify all ethical requirements are met"""
        for requirement, met in self.REQUIREMENTS.items():
            if not met:
                raise EthicalViolation(f"Missing: {requirement}")
```

---

## Troubleshooting

### Common Issues:

**Issue**: Chrome/Chromedriver version mismatch  
**Solution**: Run `./scripts/update_chromedriver.sh`

**Issue**: BrowserMob Proxy fails to start  
**Solution**: Ensure Java is installed and port 8080 is free

**Issue**: SSL certificate errors  
**Solution**: Use `--ignore-ssl` flag or install target certificates

**Issue**: Rate limiting or WAF blocking  
**Solution**: Adjust `--delay` between requests and rotate user agents

### Debug Mode:
```bash
python3 evilgen.py --url https://target.com/login --debug --verbose
```

### Logs:
- Application logs: `logs/evilgen.log`
- Audit trails: `audit/` directory
- Session data: `sessions/` directory (encrypted)

---

## Contributing

### **Development Guidelines:**
1. **Ethical First**: All contributions must maintain ethical standards
2. **Security Focus**: Code should improve defensive capabilities
3. **Documentation**: Comprehensive docs for all features
4. **Testing**: Include test cases and validation scripts

### **Code Structure:**
```
evilgen/
├── core/           # Core analysis engine
├── generators/     # Version-specific generators
├── output/         # Output formatters
├── utils/          # Utilities and helpers
├── scripts/        # Installation and helper scripts
└── tests/          # Test suite
```

### **Pull Request Process:**
1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests
4. Update documentation
5. Submit PR with ethical use statement

---

## Disclaimer

### **LEGAL DISCLAIMER:**
```text
EVILGEN - UNIVERSAL PHISHLET GENERATOR
Copyright (c) 2024 Conscience Ekhomwandolor

This tool is provided for educational and authorized security testing 
purposes ONLY. The author assumes NO liability for any misuse of this 
software. Users are solely responsible for ensuring their compliance 
with all applicable laws and regulations.

By using this software, you agree to:
1. Use it only for authorized security testing with explicit permission
2. Never use it for illegal or unauthorized activities
3. Assume all responsibility for your actions
4. Hold the author harmless from any legal consequences

This tool is not intended for:
- Unauthorized penetration testing
- Criminal activities
- Harassment or stalking
- Corporate espionage
- Any activity violating the Computer Fraud and Abuse Act (CFAA) 
  or similar legislation in your jurisdiction

The author condemns all unauthorized and illegal use of this tool.
```

### **Contact:**
For responsible disclosure of vulnerabilities or ethical questions:
- **Author**: Conscience Ekhomwandolor
- **Purpose**: Security Education & Research
- **Ethics**: Strict adherence to authorized use only

---

## 🎯 Final Note

EvilGen represents the cutting edge of defensive security research. By understanding advanced attack vectors, we build better defenses. Use this knowledge responsibly, document your work thoroughly, and always prioritize ethical conduct in all security endeavors.

**Remember:** The true mark of an elite ethical hacker isn't just technical skill—it's unwavering integrity and commitment to making the digital world safer for everyone.

*"With great power comes great responsibility."* - Use yours wisely.

---

**Last Updated**: December 2024  
**Version**: 1.0.0  
**Author**: Conscience Ekhomwandolor  
**Status**: Active Development  
**License**: MIT (with ethical use restrictions)