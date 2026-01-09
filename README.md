# Ash-Vault

**Crisis Archive & Backup Infrastructure**

[![The Alphabet Cartel](https://img.shields.io/badge/Community-The%20Alphabet%20Cartel-purple)](https://discord.gg/alphabetcartel)
[![Website](https://img.shields.io/badge/Website-alphabetcartel.org-blue)](https://alphabetcartel.org)

---

## 🎯 Mission

```
Secure     → Encrypt sensitive session data with defense-in-depth layering
Archive    → Preserve crisis records in resilient object storage
Replicate  → Maintain backups across device, site, and cloud tiers
Protect    → Safeguard our LGBTQIA+ community through vigilant data guardianship
```

---

## 📋 Overview

Ash-Vault provides secure archive storage and backup infrastructure for the [Ash ecosystem](https://github.com/the-alphabet-cartel/ash). Running on the **Syn VM** (named after the Norse goddess who guards doors), it ensures crisis session data is encrypted, preserved, and recoverable.

### Key Features

- **🔐 Defense-in-Depth Encryption**: Application-level AES-256-GCM + ZFS native encryption
- **📦 S3-Compatible Storage**: MinIO object storage for flexible archive access
- **🔄 1-2-3 Backup Strategy**: On-device, same-site, and off-site backups
- **🐍 Python Automation**: APScheduler-based backup service
- **📊 Health Monitoring**: Endpoint for status checks and Discord alerts

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     ODIN HYPERVISOR                              │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │               SYN VM (Debian Trixie)                     │   │
│   │               IP: 10.20.30.202                           │   │
│   │                                                          │   │
│   │   ┌─────────────────────────────────────────────────┐   │   │
│   │   │  ZFS Pool: syn (aes-256-gcm encrypted)          │   │   │
│   │   │  └── syn/archives → /mnt/archives               │   │   │
│   │   └─────────────────────────────────────────────────┘   │   │
│   │                                                          │   │
│   │   ┌──────────────────┐  ┌──────────────────────────┐   │   │
│   │   │ MinIO            │  │ ash-vault-backup         │   │   │
│   │   │ :30884 API       │  │ (Python Service)         │   │   │
│   │   │ :30885 Console   │  │ :30886 Health            │   │   │
│   │   └──────────────────┘  └──────────────────────────┘   │   │
│   └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ TIER 3: Local   │  │ TIER 2: Lofn   │  │ TIER 1: Cloud   │
│ ZFS Snapshots   │  │ ZFS Recv       │  │ Backblaze B2    │
│ Daily 3 AM      │  │ Nightly 4 AM   │  │ Weekly Sun 5 AM │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Hyper-V on Windows 11 (Odin hypervisor)
- Debian Trixie ISO
- Network with DHCP reservation for 10.20.30.202

### Deployment

```bash
# Clone repository
mkdir -p /dockers
cd /dockers
git clone -b v5.0 https://github.com/The-Alphabet-Cartel/ash-vault.git
cd ash-vault

# Configure
cp .env.template .env

# Create secrets
mkdir -p secrets
echo "ashadmin" > secrets/minio_root_user
openssl rand -base64 32 > secrets/minio_root_password
touch secrets/discord_alert_token
chmod 600 secrets/*

# Deploy
docker compose up -d

# Verify
curl http://localhost:30886/health | jq
```

---

## 📦 Components

| Component | Port | Purpose |
|-----------|------|---------|
| MinIO API | 30884 | S3-compatible object storage |
| MinIO Console | 30885 | Web administration UI |
| Backup Service | 30886 | Health endpoint and scheduling |

### Storage Buckets

| Bucket | Purpose |
|--------|---------|
| `ash-archives` | Encrypted crisis session archives |
| `ash-documents` | Document backups |
| `ash-exports` | PDF exports and reports |

---

## 🔐 Security

### Encryption Layers

| Layer | Method | Location |
|-------|--------|----------|
| Application | AES-256-GCM | Ash-Dash encrypts before storage |
| Filesystem | ZFS native | Syn VM storage encryption |
| Transport | HTTPS/SSH | Network communication |

### Access Control

- MinIO API: Lofn (10.20.30.253) only
- MinIO Console: Local network (10.20.30.0/24)
- SSH: Local network only
- Firewall: UFW with default deny

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Roadmap](docs/v5.0/roadmap.md) | Project phases and status |
| [Operations Guide](docs/operations/operations_guide.md) | Day-to-day maintenance |
| [Troubleshooting](docs/operations/troubleshooting.md) | Common issues and fixes |
| [Recovery Runbook](docs/v5.0/phase4/recovery_runbook.md) | Disaster recovery procedures |
| [VM Setup](docs/v5.0/phase1/syn-vm-setup.md) | Syn VM installation guide |

---

## 🔄 Backup Strategy

| Tier | Location | Schedule | Retention | RTO |
|------|----------|----------|-----------|-----|
| 3 | Syn (ZFS snapshots) | Daily 3 AM | 7d/4w/12m | 5 min |
| 2 | Lofn (ZFS recv) | Nightly 4 AM | Mirrors Syn | 30 min |
| 1 | Backblaze B2 | Weekly Sun 5 AM | Mirrors Syn | 4 hours |

---

## 🔗 Ash Ecosystem

Ash-Vault is part of the Ash crisis detection ecosystem:

| Project | Purpose |
|---------|---------|
| [ash](https://github.com/the-alphabet-cartel/ash) | Parent repository |
| [ash-bot](https://github.com/the-alphabet-cartel/ash-bot) | Discord bot frontend |
| [ash-nlp](https://github.com/the-alphabet-cartel/ash-nlp) | NLP classification backend |
| [ash-dash](https://github.com/the-alphabet-cartel/ash-dash) | Crisis response dashboard |
| [ash-thrash](https://github.com/the-alphabet-cartel/ash-thrash) | Testing suite |
| **ash-vault** | Archive & backup infrastructure |

---

## 🤝 Contributing

This project follows the [Clean Architecture Charter](docs/standards/clean_architecture_charter.md).

1. Read the charter before making changes
2. Follow the factory function pattern
3. Include proper file version headers
4. Test all backup procedures

---

## 📄 License

See [LICENSE](LICENSE) for details.

---

## 💜 Community

- **Discord**: [discord.gg/alphabetcartel](https://discord.gg/alphabetcartel)
- **Website**: [alphabetcartel.org](https://alphabetcartel.org)
- **GitHub**: [github.com/the-alphabet-cartel](https://github.com/the-alphabet-cartel)

---

**Built with care for chosen family** 🏳️‍🌈
