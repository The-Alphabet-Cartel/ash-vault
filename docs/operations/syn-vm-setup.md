# Syn VM Setup Guide

**Version**: v5.0-1  
**Created**: 2026-01-08  
**Last Updated**: 2026-01-09  
**Repository**: https://github.com/the-alphabet-cartel/ash-vault  
**Community**: [The Alphabet Cartel](https://discord.gg/alphabetcartel) | [alphabetcartel.org](https://alphabetcartel.org)

---

## 📋 Document Purpose

This document provides a comprehensive, step-by-step guide to building or rebuilding the Syn VM from scratch. Use this guide if:

- Setting up Syn for the first time
- The VM becomes corrupted or needs migration
- Disaster recovery requires VM recreation

**Syn** is named after the Norse goddess who guards the doors of halls and denies entry to those not permitted - fitting for our archive vault.

---

## 🖥️ VM Specifications

| Component | Value |
|-----------|-------|
| **Name** | Syn |
| **Hypervisor** | Odin (Windows 11 with Hyper-V) |
| **Generation** | 2 (UEFI) |
| **vCPUs** | 2 |
| **RAM** | 4 GB (Dynamic Memory enabled) |
| **OS Disk** | 256 GB (`D:\Syn\Virtual Hard Disks\Syn.vhdx`) |
| **ZFS Disk** | 256 GB Fixed (`D:\Syn\Virtual Hard Disks\Syn-ZFS.vhdx`) |
| **Network** | vEthernet (virtual switch) |
| **IP Address** | 10.20.30.202 (via DHCP reservation) |
| **OS** | Debian Trixie (13) - Minimal CLI + SSH |
| **Hostname** | syn |

### Port Allocation

| Port | Service | Access |
|------|---------|--------|
| 22 | SSH | Local network (10.20.30.0/24) |
| 30884 | MinIO API | Lofn only (10.20.30.253) |
| 30885 | MinIO Console | Local network (10.20.30.0/24) |
| 30886 | Backup Service | Local network (10.20.30.0/24) |

---

## 📥 Prerequisites

Before starting, ensure you have:

- [ ] Debian Trixie netinst ISO downloaded
  - URL: https://cdimage.debian.org/cdimage/weekly-builds/amd64/iso-cd/
  - File: `debian-testing-amd64-netinst.iso` (~600-700 MB)
- [ ] DHCP reservation configured for 10.20.30.202
- [ ] Access to Odin with Hyper-V Manager
- [ ] ZFS encryption key backup (if restoring existing data)

---

## 🔧 Step-by-Step Setup

### Step 1: Create Hyper-V Virtual Machine

1. Open **Hyper-V Manager** on Odin
2. Right-click **ODIN** → **New** → **Virtual Machine...**

#### Specify Name and Location

| Field | Value |
|-------|-------|
| Name | `Syn` |
| ☑️ | Store the virtual machine in a different location |
| Location | `D:\Syn` |

#### Specify Generation

| Option | Value |
|--------|-------|
| Generation | **Generation 2** |

#### Assign Memory

| Field | Value |
|-------|-------|
| Startup memory | `4096` MB |
| ☑️ | Use Dynamic Memory for this virtual machine |

#### Configure Networking

| Field | Value |
|-------|-------|
| Connection | **vEthernet** |

#### Connect Virtual Hard Disk

| Field | Value |
|-------|-------|
| Option | Create a virtual hard disk |
| Name | `Syn.vhdx` |
| Location | `D:\Syn\Virtual Hard Disks` |
| Size | `256` GB |

#### Installation Options

| Field | Value |
|-------|-------|
| Option | Install an operating system from a bootable image file |
| Image file | Browse to Debian Trixie ISO |

Click **Finish**

---

### Step 2: Adjust VM Settings Before First Boot

Right-click **Syn** → **Settings...**

#### Processor

- Set **Number of virtual processors** to `2`

#### Security

- **Uncheck** "Enable Secure Boot" (required for Debian)

#### Checkpoints (Optional)

- Set to **Production checkpoints** or disable as preferred

Click **OK**

---

### Step 3: Install Debian

1. Right-click **Syn** → **Connect...**
2. Click **Start**
3. Follow the Debian installer:

| Prompt | Value |
|--------|-------|
| Language | English |
| Location | Your location |
| Keyboard | Your preference |
| Hostname | `syn` |
| Domain name | (leave blank) |
| Root password | Set a strong password |
| Create user | Optional (can use root only) |
| Timezone | Your timezone |
| Partitioning | Guided - use entire disk |
| Partition scheme | All files in one partition |
| Software selection | **SSH server ONLY** (uncheck everything else) |

4. Complete installation and reboot
5. Remove ISO from VM settings after first boot

---

### Step 4: Post-Install Configuration

Log in as root and verify network:

```bash
# Verify hostname
hostname

# Verify IP (should be 10.20.30.202)
ip addr show eth0 | grep inet

# Test connectivity to Lofn
ping -c 2 10.20.30.253

# Check disk layout
lsblk
```

#### Fix .profile mesg Error (Optional)

If you see `-bash: mesg: command not found` on login:

```bash
nano /root/.profile
```

Change:
```bash
mesg n || true
```

To:
```bash
command -v mesg >/dev/null 2>&1 && mesg n
```

#### Enable Contrib Repository

```bash
nano /etc/apt/sources.list
```

Change each line to include `contrib non-free non-free-firmware`:

```
deb http://deb.debian.org/debian trixie main contrib non-free non-free-firmware
deb http://deb.debian.org/debian trixie-updates main contrib non-free non-free-firmware
deb http://security.debian.org/debian-security trixie-security main contrib non-free non-free-firmware
```

Update packages:

```bash
apt update && apt upgrade -y
```

---

### Step 5: Add ZFS Virtual Disk

1. Shut down Syn:
   ```bash
   shutdown now
   ```

2. In Hyper-V Manager, right-click **Syn** → **Settings...**

3. Select **SCSI Controller** → **Hard Drive** → **Add**

4. Click **New** to create a new virtual hard disk:

| Field | Value |
|-------|-------|
| Format | VHDX |
| Type | **Fixed size** (important for ZFS performance) |
| Name | `Syn-ZFS.vhdx` |
| Location | `D:\Syn\Virtual Hard Disks` |
| Size | `256` GB |

5. Wait for disk creation (takes several minutes for fixed size)

6. Click **OK** and start Syn

7. Verify new disk:
   ```bash
   lsblk
   ```
   Should show `sdb` at 256GB

---

### Step 6: Install ZFS

```bash
apt install -y linux-headers-amd64 dkms zfsutils-linux
```

Build ZFS module (if not auto-built):

```bash
dkms status
# If shows "zfs/x.x.x: added" but not installed:
dkms install zfs/2.3.2
```

Load module and verify:

```bash
modprobe zfs
zfs version
```

Expected output:
```
zfs-2.3.x-x
zfs-kmod-2.3.x-x
```

---

### Step 7: Create Encrypted ZFS Pool

#### Generate Encryption Key

```bash
mkdir -p /root/.zfs-keys
dd if=/dev/urandom of=/root/.zfs-keys/syn-key bs=32 count=1
chmod 600 /root/.zfs-keys/syn-key
chmod 700 /root/.zfs-keys
```

#### ⚠️ BACKUP THE KEY NOW!

```bash
base64 /root/.zfs-keys/syn-key
```

**Save this base64 string in your password manager!** Without it, data is unrecoverable.

To restore from backup:
```bash
echo "YOUR_BASE64_STRING" | base64 -d > /root/.zfs-keys/syn-key
chmod 600 /root/.zfs-keys/syn-key
```

#### Create Pool

```bash
zpool create \
    -o ashift=12 \
    -O acltype=posixacl \
    -O compression=lz4 \
    -O dnodesize=auto \
    -O normalization=formD \
    -O relatime=on \
    -O xattr=sa \
    syn /dev/sdb
```

#### Create Encrypted Dataset

```bash
zfs create \
    -o encryption=aes-256-gcm \
    -o keyformat=raw \
    -o keylocation=file:///root/.zfs-keys/syn-key \
    -o mountpoint=/mnt/archives \
    syn/archives
```

#### Verify

```bash
zpool status
zfs list
zfs get encryption,keystatus,compression syn/archives
```

---

### Step 8: Configure ZFS Auto-Mount on Boot

Create systemd service:

```bash
cat > /etc/systemd/system/zfs-load-key-syn.service << 'EOF'
[Unit]
Description=Load ZFS encryption key for syn/archives
DefaultDependencies=no
Before=zfs-mount.service
After=zfs-import.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/sbin/zfs load-key syn/archives

[Install]
WantedBy=zfs-mount.service
EOF
```

Enable service:

```bash
systemctl enable zfs-load-key-syn.service
```

Create MinIO data directory:

```bash
mkdir -p /mnt/archives/minio-data
```

---

### Step 9: Install Docker

```bash
apt install -y docker.io docker-compose
systemctl enable docker
```

Verify:

```bash
docker --version
docker compose version
systemctl status docker
```

---

### Step 10: Configure Firewall

```bash
apt install -y ufw

# Default policies
ufw default deny incoming
ufw default allow outgoing

# Allow SSH from local network
ufw allow from 10.20.30.0/24 to any port 22

# Allow MinIO API from Lofn only
ufw allow from 10.20.30.253 to any port 30884

# Allow MinIO Console from local network
ufw allow from 10.20.30.0/24 to any port 30885

# Allow Backup Service from local network
ufw allow from 10.20.30.0/24 to any port 30886

# Enable firewall
ufw enable
```

Verify:

```bash
ufw status verbose
```

---

### Step 11: Test Reboot

```bash
reboot
```

After reboot, verify everything:

```bash
zpool status
zfs list
zfs get keystatus syn/archives
ls -la /mnt/archives/
docker --version
ufw status
```

---

## ✅ Verification Checklist

After completing setup, verify:

- [ ] Hostname is `syn`
- [ ] IP address is 10.20.30.202
- [ ] Can ping Lofn (10.20.30.253)
- [ ] ZFS pool `syn` is ONLINE
- [ ] Dataset `syn/archives` is mounted at `/mnt/archives`
- [ ] ZFS keystatus is `available`
- [ ] `/mnt/archives/minio-data` directory exists
- [ ] Docker is running
- [ ] UFW firewall is active
- [ ] All settings persist after reboot

---

## 🔐 Encryption Key Recovery

If the encryption key is lost from Syn but you have the backup:

```bash
# Create key directory
mkdir -p /root/.zfs-keys
chmod 700 /root/.zfs-keys

# Restore key from base64 backup
echo "YOUR_BASE64_STRING_HERE" | base64 -d > /root/.zfs-keys/syn-key
chmod 600 /root/.zfs-keys/syn-key

# Load key and mount
zfs load-key syn/archives
zfs mount syn/archives
```

---

## 🔄 Restoring Data from Backups

### From Tier 2 (Lofn ZFS)

If Syn is rebuilt and Lofn has backup data:

```bash
# On new Syn VM (after ZFS pool is created)
ssh root@10.20.30.253 "zfs send backup/ash-vault@latest" | zfs recv -F syn/archives
```

### From Tier 1 (Backblaze B2)

If restoring from cloud backup:

```bash
# Install rclone
apt install -y rclone

# Configure rclone (see Phase 3 docs)
rclone config

# Sync data back
rclone sync b2:ash-vault-backup /mnt/archives/minio-data
```

---

## 📊 Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│                        SYN - THE GUARDIAN                        │
│                     Norse Goddess of Doorways                    │
├─────────────────────────────────────────────────────────────────┤
│  Hostname:     syn                                               │
│  IP Address:   10.20.30.202                                      │
│  OS:           Debian Trixie (13) - Minimal                      │
│  Hypervisor:   Odin (Hyper-V Gen 2)                              │
│                                                                  │
│  RESOURCES                                                       │
│  ├── vCPUs:    2                                                 │
│  ├── RAM:      4 GB (dynamic)                                    │
│  ├── OS Disk:  256 GB (Syn.vhdx)                                 │
│  └── ZFS Disk: 256 GB Fixed (Syn-ZFS.vhdx)                       │
│                                                                  │
│  ZFS                                                             │
│  ├── Pool:     syn                                               │
│  ├── Dataset:  syn/archives                                      │
│  ├── Mount:    /mnt/archives                                     │
│  ├── Encrypt:  aes-256-gcm                                       │
│  └── Key:      /root/.zfs-keys/syn-key                           │
│                                                                  │
│  PORTS                                                           │
│  ├── 22:       SSH (10.20.30.0/24)                               │
│  ├── 30884:    MinIO API (10.20.30.253 only)                     │
│  ├── 30885:    MinIO Console (10.20.30.0/24)                     │
│  └── 30886:    Backup Service (10.20.30.0/24)                    │
│                                                                  │
│  SERVICES                                                        │
│  ├── Docker:   Enabled                                           │
│  ├── SSH:      Enabled                                           │
│  ├── UFW:      Active                                            │
│  └── ZFS Key:  Auto-load on boot                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔗 Related Documents

- [Phase 1 Planning](planning.md) - Original planning document
- [Phase 1 Complete](complete.md) - Completion summary
- [Phase 2 Planning](../phase2/planning.md) - MinIO deployment

---

**Built with care for chosen family** 🏳️‍🌈
