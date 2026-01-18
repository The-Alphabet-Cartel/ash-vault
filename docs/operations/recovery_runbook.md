# Ash-Vault Recovery Runbook

**Version**: v5.0-4  
**Created**: 2026-01-09  
**Last Updated**: 2026-01-09  
**Repository**: https://github.com/the-alphabet-cartel/ash-vault  
**Community**: [The Alphabet Cartel](https://discord.gg/alphabetcartel) | [alphabetcartel.org](https://alphabetcartel.org)

---

## 📋 Overview

This runbook provides step-by-step procedures for recovering Ash-Vault data from each backup tier.

| Tier | Use Case | RTO | Location |
|------|----------|-----|----------|
| **3** | Accidental deletion, quick recovery | < 5 min | Syn ZFS snapshots |
| **2** | Syn VM failure | < 30 min | Lofn ZFS replica |
| **1** | Complete site loss | 1-4 hours | Backblaze B2 cloud |

**Always start with the highest available tier (3 → 2 → 1).**

---

## 🔐 Prerequisites

Before any recovery:

1. **SSH access** to Syn (10.20.30.202) as root
2. **SSH key** for Lofn: `/root/.ssh/id_ed25519_lofn`
3. **Rclone** configured with B2 remote
4. **ZFS dataset** `syn/archives` exists (or can be created)

---

## 🟢 Tier 3: Recover from ZFS Snapshot (Syn)

**Use when**: Files accidentally deleted, need quick recovery, Syn VM is operational.

### Step 1: List Available Snapshots

```bash
zfs list -t snapshot -o name,creation | grep syn/archives
```

Example output:
```
syn/archives@daily-2026-01-09      Thu Jan  9  3:00 2026
syn/archives@daily-2026-01-08      Wed Jan  8  3:00 2026
syn/archives@weekly-2026-01-05     Sun Jan  5  3:00 2026
```

### Step 2: Choose Recovery Method

#### Option A: Clone and Copy (Non-destructive, Recommended)

Use this to recover specific files without affecting current data.

```bash
# Clone the snapshot
zfs clone syn/archives@daily-2026-01-09 syn/recovery

# Browse the clone
ls /syn/recovery/minio-data/

# Copy needed files back
cp /syn/recovery/minio-data/path/to/file.txt /mnt/archives/minio-data/path/to/

# Cleanup when done
zfs destroy syn/recovery
```

#### Option B: Rollback (Destructive)

⚠️ **WARNING**: This destroys ALL changes made after the snapshot!

```bash
# Stop MinIO first
docker stop ash-vault-minio

# Rollback to snapshot
zfs rollback syn/archives@daily-2026-01-09

# Restart MinIO
docker start ash-vault-minio
```

### Step 3: Verify Recovery

```bash
# Check files exist
ls -la /mnt/archives/minio-data/

# Verify MinIO sees the data
curl http://localhost:30884/minio/health/live
```

---

## 🟡 Tier 2: Recover from Lofn ZFS Replica

**Use when**: Syn VM failed, OS corrupted, or Tier 3 snapshots unavailable.

### Prerequisites

- Syn VM rebuilt with Debian 12
- ZFS pool `syn` created
- SSH key for Lofn exists or can be copied
- Network connectivity to Lofn (10.20.30.253)

### Step 1: Verify Lofn Has Data

From Syn (or any machine with SSH access to Lofn):

```bash
ssh -i /root/.ssh/id_ed25519_lofn root@10.20.30.253 \
  "zfs list -t snapshot backup/ash-vault"
```

### Step 2: Receive from Lofn

```bash
# Get the latest snapshot name
LATEST=$(ssh -i /root/.ssh/id_ed25519_lofn root@10.20.30.253 \
  "zfs list -t snapshot -o name -H backup/ash-vault | tail -1")

echo "Receiving: $LATEST"

# Receive the encrypted dataset
ssh -i /root/.ssh/id_ed25519_lofn root@10.20.30.253 \
  "zfs send -w $LATEST" | zfs recv -F syn/archives
```

### Step 3: Load Encryption Key

The dataset is encrypted. You need the encryption key to mount it.

```bash
# Load the encryption key (you'll be prompted for passphrase)
zfs load-key syn/archives

# Mount the dataset
zfs mount syn/archives

# Verify
ls /mnt/archives/minio-data/
```

### Step 4: Restart Services

```bash
cd /dockers/ash-vault
docker compose up -d
docker compose ps
```

### Step 5: Verify Recovery

```bash
curl http://localhost:30884/minio/health/live
curl http://localhost:30886/health
```

---

## 🔴 Tier 1: Recover from Backblaze B2 Cloud

**Use when**: Complete site loss, both Syn and Lofn unavailable.

### Prerequisites

- New Syn VM with Debian 12
- ZFS pool `syn` created
- Dataset `syn/archives` created and encrypted
- Rclone installed and configured with B2 credentials
- Internet connectivity

### Step 1: Create Fresh Dataset (if needed)

```bash
# Create encrypted dataset
zfs create -o encryption=aes-256-gcm -o keyformat=passphrase \
  -o mountpoint=/mnt/archives syn/archives

# Enter passphrase when prompted (use same as original!)
```

### Step 2: Verify B2 Connection

```bash
# List B2 bucket contents
rclone ls b2:ash-vault-backup-alphabetcartel | head -20
```

### Step 3: Restore from B2

```bash
# Create target directory
mkdir -p /mnt/archives/minio-data

# Sync from B2 (this may take hours depending on data size)
rclone sync b2:ash-vault-backup-alphabetcartel /mnt/archives/minio-data \
  --transfers 8 \
  --progress \
  --stats 30s

# Verify file count
rclone size b2:ash-vault-backup-alphabetcartel
ls -la /mnt/archives/minio-data/
```

### Step 4: Deploy Ash-Vault

```bash
# Clone repository
mkdir -p /dockers
cd /dockers
git clone -b v5.0 https://github.com/The-Alphabet-Cartel/ash-vault.git
cd ash-vault

# Create .env from template
cp .env.template .env

# Create secrets
mkdir -p secrets
echo "ashadmin" > secrets/minio_root_user
# Generate or restore MinIO password
echo "YOUR_MINIO_PASSWORD" > secrets/minio_root_password
touch secrets/discord_alert_token
chmod 600 secrets/*

# Start services
docker compose up -d
```

### Step 5: Verify Recovery

```bash
docker compose ps
curl http://localhost:30884/minio/health/live
curl http://localhost:30886/health

# Log into MinIO console at http://SYN_IP:30885
# Verify buckets: ash-archives, ash-documents, ash-exports
```

---

## 📊 Recovery Decision Tree

```
Data Loss Detected
       │
       ▼
┌──────────────────┐
│ Is Syn VM        │
│ operational?     │
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
   YES        NO
    │         │
    ▼         ▼
┌─────────┐ ┌──────────────────┐
│ TIER 3  │ │ Is Lofn          │
│ ZFS     │ │ accessible?      │
│ Snapshot│ └────────┬─────────┘
└─────────┘          │
              ┌──────┴──────┐
              │             │
             YES            NO
              │             │
              ▼             ▼
         ┌─────────┐  ┌─────────┐
         │ TIER 2  │  │ TIER 1  │
         │ Lofn    │  │ B2      │
         │ Replica │  │ Cloud   │
         └─────────┘  └─────────┘
```

---

## ⏱️ Expected Recovery Times

| Tier | Data Size | Estimated Time |
|------|-----------|----------------|
| **3** | Any | < 5 minutes |
| **2** | 1 GB | 5-10 minutes |
| **2** | 10 GB | 20-30 minutes |
| **2** | 100 GB | 2-4 hours |
| **1** | 1 GB | 10-20 minutes |
| **1** | 10 GB | 1-2 hours |
| **1** | 100 GB | 4-8 hours |

*Times depend on network speed and system load.*

---

## 🔑 Important Notes

### Encryption Key

The ZFS encryption passphrase is **critical** for Tier 2 and Tier 3 recovery. Store it securely:
- Password manager (recommended)
- Offline secure location
- NOT in the git repository

### MinIO Credentials

MinIO credentials are stored in Docker secrets. If recovering to a new system:
- Use the same credentials as the original
- Or create new credentials and update any dependent systems

### Snapshot Naming Convention

| Type | Pattern | Example |
|------|---------|---------|
| Daily | `@daily-YYYY-MM-DD` | `@daily-2026-01-09` |
| Weekly | `@weekly-YYYY-MM-DD` | `@weekly-2026-01-05` |
| Monthly | `@monthly-YYYY-MM-DD` | `@monthly-2026-01-01` |
| Replication | `@repl-*` | `@repl-test` |

---

## 📞 Emergency Contacts

| Role | Contact | Notes |
|------|---------|-------|
| Sys Admin | *TBD* | Primary recovery contact |
| Backup Admin | *TBD* | Backup system access |
| Cloud Admin | *TBD* | Backblaze B2 access |

---

## 📝 Recovery Log Template

```markdown
## Recovery Log - [DATE]

**Incident**: [Brief description]
**Tier Used**: [3/2/1]
**Data Loss Window**: [Time range of lost data]

### Timeline
- HH:MM - Incident detected
- HH:MM - Recovery started
- HH:MM - Recovery completed
- HH:MM - Services verified

### Steps Taken
1. [Step]
2. [Step]

### Data Recovered
- [Description]

### Data Lost (if any)
- [Description]

### Lessons Learned
- [What went well]
- [What could improve]

### Sign-off
- Recovered by: [Name]
- Verified by: [Name]
```

---

**Built with care for chosen family** 🏳️‍🌈
