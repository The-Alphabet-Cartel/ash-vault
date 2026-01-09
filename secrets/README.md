# Ash-Vault Secrets Directory

**Version**: v5.0-3-3.6-1  
**Repository**: https://github.com/the-alphabet-cartel/ash-vault  
**Community**: [The Alphabet Cartel](https://discord.gg/alphabetcartel) | [alphabetcartel.org](https://alphabetcartel.org)

---

## ⚠️ IMPORTANT

This directory contains sensitive credentials. These files are:
- **NOT tracked by git** (listed in `.gitignore`)
- **Required for Docker secrets** functionality
- **Must be created manually** on each deployment

---

## 📋 Required Secrets

| Secret File | Service | Description | Required |
|-------------|---------|-------------|----------|
| `minio_root_user` | MinIO | Admin username | ✅ Yes |
| `minio_root_password` | MinIO | Admin password (32+ chars recommended) | ✅ Yes |
| `discord_alert_token` | Backup Service | Discord webhook URL for alerts | ⚡ Optional |

---

## 🔧 Setup Instructions

### 1. MinIO Credentials

```bash
# Create MinIO admin username
echo "ashadmin" > ./secrets/minio_root_user

# Create MinIO admin password (use a strong password!)
echo "YourSuperSecurePassword32CharsMin" > ./secrets/minio_root_password

# Secure the files
chmod 600 ./secrets/minio_root_user
chmod 600 ./secrets/minio_root_password
```

### 2. Discord Webhook (Optional)

If you want backup failure alerts in Discord:

1. Create a Discord webhook in your server
2. Copy the webhook URL
3. Create the secret file:

```bash
echo "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL" > ./secrets/discord_alert_token
chmod 600 ./secrets/discord_alert_token
```

If you don't want Discord alerts, create an empty file:

```bash
touch ./secrets/discord_alert_token
chmod 600 ./secrets/discord_alert_token
```

---

## 📁 Expected Directory Structure

```
secrets/
├── README.md              # This file
├── minio_root_user        # MinIO admin username
├── minio_root_password    # MinIO admin password
└── discord_alert_token    # Discord webhook URL (or empty)
```

---

## ✅ Verification

After creating secrets, verify permissions:

```bash
ls -la ./secrets/
```

Expected output:
```
-rw------- 1 root root   xx xxx xx xx:xx minio_root_user
-rw------- 1 root root   xx xxx xx xx:xx minio_root_password
-rw------- 1 root root   xx xxx xx xx:xx discord_alert_token
```

All secret files should show `-rw-------` (600) permissions.

---

## 🔐 Security Notes

- Never commit secret files to git
- Use strong, unique passwords (32+ characters for MinIO)
- Rotate credentials periodically
- Back up credentials securely (password manager recommended)
- The `.gitignore` file excludes all files in this directory except `README.md`

---

**Built with care for chosen family** 🏳️‍🌈
