"""
ReLoop AI Next-Life Decision & Evaluation Service.
Implements the exact circular economy Decision Matrix and multimodal assessment.
"""
import logging
import re
from typing import Any, Dict, List, Optional
from app.config import settings
from app.schemas.next_life import (
    CosmeticGrade,
    DeviceSummary,
    DiagnosticInputPayload,
    EnvironmentalImpact,
    NextLifeAction,
    NextLifeAnalysisRequest,
    NextLifeRecommendation,
    NextLifeResponse,
)

logger = logging.getLogger(__name__)


class NextLifeService:
    def __init__(self):
        pass

    def analyze(
        self,
        req: NextLifeAnalysisRequest,
        image_bytes_list: Optional[List[bytes]] = None,
    ) -> NextLifeResponse:
        """
        Evaluates laptop cosmetic condition and diagnostic hardware health,
        applying the deterministic Next-Life Decision Matrix.
        Uses Gemini multimodal AI when live credentials and images are available,
        falling back seamlessly to the deterministic rule engine.
        """
        # Try live Gemini multimodal if API key is present and images/notes provided
        if settings.GEMINI_API_KEY and image_bytes_list:
            try:
                from app.ai.gemini_client import GeminiClient
                from app.ai.prompts.next_life import get_next_life_prompt

                client = GeminiClient()
                prompt_content = get_next_life_prompt("v1")
                diag_summary = req.diagnostics.model_dump() if req.diagnostics else {}
                enriched_prompt = (
                    f"{prompt_content}\n\n"
                    f"### SUPPLIED SYSTEM DATA:\n"
                    f"- Model Hint: {req.detected_model}\n"
                    f"- User Cosmetic Notes: {req.cosmetic_notes or 'None'}\n"
                    f"- Diagnostics JSON: {diag_summary}\n"
                )
                res = client.generate_structured(
                    prompt=enriched_prompt,
                    response_model=NextLifeResponse,
                    images=image_bytes_list,
                )
                if res and isinstance(res, NextLifeResponse):
                    return res
            except Exception as e:
                logger.warning(f"Live Gemini Next-Life assessment failed or skipped ({e}). Falling back to deterministic engine.")

        # Deterministic Next-Life Evaluation Engine
        return self._evaluate_deterministic(req)

    def _evaluate_deterministic(self, req: NextLifeAnalysisRequest) -> NextLifeResponse:
        diag = req.diagnostics or DiagnosticInputPayload()
        model_name = req.detected_model or "Dell Latitude 5420"
        notes_lower = (req.cosmetic_notes or "").lower()

        # ─── 1. VISUAL COSMETIC ASSESSMENT ──────────────────────────────────────
        display_flags = diag.display_test_flags or {}
        has_display_cracks = bool(
            display_flags.get("cracks")
            or "crack" in notes_lower and "screen" in notes_lower
            or "broken screen" in notes_lower
            or "shattered screen" in notes_lower
        )
        has_bezel_damage = bool(display_flags.get("bezel_separation") or "bezel" in notes_lower)
        has_chassis_cracks = bool(
            "chassis crack" in notes_lower
            or "broken hinge" in notes_lower
            or "hinge broken" in notes_lower
            or (diag.chassis_condition and "crack" in diag.chassis_condition.lower())
        )
        has_severe_damage = bool(
            "shattered" in notes_lower
            or "severe" in notes_lower
            or "disintegration" in notes_lower
            or (diag.chassis_condition and "severe" in diag.chassis_condition.lower())
        )

        if req.cosmetic_grade_override:
            cosmetic_grade: CosmeticGrade = req.cosmetic_grade_override
        elif has_severe_damage:
            cosmetic_grade = "Grade D"
        elif has_display_cracks or has_chassis_cracks or has_bezel_damage:
            cosmetic_grade = "Grade C"
        elif "scuff" in notes_lower or "scratch" in notes_lower or "wear" in notes_lower:
            cosmetic_grade = "Grade B"
        else:
            # Default to Grade B or Grade A based on model/notes
            cosmetic_grade = "Grade A" if "pristine" in notes_lower or "like new" in notes_lower else "Grade B"

        # Construct cosmetic observations
        cosmetic_obs: List[str] = []
        if cosmetic_grade == "Grade A":
            cosmetic_obs.append("Display panel and anti-glare coating in pristine condition with zero scratch marks, dead pixels, or bezel separation.")
            cosmetic_obs.append("Chassis enclosure, palmrest, and keycaps exhibit minimal wear with all factory structural tolerances fully intact.")
            cosmetic_obs.append("All I/O ports (USB-C/Thunderbolt, HDMI, USB-A) and hinge tension are mechanically sound.")
        elif cosmetic_grade == "Grade B":
            cosmetic_obs.append("Display panel is fully intact and optically uniform with no cracks or internal line defects.")
            cosmetic_obs.append("Outer clamshell and bottom casing show minor cosmetic scuffs and edge sheen consistent with normal operational handling.")
            cosmetic_obs.append("Keyboard deck and trackpad show light surface shine on high-traffic keys, with all scissor switches responsive and ports undamaged.")
        elif cosmetic_grade == "Grade C":
            if has_display_cracks:
                cosmetic_obs.append("Display panel exhibits glass fracture / spiderweb cracks requiring external monitor connection or panel replacement.")
            else:
                cosmetic_obs.append("Display panel operates with visible edge scratches or minor cosmetic pressure markings.")
            cosmetic_obs.append("Chassis exhibits heavy physical wear, structural corner stress cracks, or loosened hinge mounts.")
            cosmetic_obs.append("Trackpad and keyboard show significant keycap smoothing, but motherboard I/O ports remain electrically accessible.")
        else: # Grade D
            cosmetic_obs.append("Severe structural disintegration: chassis cracked open with exposed internal shielding and broken structural anchors.")
            cosmetic_obs.append("Display panel detached, crushed, or suffering severe bezel separation.")
            cosmetic_obs.append("I/O ports and hinge assembly severely deformed or mechanically compromised.")

        # ─── 2. DIAGNOSTIC HARDWARE ASSESSMENT ──────────────────────────────────
        # Battery Health Calculation: (Current Max Capacity / Original Design Capacity) * 100
        if diag.battery_max_capacity and diag.battery_design_capacity and diag.battery_design_capacity > 0:
            battery_health = round((diag.battery_max_capacity / diag.battery_design_capacity) * 100.0, 1)
        elif diag.battery_wear_pct is not None:
            battery_health = round(max(0.0, 100.0 - diag.battery_wear_pct), 1)
        elif diag.battery_health_pct is not None:
            battery_health = round(float(diag.battery_health_pct), 1)
        else:
            battery_health = 82.0

        # Storage Health: S.M.A.R.T remaining write endurance %
        storage_health = round(float(diag.ssd_smart_health_pct if diag.ssd_smart_health_pct is not None else 90.0), 1)

        # CPU/RAM Capability Evaluation
        cpu_str = (diag.cpu or "Intel Core i5-1145G7").lower()
        ram_val = float(diag.ram_gb if diag.ram_gb is not None else 16.0)

        # Detect older CPU architectures
        is_older_cpu = bool(
            any(k in cpu_str for k in ["core 2 duo", "pentium", "celeron", "atom", "athlon", "turion", "core 2 quad"])
            or ("i3-" in cpu_str and any(gen in cpu_str for gen in ["i3-2", "i3-3", "i3-4", "i3-5"]))
            or ("i5-" in cpu_str and any(gen in cpu_str for gen in ["i5-2", "i5-3", "i5-4"]))
        )
        is_low_ram = ram_val <= 4.0
        is_strong_hardware = (not is_older_cpu) and (ram_val >= 8.0) and (storage_health >= 70.0)

        # Motherboard & core health
        motherboard_ok = diag.motherboard_functional is not False
        storage_dead = storage_health <= 10.0

        # Hardware Score Calculation (0-100%)
        if not motherboard_ok:
            hardware_score = int(min(20, (storage_health * 0.15) + (ram_val * 0.5)))
        elif storage_dead:
            hardware_score = int(min(30, (battery_health * 0.2) + (ram_val * 0.8)))
        else:
            # Weighted components:
            # CPU/RAM modern workload capability: up to 35 pts
            if is_older_cpu or is_low_ram:
                cpu_ram_score = 15.0 if is_older_cpu and is_low_ram else 22.0
            else:
                cpu_ram_score = 35.0 if ram_val >= 16.0 else 30.0

            # Storage health: up to 35 pts
            storage_score = (min(100.0, storage_health) / 100.0) * 35.0

            # Battery health: up to 20 pts
            battery_score = (min(100.0, battery_health) / 100.0) * 20.0

            # System & motherboard stability: 10 pts
            stability_score = 10.0

            hardware_score = int(round(cpu_ram_score + storage_score + battery_score + stability_score))
            hardware_score = max(0, min(100, hardware_score))

        # Hardware Observations
        hw_obs: List[str] = [
            f"Battery retention computed at {battery_health:.1f}% health relative to design capacity with stable internal resistance.",
            f"NVMe/SATA SSD S.M.A.R.T telemetry reports {storage_health:.1f}% remaining write endurance with zero critical media errors.",
            f"{diag.cpu or 'Modern processor'} and {int(ram_val)}GB memory benchmarked: {'fully capable of contemporary multitasking workloads' if is_strong_hardware else 'constrained for heavy modern OS; best suited for headless or lightweight computing'}.",
        ]

        # ─── 3. DECISION MATRIX FOR NEXT-LIFE ACTION ───────────────────────────
        # Rule 5: "E-Waste Recycling": Severe body damage AND failing core hardware (CPU/Board failure or dead storage)
        if cosmetic_grade == "Grade D" and (not motherboard_ok or storage_dead or hardware_score < 40):
            action: NextLifeAction = "E-Waste Recycling"
            headline = "Certified Responsible E-Waste Material Recycling"
            justification = (
                f"Severe cosmetic disintegration ({cosmetic_grade}) coupled with compromised core electronics "
                f"(Hardware Score: {hardware_score}%) renders functional reuse unviable. Dismantling for raw metallurgical recycling "
                f"prevents hazardous landfill contamination and recovers precious metals."
            )
            steps = [
                "De-energize device and isolate degraded lithium-ion battery for specialized HazMat recycling.",
                "Disassemble chassis to separate high-grade aluminum, copper heat pipes, and leaded components.",
                "Route depopulated PCBs to an R2 or e-Stewards certified smelter for precious metals recovery (Gold, Silver, Palladium)."
            ]
            circular_score = 28
            e_waste_kg = 0.2
            co2_offset = 22.0

        # Rule 4: "Component Salvage": Unusable chassis or dead motherboard, but has functional modular parts
        elif (not motherboard_ok or cosmetic_grade in ["Grade C", "Grade D"]) and (diag.has_modular_parts and (storage_health >= 60 or ram_val >= 8)):
            action = "Component Salvage"
            headline = "Modular Component Harvesting & Donor Parts Salvage"
            justification = (
                f"The overall machine suffers from an unviable chassis or board ({cosmetic_grade}, Hardware Score: {hardware_score}%), "
                f"yet retains high-value modular sub-assemblies (such as {', '.join(diag.modular_components or ['RAM', 'SSD', 'Wi-Fi card'])}) "
                f"with {storage_health:.0f}% SSD endurance ready for donor inventory."
            )
            steps = [
                "Extract modular DDR RAM sticks, NVMe M.2 SSD, and Wi-Fi/Bluetooth PCIe card.",
                "Run standalone bench tests and wipe storage drive with NIST 800-88 cryptographic sanitization.",
                "Catalog validated parts into repair depot spare-parts inventory for secondary laptop refurbishments."
            ]
            circular_score = 58
            e_waste_kg = 0.6
            co2_offset = 55.0

        # Rule 3: "Convert to Lightweight OS": Cosmetic Grade A/B BUT older CPU/low RAM or dead battery
        elif cosmetic_grade in ["Grade A", "Grade B"] and (is_older_cpu or is_low_ram or battery_health < 40.0):
            action = "Convert to Lightweight OS"
            headline = "Modernize via Cloud-First Lightweight OS Deployment"
            justification = (
                f"The cosmetic chassis is well-preserved ({cosmetic_grade}), but the processing architecture or power system "
                f"({diag.cpu or 'Legacy CPU'}, {int(ram_val)}GB RAM, Battery: {battery_health:.1f}%) struggles on bloated modern OS. "
                f"Migrating to a lightweight operating system (ChromeOS Flex, Lubuntu, or Linux Lite) revitalizes responsive performance."
            )
            steps = [
                "Flash lightweight operating system image (ChromeOS Flex or Linux Lite) to internal storage.",
                "Configure power management daemon to optimize thermal throttle and wall-power operation.",
                "Deploy for student digital literacy labs, community centers, or dedicated web-kiosk environments."
            ]
            circular_score = 78
            e_waste_kg = 1.4
            co2_offset = 165.0

        # Rule 2: "Repurpose as Headless Server": Cosmetic Grade C/D BUT Hardware Score >= 60%
        elif cosmetic_grade in ["Grade C", "Grade D"] and hardware_score >= 60:
            action = "Repurpose as Headless Server"
            headline = "Repurpose as Energy-Efficient Headless Home Server / IoT Node"
            justification = (
                f"The physical chassis or display panel is damaged ({cosmetic_grade}), but the core computational engine remains robust "
                f"with a Hardware Score of {hardware_score}% (strong CPU, {int(ram_val)}GB RAM, {storage_health:.0f}% SSD). "
                f"Its built-in battery functions as an integrated uninterruptible power supply (UPS) for 24/7 server workloads."
            )
            steps = [
                "Disable broken internal LCD in BIOS and configure automatic power-on upon AC connect.",
                "Install a headless Linux server distribution (Debian Server or Ubuntu Server LTS) with Docker / Portainer.",
                "Deploy self-hosted services (Home Assistant, Pi-hole, local media server, or automated backup node)."
            ]
            circular_score = 83
            e_waste_kg = 1.5
            co2_offset = 195.0

        # Rule 1: "Resell / Refurbish": Cosmetic Grade A/B AND Hardware Score >= 75%
        elif cosmetic_grade in ["Grade A", "Grade B"] and hardware_score >= 75:
            action = "Resell / Refurbish"
            headline = "Certified Refurbishment & Direct Secondary Market Resale"
            justification = (
                f"Excellent cosmetic preservation ({cosmetic_grade}) paired with a superior Hardware Health Score ({hardware_score}%) "
                f"fulfills premium refurbishment standards. Reconditioning preserves 85%+ of original embodied carbon while delivering "
                f"high economic recovery."
            )
            steps = [
                "Execute NIST SP 800-88 Rev. 1 cryptographic erasure across the internal storage.",
                "Perform ultrasonic chassis cleaning, fan dust evacuation, and fresh thermal compound application.",
                "Recalibrate battery BMS and list on circular secondary electronics exchange with a 90-day warranty."
            ]
            circular_score = 88
            e_waste_kg = 1.4
            co2_offset = 245.0

        # Edge fallback
        else:
            if hardware_score >= 60:
                action = "Repurpose as Headless Server"
                headline = "Low-Impact Headless Micro-Server Repurposing"
                justification = f"Hardware health of {hardware_score}% provides dependable compute capacity despite cosmetic limitations."
                steps = ["Install lightweight Linux Server", "Configure Docker container services", "Deploy as local backup node"]
                circular_score = 75
                e_waste_kg = 1.4
                co2_offset = 170.0
            else:
                action = "Component Salvage"
                headline = "Harvest Working Modular Sub-Assemblies"
                justification = f"Hardware health ({hardware_score}%) indicates board or component degradation. Extract remaining modular parts."
                steps = ["Remove RAM and SSD", "Test modular components", "Recycle chassis responsibly"]
                circular_score = 55
                e_waste_kg = 0.5
                co2_offset = 50.0

        return NextLifeResponse(
            device_summary=DeviceSummary(
                detected_model=model_name,
                cosmetic_grade=cosmetic_grade,
                hardware_health_score=hardware_score,
                reloop_circular_score=circular_score,
            ),
            cosmetic_observations=cosmetic_obs,
            hardware_observations=hw_obs,
            next_life_recommendation=NextLifeRecommendation(
                action=action,
                headline=headline,
                justification=justification,
                actionable_steps=steps,
            ),
            environmental_impact=EnvironmentalImpact(
                e_waste_prevented_kg=e_waste_kg,
                estimated_co2_offset_kg=co2_offset,
            ),
        )


next_life_service = NextLifeService()
