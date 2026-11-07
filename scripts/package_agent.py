"""
ReLoop AI Diagnostics Agent Packaging Script.
Builds standalone, zero-dependency executable for Windows, macOS, or Linux using PyInstaller.
"""
import os
import platform
import shutil
import subprocess
import sys

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    agent_dir = os.path.join(repo_root, "diagnostics_agent")
    entrypoint = os.path.join(agent_dir, "runner.py")
    dist_dir = os.path.join(repo_root, "dist")
    build_dir = os.path.join(repo_root, "build", "agent")
    frontend_public_downloads = os.path.join(repo_root, "frontend", "public", "downloads")
    frontend_public_root = os.path.join(repo_root, "frontend", "public")
    
    os.makedirs(frontend_public_downloads, exist_ok=True)
    os.makedirs(dist_dir, exist_ok=True)
    
    current_os = platform.system().lower()
    binary_name = "reloop-agent.exe" if current_os == "windows" else "reloop-agent"

    print("================================================================================")
    print(f"  Packaging ReLoop AI Diagnostics Agent for [{platform.system()}]")
    print(f"  Target: {os.path.join(dist_dir, binary_name)}")
    print("================================================================================")

    # Locate pyinstaller in python environment
    pyinstaller_bin = shutil.which("pyinstaller")
    if not pyinstaller_bin:
        venv_scripts = os.path.join(repo_root, "backend", ".venv", "Scripts", "pyinstaller.exe")
        if os.path.exists(venv_scripts):
            pyinstaller_bin = venv_scripts
        else:
            venv_bin = os.path.join(repo_root, "backend", ".venv", "bin", "pyinstaller")
            if os.path.exists(venv_bin):
                pyinstaller_bin = venv_bin

    if not pyinstaller_bin:
        print("[!] PyInstaller executable not found in PATH or virtualenv. Exiting.")
        sys.exit(1)

    cmd = [
        pyinstaller_bin,
        "--onefile",
        "--clean",
        "--name", os.path.splitext(binary_name)[0],
        "--distpath", dist_dir,
        "--workpath", build_dir,
        "--specpath", os.path.join(repo_root, "build"),
        "--paths", repo_root,
        entrypoint,
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=repo_root)

    if result.returncode != 0:
        print(f"[!] PyInstaller build failed with returncode {result.returncode}")
        sys.exit(result.returncode)

    built_binary = os.path.join(dist_dir, binary_name)
    if os.path.exists(built_binary):
        print(f"\n[+] Executable successfully generated: {built_binary} ({os.path.getsize(built_binary)} bytes)")
        
        # Copy to frontend public directories
        target_dl = os.path.join(frontend_public_downloads, binary_name)
        shutil.copy2(built_binary, target_dl)
        print(f"[+] Staged to web downloads: {target_dl}")
        
        # Also maintain compatibility with reloop_agent.exe name
        compat_name = "reloop_agent.exe" if current_os == "windows" else "reloop_agent"
        target_compat = os.path.join(frontend_public_root, compat_name)
        shutil.copy2(built_binary, target_compat)
        print(f"[+] Staged to web root: {target_compat}")
        print("\n[OK] Diagnostics Agent packaging complete and verified!")
    else:
        print(f"[!] Target binary not found at expected location: {built_binary}")
        sys.exit(1)

if __name__ == "__main__":
    main()

