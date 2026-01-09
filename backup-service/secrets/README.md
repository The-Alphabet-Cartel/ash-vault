# Backup Service Secrets

**Version**: v5.0-3  
**Repository**: https://github.com/the-alphabet-cartel/ash-vault  
**Community**: [The Alphabet Cartel](https://discord.gg/alphabetcartel) | [alphabetcartel.org](https://alphabetcartel.org)

---

## ⚠️ Do Not Commit Secrets to Git!

This directory contains Docker secrets that should **never** be committed to version control.

## 📁 Required Files

Create the following file manually on Syn:

| File | Purpose | Permissions |
|------|---------|-------------|
| `discord_webhook` | Discord webhook URL for alerts | 600 |

## 🔐 Setup Instructions

On Syn (`10.20.30.202`):

```bash
# Navigate to backup service directory
cd /opt/ash-vault-backup/secrets

# Create Discord webhook secret (paste your webhook URL)
echo "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN" > discord_webhook

# Secure the file
chmod 600 discord_webhook
```

## 🔗 Getting a Discord Webhook

1. Go to your Discord server
2. Select the channel for backup alerts
3. Click **Edit Channel** (gear icon)
4. Go to **Integrations** → **Webhooks**
5. Click **New Webhook**
6. Name it "Ash-Vault Backup"
7. Copy the **Webhook URL**
8. Paste into the `discord_webhook` file

---

**Built with care for chosen family** 🏳️‍🌈
