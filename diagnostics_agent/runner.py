"""
CLI Runner for ReLoop AI Cross-Platform Smart Diagnostics Agent.
Zero external dependencies (Python standard library only).
"""
import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from typing import Any, Dict, Optional
from diagnostics_agent.os_detect import detect_os
from diagnostics_agent.collector import StructuredCollector

AGENT_VERSION = "1.2.0"

CONSENT_TEXT = """
================================================================================
                    ReLoop AI — Smart Hardware Diagnostics
                     The Next-Life Engine for Electronics
================================================================================

[PRIVACY & SECURITY NOTICE]
ReLoop AI evaluates your laptop's internal hardware condition to identify
potential faults and determine the optimal circular lifecycle pathway
(Repair, Upgrade, Refurbish, Reuse, Component Recovery, or Recycling).

Scope of Diagnostic Collection:
  1. Battery: Design capacity, full charge capacity, cycle count, wear rate.
  2. Storage: SMART health, drive model, capacity, failure predictions.
  3. Memory: Installed RAM capacity, slots, hardware error events.
  4. Thermals: Temperature ranges, active/logged thermal throttling events.
  5. Processor: CPU model, core architecture, clock speed, machine checks.
  6. Display: Resolution, refresh rate, graphics controller operational status.
  7. Keyboard: Input controller presence and driver operational health.
  8. Chassis: Form factor identifier and structural inspection guidance.
  9. System Board: Motherboard model, BIOS/UEFI version, POST status.

Security Guarantees:
  - 100% Read-Only: Will NOT execute destructive disk operations or alter settings.
  - Zero Personal Data: Will NEVER access passwords, browser history, or personal files.
  - No Silent Installs: Will NOT install drivers or software.
  - Data sent only to your active ReLoop session.
================================================================================
"""


def prompt_consent() -> bool:
    print(CONSENT_TEXT)
    try:
        reply = input("Do you allow ReLoop AI to run these hardware diagnostics? [y/N]: ").strip().lower()
        return reply in ["y", "yes"]
    except (KeyboardInterrupt, EOFError):
        print("\nDiagnostics cancelled.")
        return False


def submit_results(api_url: str, session_token: str, payload: Dict[str, Any]) -> bool:
    endpoint = f"{api_url.rstrip('/')}/api/diagnostics/session/{session_token}/submit"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "ReLoop-DiagnosticsAgent/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status in [200, 201]:
                return True
            else:
                print(f"Server responded with status code: {resp.status}")
                return False
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        print(f"HTTP Error {e.code}: {err_msg}")
        return False
    except Exception as e:
        print(f"Failed to submit diagnostics to ReLoop backend: {str(e)}")
        return False


