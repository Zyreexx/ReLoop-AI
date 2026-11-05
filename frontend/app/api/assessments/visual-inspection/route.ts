import { NextRequest, NextResponse } from "next/server";
import { MVP_SUPPORTED_MODELS, VisualObservation } from "@/types/assessment";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { images, selectedModelId, fileNames, hint } = body;

    if (!images || !Array.isArray(images) || images.length === 0) {
      return NextResponse.json(
        { error: "At least one image is required for visual inspection." },
        { status: 400 }
      );
    }

    // Check for Gemini API Key in header, body, or environment
    const geminiApiKey =
      req.headers.get("x-gemini-api-key") ||
      body.apiKey ||
      process.env.GEMINI_API_KEY ||
      process.env.NEXT_PUBLIC_GEMINI_API_KEY;

    // Check if we can run direct Gemini Vision analysis on uploaded images
    if (geminiApiKey && images && images.length > 0) {
      try {
        const imageParts: any[] = [];
        for (const img of images.slice(0, 3)) {
          if (typeof img === "string" && img.startsWith("data:")) {
            const parts = img.split(",", 2);
            const mime = parts[0].split(";")[0].replace("data:", "") || "image/jpeg";
            imageParts.push({
              inline_data: {
                mime_type: mime,
                data: parts[1],
              },
            });
          }
        }

        if (imageParts.length > 0) {
          const supportedList = MVP_SUPPORTED_MODELS.map(
            (m) => `- ${m.manufacturer} ${m.model}`
          ).join("\n");

          const prompt = `You are an expert optical laptop hardware identifier and physical defect evaluator.
Examine the laptop image(s) and identify the exact manufacturer and model name.
Also inspect visible hardware in the photos for physical damage across:
- display (cracks, fractures, panel damage, or intact glass)
- keyboard (loose keys, missing keycaps, broken scissor switches, or all keys intact)
- charging ports & I/O (bent pins, broken connectors, debris obstruction, or clean ports)
- chassis & hinges (cracks, dents, hinge misalignment, or structurally solid)

Preferred primary catalog models:
${supportedList}

Output pure JSON in this format:
{
  "manufacturer": "<e.g. Dell, Apple, Lenovo, HP, Asus, Acer>",
  "model": "<e.g. Latitude 5420, MacBook Air M1, ThinkPad T14 Gen 1, XPS 13, etc.>",
  "confidence": 0.95,
  "visual_clues": ["<clue 1>", "<clue 2>"],
  "visible_label_text": "<read text or null>",
  "display_cracks": [],
  "keyboard_faults": [],
  "port_faults": [],
  "chassis_faults": [],
  "components_inspected_clean": ["display", "keyboard", "ports", "chassis"]
}`;

          const candidateModels = [
            "gemini-flash-latest",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3.5-flash",
          ];
          let rawText = "";

          for (const model of candidateModels) {
            try {
              const geminiRes = await fetch(
                `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${geminiApiKey}`,
                {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    contents: [
                      {
                        parts: [{ text: prompt }, ...imageParts],
                      },
                    ],
                    generationConfig: {
                      responseMimeType: "application/json",
                    },
                  }),
                }
              );

              if (geminiRes.ok) {
                const geminiData = await geminiRes.json();
                const text =
                  geminiData.candidates?.[0]?.content?.parts?.[0]?.text;
                if (text) {
                  rawText = text;
                  break;
                }
              }
            } catch {
              continue;
            }
          }

          if (rawText) {
            const parsed = JSON.parse(rawText);
            const detectedModel =
              parsed.model ||
              parsed.model_name ||
              parsed.identification ||
              parsed.series ||
              "";
            const detectedMfr = parsed.manufacturer || parsed.brand || "Laptop";

            if (detectedModel && detectedModel.toLowerCase() !== "unknown") {
              const conf = parsed.confidence || 0.92;
              const observations: VisualObservation[] = [];

              // Display findings
              const dispCracks: string[] = Array.isArray(parsed.display_cracks) ? parsed.display_cracks : [];
              if (dispCracks.length > 0) {
                dispCracks.forEach((c: string, idx: number) => {
                  observations.push({
                    id: `vis-disp-${idx + 1}`,
                    component: "display",
                    condition: "visible_crack",
                    severity: "HIGH",
                    observation: c,
                    confidence: conf,
                    source: "DAMAGE_ANALYSIS",
                  });
                });
              } else if (Array.isArray(parsed.components_inspected_clean) && parsed.components_inspected_clean.includes("display")) {
                observations.push({
                  id: "vis-disp-clean",
                  component: "display",
                  condition: "no_visible_damage",
                  severity: "NONE",
                  observation: "Display panel and glass clearly visible with no cracks or fractures detected",
                  confidence: conf,
                  source: "DAMAGE_ANALYSIS",
                });
              }

              // Keyboard findings
              const kbFaults: string[] = Array.isArray(parsed.keyboard_faults) ? parsed.keyboard_faults : [];
              if (kbFaults.length > 0) {
                kbFaults.forEach((k: string, idx: number) => {
                  const isLoose = /loose|unseated|wobbly|detached/i.test(k);
                  observations.push({
                    id: `vis-kb-${idx + 1}`,
                    component: "keyboard",
                    condition: isLoose ? "loose_part" : "missing_key",
                    severity: "MODERATE",
                    observation: k,
                    confidence: conf,
                    source: "DAMAGE_ANALYSIS",
                  });
                });
              } else if (Array.isArray(parsed.components_inspected_clean) && parsed.components_inspected_clean.includes("keyboard")) {
                observations.push({
                  id: "vis-kb-clean",
                  component: "keyboard",
                  condition: "no_visible_damage",
                  severity: "NONE",
                  observation: "Keyboard layout clearly visible with all keycaps intact and aligned",
                  confidence: conf,
                  source: "DAMAGE_ANALYSIS",
                });
              }

              // Ports findings
              const portFaults: string[] = Array.isArray(parsed.port_faults) ? parsed.port_faults : [];
              if (portFaults.length > 0) {
                portFaults.forEach((p: string, idx: number) => {
                  observations.push({
                    id: `vis-port-${idx + 1}`,
                    component: "ports",
                    condition: "port_damage",
                    severity: "MODERATE",
                    observation: p,
                    confidence: conf,
                    source: "DAMAGE_ANALYSIS",
                  });
                });
              } else if (Array.isArray(parsed.components_inspected_clean) && parsed.components_inspected_clean.includes("ports")) {
                observations.push({
                  id: "vis-port-clean",
                  component: "ports",
                  condition: "no_visible_damage",
                  severity: "NONE",
                  observation: "Charging ports and external I/O clean with no pin or connector damage",
                  confidence: conf,
                  source: "DAMAGE_ANALYSIS",
                });
              }

              // Chassis findings
              const chassisFaults: string[] = Array.isArray(parsed.chassis_faults) ? parsed.chassis_faults : [];
              if (chassisFaults.length > 0) {
                chassisFaults.forEach((c: string, idx: number) => {
                  const isCrack = /crack|fracture|split|broken/i.test(c);
                  observations.push({
                    id: `vis-chassis-${idx + 1}`,
                    component: "chassis",
                    condition: isCrack ? "visible_crack" : "minor_wear",
                    severity: isCrack ? "HIGH" : "LOW",
                    observation: c,
                    confidence: conf,
                    source: "DAMAGE_ANALYSIS",
                  });
                });
              } else if (Array.isArray(parsed.components_inspected_clean) && parsed.components_inspected_clean.includes("chassis")) {
                observations.push({
                  id: "vis-chassis-clean",
                  component: "chassis",
                  condition: "no_visible_damage",
                  severity: "NONE",
                  observation: "Chassis casing and hinges structurally solid with normal alignment",
                  confidence: conf,
                  source: "DAMAGE_ANALYSIS",
                });
              }

              // General clues
              (parsed.visual_clues || parsed.distinguishing_features || []).forEach((clue: string, i: number) => {
                if (!observations.some((o) => o.observation.toLowerCase().includes(clue.toLowerCase()))) {
                  observations.push({
                    id: `vis-gemini-${i + 1}`,
                    component: "chassis",
                    condition: "no_visible_damage",
                    observation: clue,
                    confidence: conf,
                    source: "MODEL_IDENTIFICATION",
                  });
                }
              });

              if (observations.length === 0) {
                observations.push({
                  id: "vis-gemini-1",
                  component: "chassis",
                  condition: "no_visible_damage",
                  observation: `Identified as ${detectedMfr} ${detectedModel} from optical inspection`,
                  confidence: conf,
                });
              }

              return NextResponse.json({
                success: true,
                identified_product: {
                  manufacturer: detectedMfr,
                  model: detectedModel,
                  confidence: parsed.confidence || 0.92,
                  confirmed: (parsed.confidence || 0.92) >= 0.85,
                  visible_label_text: parsed.visible_label_text || null,
                },
                visible_observations: observations,
              });
            }
          }
        }
      } catch (geminiErr) {
        console.warn("[Gemini API fallback]", geminiErr);
      }
    }

    // Combine any text clues from file names or hints
    const cluesText = [
      hint || "",
      Array.isArray(fileNames) ? fileNames.join(" ") : (fileNames || ""),
      images.filter((img: any) => typeof img === "string" && !img.startsWith("data:")).join(" "),
    ].join(" ").toLowerCase();

    // Manual selection with exact selectedModelId matching across supported models
    let matchedModel: any = null;
    let confidence = 0.85;

    if (selectedModelId) {
      const found = MVP_SUPPORTED_MODELS.find((m) => m.id === selectedModelId);
      if (found) {
        matchedModel = found;
        confidence = 1.0;
      }
    }

    if (!matchedModel) {
      return NextResponse.json({
        success: false,
        status: "UNKNOWN",
        message: "Model could not be identified. Your device may not be in the currently supported catalog. Please select your model manually to continue.",
        identified_product: null,
        visible_observations: [],
      });
    }

    // Manual model selection fallback (no fake defects or hardcoded wear)
    const visibleObservations: VisualObservation[] = [
      {
        id: "vis-chassis-manual",
        component: "chassis",
        condition: "no_visible_damage",
        observation: `Manually confirmed hardware profile for ${matchedModel.manufacturer} ${matchedModel.model}`,
        confidence: 1.0,
        severity: "NONE",
      },
    ];

    return NextResponse.json({
      success: true,
      status: "IDENTIFIED",
      identified_product: {
        manufacturer: matchedModel.manufacturer,
        model: matchedModel.model,
        confidence,
        confirmed: confidence === 1.0,
      },
      visible_observations: visibleObservations,
    });
  } catch (error: any) {
    return NextResponse.json(
      { error: "Unable to analyze these images right now. Please try again.", status: "AI_UNAVAILABLE" },
      { status: 500 }
    );
  }
}
