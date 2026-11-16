# Testing in a browser emulator (oses.ioblako.com)

That site runs **v86**, a 32-bit x86 emulator in WebAssembly: BIOS only, no 64-bit CPU, no UEFI, max 2 GB RAM, and it is slow.
The normal Dilshan OS ISO is 64-bit (`amd64`) and **cannot boot there**. Use the separate **lite** image instead.

## Build the lite ISO
1. Push to GitHub, open **Actions**, pick the latest run.
2. Download the artifact **dilshan-os-lite-iso** and unzip it. You get `dilshan-os-lite-<version>-i386.iso`.
   (Or on an x86-64 Linux/Docker host: `PROFILE=lite sudo ./scripts/build-iso.sh`.)

## Run it
1. Open https://oses.ioblako.com/main.html
2. Under **CD-ROM** upload the `.iso`.
3. RAM 512 or 1024 MB, boot order **CD-ROM first**, click **Start Emulator**.
4. Wait: booting can take a few minutes. The console login is `user` / `live`.

The lite image is experimental: v86 may not support every CPU feature of Debian's 686 kernel. Do not expect the desktop; test that in QEMU, UTM or on real hardware with the desktop ISO.
