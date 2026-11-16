# Performance

## What Phase 2 configures
| Area | Setting |
|---|---|
| Swap | zram (zstd, RAM/2 up to 4 GiB, priority 100) via `systemd-zram-generator`. Disk swap stays optional. |
| Kernel | `swappiness=100`, `page-cluster=0`, `vfs_cache_pressure=50`, lower dirty ratios. No cache dropping. |
| OOM | `earlyoom` acts only below 5% free RAM and swap; protects systemd, Xorg, lightdm, NetworkManager, sshd. |
| Power | `power-profiles-daemon` (power saver / balanced / performance). Only one power service is installed, so there is no conflict. |
| Boot | `NetworkManager-wait-online` masked. |
| Tools | `dilshan-memory-monitor`, `dilshan-power-settings` (Python + GTK 3). |

## Targets (NOT measured yet)
| | 2 GB | 4 GB | 8 GB |
|---|---|---|---|
| Idle RAM used | < 500 MB | < 550 MB | < 600 MB |
| Boot to desktop (HDD) | < 60 s | < 50 s | < 45 s |
| Idle CPU | < 3% | < 3% | < 3% |

## Measurements
The boot test writes `systemd-analyze`, `free -m` and `swapon --show` to the serial log of every CI run (artifact `boot-test-*`). Real numbers will be copied here from those logs; the live environment runs from RAM, so installed-system figures will differ.