def run_health_check(api_url: Optional[str] = None) -> Dict[str, Any]:
    """Run an automated diagnostic environment and capability health check."""
    os_info = detect_os()
    checks: Dict[str, Any] = {
        "os_supported": os_info.system in ["Windows", "Darwin", "Linux"],
        "os_system": os_info.system,
        "os_release": os_info.release,
        "os_architecture": os_info.machine,
        "is_admin": os_info.is_admin,
        "available_tools": os_info.available_tools,
    }

    adapter_ok = False
    try:
        collector = StructuredCollector(os_info)
        adapter_ok = collector.adapter is not None
    except Exception as e:
        checks["adapter_error"] = str(e)
    checks["adapter_initialized"] = adapter_ok

    backend_reachable = None
    if api_url:
        try:
            req = urllib.request.Request(f"{api_url.rstrip('/')}/health", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                backend_reachable = resp.status == 200
        except Exception:
            backend_reachable = False
    checks["backend_reachable"] = backend_reachable

    status = "HEALTHY" if (checks["os_supported"] and adapter_ok) else "DEGRADED"
    return {
        "status": status,
        "version": AGENT_VERSION,
        "timestamp": time.time(),
        "checks": checks,
    }


def main():
    parser = argparse.ArgumentParser(
        description="ReLoop AI Cross-Platform Smart Diagnostics Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"ReLoop AI Diagnostics Agent v{AGENT_VERSION}",
    )
    parser.add_argument(
        "--health", "--check-health",
        action="store_true",
        help="Run environment health check and verify hardware diagnostic capabilities",
    )
    parser.add_argument("--token", type=str, help="Session token provided by the ReLoop web interface")
    parser.add_argument("--api-url", type=str, default="http://127.0.0.1:8000", help="ReLoop backend API base URL")
    parser.add_argument("--consent", action="store_true", help="Explicitly grant consent without interactive prompt")
    parser.add_argument("--dry-run", action="store_true", help="Run diagnostics locally without transmitting to backend")
    parser.add_argument("--json-output", type=str, help="Optional filepath to save diagnostic JSON output")

    args = parser.parse_args()

    if args.health:
        health_data = run_health_check(args.api_url)
        if args.json_output:
            with open(args.json_output, "w", encoding="utf-8") as f:
                json.dump(health_data, f, indent=2)
            print(f"[+] Health check report written to: {args.json_output}")
        else:
            print(f"\n================================================================================")
            print(f"       ReLoop AI Diagnostics Agent v{health_data['version']} — Health Status: [{health_data['status']}]")
            print(f"================================================================================")
            checks = health_data["checks"]
            print(f"  Operating System      : {checks['os_system']} {checks['os_release']} ({checks['os_architecture']})")
            print(f"  Platform Supported    : {'[OK]' if checks['os_supported'] else '[FAIL]'}")
            print(f"  Privileges            : {'[Elevated / Admin]' if checks['is_admin'] else '[Standard User]'}")
            print(f"  Adapter Initialized   : {'[OK]' if checks['adapter_initialized'] else '[FAIL]'}")
            if checks["backend_reachable"] is not None:
                print(f"  Backend ({args.api_url}): {'[Reachable]' if checks['backend_reachable'] else '[Unreachable / Offline]'}")
            print(f"  Available Utilities   : {', '.join(k for k, v in checks['available_tools'].items() if v) or 'None'}")
            print("================================================================================\n")
        sys.exit(0 if health_data["status"] == "HEALTHY" else 1)

    if not args.consent and not args.dry_run:
        if not prompt_consent():
            print("Consent not granted. Exiting diagnostics safely with zero changes made.")
            sys.exit(0)

    print("\n[+] Inspecting operating system and available hardware interfaces...")
    os_info = detect_os()
    print(f"    Operating System : {os_info.system} {os_info.release} ({os_info.machine})")
    print(f"    Privilege Level  : {'Administrator / Root' if os_info.is_admin else 'Standard User'}")

    print("\n[+] Initializing hardware telemetry collector...")
    collector = StructuredCollector(os_info)

    def on_progress(key: str, status: str, details: Dict[str, Any]):
        if status == "Running":
            name = details.get("name", key)
            print(f"    [*] Testing {name:<38} ... ", end="", flush=True)
        else:
            badge = f"[{status}]"
            comp_st = details.get("component_status", "")
            if comp_st:
                badge += f" (Condition: {comp_st})"
            print(badge)

    start_time = time.time()
    results = collector.collect_all(progress_cb=on_progress)
    duration = time.time() - start_time

    print(f"\n[+] Diagnostic scan completed in {duration:.2f}s.")
    print(f"    Overall Hardware Status : {results['overall_status']}")
    print(f"    Faults Detected         : {results['total_faults_count']}")

    if results["faults"]:
        print("\n[!] Detected Hardware Anomalies:")
        for f in results["faults"]:
            print(f"    - [{f['severity']}] {f['component'].upper()}: {f['description']}")

    # Save to JSON file if requested
    if args.json_output:
        try:
            with open(args.json_output, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
            print(f"\n[+] Detailed diagnostic report saved to: {args.json_output}")
        except Exception as e:
            print(f"[!] Warning: Could not write JSON output file: {str(e)}")

    if args.dry_run:
        print("\n[+] Dry run complete. Telemetry was not submitted to server.")
        return

    if not args.token:
        print("\n[!] No session token specified. Run with --token <SESSION_TOKEN> to link with your web assessment.")
        print("    Alternatively, use the JSON output file or copy values to manual entry.")
        return

    print(f"\n[+] Transmitting hardware findings to ReLoop backend ({args.api_url})...")
    if submit_results(args.api_url, args.token, results):
        print("[OK] Telemetry securely delivered! You may now return to your browser to view the evaluation.")
    else:
        print("[!] Transmission failed. You can export results with --json-output and upload manually.")


if __name__ == "__main__":
    main()
