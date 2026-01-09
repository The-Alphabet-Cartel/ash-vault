# Ash-Vault Troubleshooting Guide

**Version**: v5.0-5  
**Created**: 2026-01-09  
**Repository**: https://github.com/the-alphabet-cartel/ash-vault  
**Community**: [The Alphabet Cartel](https://discord.gg/alphabetcartel) | [alphabetcartel.org](https://alphabetcartel.org)

---

## 🔍 Diagnostic Commands

```bash
# Quick health check
docker compose ps
curl -s http://localhost:30886/health | jq
curl -s http://localhost:30884/minio/health/live

# View recent logs
docker compose logs --tail=50 ash-vault-backup
docker compose logs --tail=50 ash-vault-minio

# Check ZFS status
zfs list syn/archives
zpool status syn
```

---

## 🚨 Common Issues

### Container Won't Start

**Symptoms**: `docker compose up` fails, container exits immediately

**Check**:
```bash
docker compose logs ash-vault-backup
```

**Common Causes**:

| Cause | Solution |
|-------|----------|
| Missing secrets file | Create `secrets/discord_alert_token` (can be empty) |
| Port in use | Check `netstat -tlnp | grep 30886` |
| Invalid .env | Verify `.env` copied from `.env.template` |

**Fix**:
```bash
# Ensure secrets exist
touch /dockers/ash-vault/secrets/discord_alert_token
chmod 600 /dockers/ash-vault/secrets/*

# Recreate container
docker compose down
docker compose up -d
```

---

### MinIO Not Accessible

**Symptoms**: Can't access :30884 or :30885

**Check**:
```bash
docker compose ps ash-vault-minio
docker compose logs ash-vault-minio
```

**Common Causes**:

| Cause | Solution |
|-------|----------|
| Container not running | `docker compose up -d ash-vault-minio` |
| Wrong credentials | Check `secrets/minio_root_user` and `minio_root_password` |
| Data directory permissions | Verify `/mnt/archives/minio-data` exists and is writable |

**Fix**:
```bash
# Check data directory
ls -la /mnt/archives/minio-data/

# Restart MinIO
docker compose restart ash-vault-minio
```

---

### ZFS Snapshot Fails

**Symptoms**: Discord alert about snapshot failure, no new snapshots

**Check**:
```bash
zfs list -t snapshot | grep syn/archives | tail -5
zpool status syn
```

**Common Causes**:

| Cause | Solution |
|-------|----------|
| Pool full | Delete old snapshots, expand pool |
| Pool degraded | Replace failed disk |
| Dataset not mounted | `zfs mount syn/archives` |

**Fix**:
```bash
# Check pool capacity
zpool list syn

# Manual snapshot test
zfs snapshot syn/archives@test-$(date +%s)
zfs destroy syn/archives@test-*
```

---

### Lofn Replication Fails

**Symptoms**: Replication job fails, no recent snapshots on Lofn

**Check**:
```bash
# Test SSH connection
ssh -i /root/.ssh/id_ed25519_lofn root@10.20.30.253 "hostname"

# Check Lofn dataset
ssh -i /root/.ssh/id_ed25519_lofn root@10.20.30.253 "zfs list backup/ash-vault"
```

**Common Causes**:

| Cause | Solution |
|-------|----------|
| SSH key issue | Verify key permissions (600) |
| Lofn offline | Check Lofn server |
| Dataset doesn't exist | Let `zfs recv` create it |
| Encryption mismatch | Destroy unencrypted dataset on Lofn |

**Fix (encryption mismatch)**:
```bash
# On Lofn - destroy existing dataset
ssh -i /root/.ssh/id_ed25519_lofn root@10.20.30.253 "zfs destroy -r backup/ash-vault"

# Retry send - will create encrypted dataset
zfs send -w syn/archives@daily-LATEST | \
  ssh -i /root/.ssh/id_ed25519_lofn root@10.20.30.253 "zfs recv -F backup/ash-vault"
```

---

### B2 Sync Fails

**Symptoms**: Cloud sync job fails, files missing from B2

**Check**:
```bash
# Test rclone connection
rclone lsd b2:

# Test bucket access
rclone ls b2:ash-vault-backup-alphabetcartel | head
```

**Common Causes**:

| Cause | Solution |
|-------|----------|
| Invalid credentials | Check rclone config |
| Network issue | Verify internet connectivity |
| Bucket deleted | Recreate bucket in B2 console |
| Rate limited | Wait and retry |

**Fix**:
```bash
# Verify rclone config
cat /root/.config/rclone/rclone.conf

# Manual sync test
rclone sync /mnt/archives/minio-data b2:ash-vault-backup-alphabetcartel --dry-run
```

---

### Health Endpoint Returns Unhealthy

**Symptoms**: `/health` returns error or unhealthy status

**Check**:
```bash
curl -v http://localhost:30886/health
docker compose logs ash-vault-backup | tail -20
```

**Common Causes**:

| Cause | Solution |
|-------|----------|
| Service crashed | Restart container |
| Port binding issue | Check port availability |
| Python error | Check logs for traceback |

**Fix**:
```bash
docker compose restart ash-vault-backup
sleep 30
curl http://localhost:30886/health
```

---

### Scheduled Jobs Not Running

**Symptoms**: Jobs show in `/status` but don't execute

**Check**:
```bash
curl http://localhost:30886/status | jq '.scheduler'
docker compose logs ash-vault-backup | grep -i "scheduler\|job"
```

**Common Causes**:

| Cause | Solution |
|-------|----------|
| Scheduler not started | Restart container |
| Timezone mismatch | Verify TZ in .env |
| Job crashed | Check logs for errors |

**Fix**:
```bash
# Verify timezone
docker compose exec ash-vault-backup date

# Restart to reinitialize scheduler
docker compose restart ash-vault-backup
```

---

## 🔧 Advanced Diagnostics

### Enter Container Shell

```bash
docker compose exec ash-vault-backup /bin/bash
```

### Test Python Imports

```bash
docker compose exec ash-vault-backup python -c "from src.jobs import create_snapshot_job; print('OK')"
```

### Check ZFS Inside Container

```bash
docker compose exec ash-vault-backup zfs list
```

### View APScheduler Jobs

```bash
curl http://localhost:30886/status | jq '.scheduler.jobs'
```

---

## 📞 Escalation

If issues persist after troubleshooting:

1. Collect logs:
   ```bash
   docker compose logs > /tmp/ash-vault-logs.txt 2>&1
   ```

2. Check GitHub issues: https://github.com/the-alphabet-cartel/ash-vault/issues

3. Ask in Discord: https://discord.gg/alphabetcartel

---

**Built with care for chosen family** 🏳️‍🌈
