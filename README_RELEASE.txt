Forja Viral — Professional Release Order (CPU+GPU)

0) UI/License OK (you already did)
1) Cleanup old projects (TTL) -> keep app stable
2) Lock dependencies:
   - requirements_common.txt
   - constraints.txt
   - install_cpu.bat / install_gpu.bat / install.bat
3) Build EXE:
   - run build_exe.bat (generates dist/ForjaViral/ForjaViral.exe)
4) Build Installer:
   - Install Inno Setup
   - Open forja_installer.iss and Compile
   - Installer asks CPU/GPU and runs the right install bat
5) Version lock (anti leak):
   - Use license_server_versionlock.py on server
   - Set FORJA_MIN_VERSION=1.0.0 (or per key min_version in admin)
6) Deploy server online:
   - Use license_server_railway/ folder (Docker)
   - Reality: Railway Free gives $5 trial then $1/month credit; may sleep on inactivity if enabled. citeturn0search8turn0search1
