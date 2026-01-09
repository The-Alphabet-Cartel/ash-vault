# Ash-Vault Secrets

**Repository**: https://github.com/the-alphabet-cartel/ash-vault  
**Community**: [The Alphabet Cartel](https://discord.gg/alphabetcartel) | [alphabetcartel.org](https://alphabetcartel.org)

---

## Overview

This directory contains sensitive credentials used by Ash-Vault. These files are:
- **NOT** committed to Git (via `.gitignore`)
- Mounted into Docker containers via Docker Secrets
- Read by the `SecretsManager` at runtime

---

## Secret Files

| File | Description | Required | Used By |
|------|-------------|----------|---------|
| `minio_root_user` | MinIO admin username | ✅ Required | MinIO container |
| `minio_root_password` | MinIO admin password | ✅ Required | MinIO container |
| `b2_key_id` | Backblaze B2 application key ID | ✅ Required | Backup service |
| `b2_application_key` | Backblaze B2 application key | ✅ Required | Backup service |
| `discord_alert_token` | Discord webhook URL for alerts | Optional | Backup service |

---

## Setup Instructions

### 1. Create the secrets directory (if not exists)

```bash
mkdir -p secrets
chmod 700 secrets
```

### 2. Add MinIO Credentials (Required)

These credentials are used by MinIO for authentication.

```bash
# Set admin username
echo "ashadmin" > secrets/minio_root_user

# Generate secure password (32 characters)
openssl rand -base64 32 > secrets/minio_root_password

# Set secure permissions
chmod 600 secrets/minio_root_user
chmod 600 secrets/minio_root_password

# Display the password (save it in your password manager!)
echo "MinIO Admin Password:"
cat secrets/minio_root_password
```

⚠️ **Save the MinIO password in your password manager!**

### 3. Add Backblaze B2 Credentials (Required for Cloud Backup)

Get your B2 credentials from: https://secure.backblaze.com/app_keys.htm

1. Log into Backblaze B2 Console
2. Create a new bucket named `ash-vault-backup` (private)
3. Create an Application Key with access to that bucket only
4. Save the keyID and applicationKey

```bash
# Create B2 key ID secret
echo "your_b2_key_id_here" > secrets/b2_key_id

# Create B2 application key secret
echo "your_b2_application_key_here" > secrets/b2_application_key

# Set secure permissions
chmod 600 secrets/b2_key_id
chmod 600 secrets/b2_application_key
```

### 4. Add Discord Alert Webhook (Optional)

For backup success/failure notifications:

1. In Discord: Server Settings → Integrations → Webhooks → New Webhook
2. Copy the webhook URL
3. Create the secret:

```bash
# Create the webhook secret
echo "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN" > secrets/discord_alert_token

# Set secure permissions
chmod 600 secrets/discord_alert_token
```

### 5. Verify Setup

```bash
# Check files exist and have correct permissions
ls -la secrets/

# Expected output (permissions should be -rw-------)
# -rw------- 1 root root   XX  secrets/minio_root_user
# -rw------- 1 root root   XX  secrets/minio_root_password
# -rw------- 1 root root   XX  secrets/b2_key_id
# -rw------- 1 root root   XX  secrets/b2_application_key
# -rw------- 1 root root   XX  secrets/discord_alert_token

# Verify no trailing whitespace
cat -A secrets/minio_root_password
```

---

## How It Works

### MinIO Container

MinIO reads credentials from Docker secrets at startup:

```yaml
# In /opt/minio/docker-compose.yml
services:
  minio:
    environment:
      MINIO_ROOT_USER_FILE: /run/secrets/minio_root_user
      MINIO_ROOT_PASSWORD_FILE: /run/secrets/minio_root_password
    secrets:
      - minio_root_user
      - minio_root_password

secrets:
  minio_root_user:
    file: ./secrets/minio_root_user
  minio_root_password:
    file: ./secrets/minio_root_password
```

### Backup Service

The Python backup service reads secrets via `SecretsManager`:

```python
from src.managers import create_secrets_manager

secrets = create_secrets_manager()

# Get B2 credentials for rclone
b2_key_id = secrets.get("b2_key_id")
b2_app_key = secrets.get("b2_application_key")

# Get Discord webhook for alerts
discord_webhook = secrets.get("discord_alert_token")
```

---

## Deployment Locations

### On Syn VM

Secrets are stored in two locations:

| Location | Purpose |
|----------|---------|
| `/opt/minio/secrets/` | MinIO credentials (MinIO docker-compose) |
| `/opt/ash-vault/secrets/` | Backup service credentials |

### Development

For local development, `SecretsManager` checks:
1. `/run/secrets/` (Docker secrets path)
2. `./secrets/` (local directory)
3. Environment variables (fallback)

---

## Security Best Practices

### DO ✅

- Use `chmod 600` for all secret files
- Keep secrets out of Git (check `.gitignore`)
- Rotate credentials periodically
- Use minimal B2 key permissions (single bucket only)
- Store backup copies in your password manager
- Use separate credentials for dev and prod

### DON'T ❌

- Commit secrets to Git
- Log or print secret values
- Share secrets in chat/email
- Use the same credentials across environments
- Store secrets in environment files committed to Git
- Include quotes or extra whitespace in secret files

---

## File Format

Secret files should contain **only** the secret value:

**Correct** ✅
```
ashadmin
```

**Wrong** ❌
```
MINIO_ROOT_USER=ashadmin
```

**Wrong** ❌
```
"ashadmin"
```

**Wrong** ❌
```
ashadmin

```
(trailing newline can cause issues)

---

## Troubleshooting

### Secret Not Found

```
DEBUG: Secret 'minio_root_password' not found
```

Check:
1. File exists: `ls -la secrets/minio_root_password`
2. File has content: `cat secrets/minio_root_password`
3. No extra whitespace: `cat -A secrets/minio_root_password`

### Permission Denied

```
WARNING: Failed to read secret 'b2_key_id': Permission denied
```

Fix permissions:
```bash
chmod 600 secrets/b2_key_id
```

### MinIO Won't Start

Check secrets are readable:
```bash
docker compose logs minio
# Look for authentication errors

# Verify secrets exist
ls -la /opt/minio/secrets/
```

### B2 Sync Fails

1. Verify B2 credentials at https://secure.backblaze.com/app_keys.htm
2. Check the application key has access to the correct bucket
3. Verify rclone configuration

---

## Rclone Configuration

The backup service uses rclone for B2 sync. Configuration is generated automatically using secrets:

```ini
# /root/.config/rclone/rclone.conf (auto-generated)
[b2]
type = b2
account = <from b2_key_id secret>
key = <from b2_application_key secret>
hard_delete = true
```

---

## Support

- **Discord**: [discord.gg/alphabetcartel](https://discord.gg/alphabetcartel)
- **GitHub Issues**: [github.com/the-alphabet-cartel/ash-vault/issues](https://github.com/the-alphabet-cartel/ash-vault/issues)

---

**Built with care for chosen family** 🏳️‍🌈
