# MinIO Configuration

**Version**: v5.0-2  
**Location on Syn**: `/opt/minio/`  
**Repository**: https://github.com/the-alphabet-cartel/ash-vault  
**Community**: [The Alphabet Cartel](https://discord.gg/alphabetcartel) | [alphabetcartel.org](https://alphabetcartel.org)

---

## 📋 Overview

This directory contains the Docker Compose configuration for MinIO object storage on the Syn VM.

## 📁 Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | MinIO container configuration |

## 🔐 Secrets (Not in Git)

The following files must be created manually on Syn at `/opt/minio/secrets/`:

| File | Purpose | Permissions |
|------|---------|-------------|
| `minio_root_user` | Admin username | 600 |
| `minio_root_password` | Admin password (32+ chars) | 600 |

## 🚀 Deployment

On Syn VM:

```bash
# Create directory structure
mkdir -p /opt/minio/secrets
chmod 700 /opt/minio/secrets

# Copy docker-compose.yml from git repo
cp /path/to/repo/minio/docker-compose.yml /opt/minio/

# Create secrets (if not already done)
echo "ashadmin" > /opt/minio/secrets/minio_root_user
openssl rand -base64 32 > /opt/minio/secrets/minio_root_password
chmod 600 /opt/minio/secrets/*

# Start MinIO
cd /opt/minio
docker compose up -d
```

## 🔗 Endpoints

| Service | Port | URL |
|---------|------|-----|
| S3 API | 30884 | `http://10.20.30.202:30884` |
| Web Console | 30885 | `http://10.20.30.202:30885` |

---

**Built with care for chosen family** 🏳️‍🌈
