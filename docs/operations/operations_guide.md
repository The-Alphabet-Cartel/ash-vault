# Ash-Vault Operations Guide

**Version**: v5.0-5  
**Created**: 2026-01-09  
**Repository**: https://github.com/the-alphabet-cartel/ash-vault  
**Community**: [The Alphabet Cartel](https://discord.gg/alphabetcartel) | [alphabetcartel.org](https://alphabetcartel.org)

---

## 📋 Overview

This guide covers day-to-day operations for maintaining Ash-Vault.

---

## 🔄 Daily Operations

### Health Check

```bash
# Check container status
cd /dockers/ash-vault
docker compose ps

# Check backup service health
curl http://localhost:30886/health | jq

# Check MinIO health
curl http://localhost:30884/minio/health/live
```

**Expected**: Both containers showing `healthy` status.

### View Scheduled Jobs

```bash
curl http://localhost:30886/status | jq '.scheduler'
```

### Check Logs

```bash
# Backup service logs
docker compose logs --tail=50 ash-vault-backup

# MinIO logs
docker compose logs --tail=50 ash-vault-minio
```

---

## 📅 Weekly Operations

### Verify B2 Sync (Monday morning)

```bash
# Check last sync completed (runs Sunday 5 AM)
rclone ls b2:ash-vault-backup-alphabetcartel | wc -l

# Compare with local
ls /mnt/archives/minio-data/.minio.sys/buckets/ | wc -l
```

### Review Snapshots

```bash
# List all snapshots
zfs list -t snapshot | grep syn/archives

# Verify retention (should have ~7 daily, ~4 weekly, ~12 monthly max)
zfs list -t snapshot -o name | grep daily | wc -l
zfs list -t snapshot -o name | grep weekly | wc -l
zfs list -t snapshot -o name | grep monthly | wc -l
```

---

## 📆 Monthly Operations

### Verify Lofn Replication

```bash
# Check Lofn has recent snapshots
ssh -i /root/.ssh/id_ed25519_lofn root@10.20.30.253 \
  "zfs list -t snapshot backup/ash-vault"
```

### Check Disk Usage

```bash
# Syn ZFS usage
zfs list syn/archives

# MinIO data size
du -sh /mnt/archives/minio-data/
```

### Review B2 Storage

Log into [Backblaze B2 Console](https://secure.backblaze.com/b2_buckets.htm) and check:
- Bucket size
- File count
- Any failed uploads

---

## 🔧 Common Tasks

### Restart Services

```bash
cd /dockers/ash-vault
docker compose restart
```

### Update Ash-Vault

```bash
cd /dockers/ash-vault
git pull origin v5.0
docker compose up -d --build
```

### Manual Snapshot

```bash
# Create manual snapshot (for before major changes)
zfs snapshot syn/archives@manual-$(date +%Y%m%d-%H%M%S)
```

### Manual Replication

```bash
# Force replication to Lofn
SNAP=$(zfs list -t snapshot -o name -H syn/archives | tail -1)
zfs send -w $SNAP | \
  ssh -i /root/.ssh/id_ed25519_lofn root@10.20.30.253 \
  "zfs recv -F backup/ash-vault"
```

### Manual B2 Sync

```bash
# Force sync to B2
rclone sync /mnt/archives/minio-data b2:ash-vault-backup-alphabetcartel -v
```

---

## 🔐 Credential Management

### Rotate MinIO Password

1. Generate new password:
   ```bash
   openssl rand -base64 32
   ```

2. Update secret file:
   ```bash
   echo "NEW_PASSWORD" > /dockers/ash-vault/secrets/minio_root_password
   chmod 600 /dockers/ash-vault/secrets/minio_root_password
   ```

3. Restart MinIO:
   ```bash
   docker compose restart ash-vault-minio
   ```

4. Update any dependent systems (Ash-Dash, etc.)

### Update Discord Webhook

```bash
echo "https://discord.com/api/webhooks/NEW_WEBHOOK" > /dockers/ash-vault/secrets/discord_alert_token
chmod 600 /dockers/ash-vault/secrets/discord_alert_token
docker compose restart ash-vault-backup
```

---

## 📊 Monitoring

### Health Endpoint

| Endpoint | Purpose |
|----------|---------|
| `http://localhost:30886/health` | Basic health check |
| `http://localhost:30886/status` | Detailed status with jobs |
| `http://localhost:30886/docs` | API documentation |

### Log Locations

| Log | Location |
|-----|----------|
| Backup service | `/dockers/ash-vault/logs/` |
| Docker logs | `docker compose logs` |
| ZFS operations | `journalctl -u zfs*` |

---

## 🚨 Alert Response

### Backup Failure Alert

1. Check service status:
   ```bash
   docker compose ps
   curl http://localhost:30886/status | jq
   ```

2. Check logs for errors:
   ```bash
   docker compose logs --tail=100 ash-vault-backup | grep -i error
   ```

3. See [Troubleshooting Guide](./troubleshooting.md)

---

## 📝 Maintenance Windows

| Task | Recommended Window | Impact |
|------|-------------------|--------|
| Updates | Sunday 6-8 AM | Brief service restart |
| ZFS scrub | Monthly, overnight | Minimal |
| Credential rotation | Quarterly | Brief outage |

---

**Built with care for chosen family** 🏳️‍🌈
