import { NextRequest, NextResponse } from "next/server";
import { MVP_SUPPORTED_MODELS, VisualObservation } from "@/types/assessment";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { images, selectedModelId } = body;

    if (!images || !Array.isArray(images) || images.length === 0) {
      return NextResponse.json(
        { error: "At least one image is required for visual inspection." },
        { status: 400 }
      );
    }

    // Default model match or selection
    let matchedModel = MVP_SUPPORTED_MODELS[0]; // Dell Latitude 5420 default
    let confidence = 0.91;

    if (selectedModelId) {
      const found = MVP_SUPPORTED_MODELS.find((m) => m.id === selectedModelId);
      if (found) {
        matchedModel = found;
        confidence = 1.0;
      }
    } else {
      // Simulate realistic model identification with confidence based on image count
      if (images.length >= 2) {
        matchedModel = MVP_SUPPORTED_MODELS[0]; // Dell Latitude 5420
        confidence = 0.91;
      } else {
        matchedModel = MVP_SUPPORTED_MODELS[0];
        confidence = 0.78;
      }
    }

    // Mock/Structured Vision AI Observations based on image visual evidence
    // Rules: ONLY visible physical characteristics. NO internal health claims!
    const visibleObservations: VisualObservation[] = [
      {
        id: "vis-chassis-1",
        component: "chassis",
        condition: "surface_scratches",
        observation: "Minor cosmetic scratches near palm rest and top lid edge",
        confidence: 0.88,
      },
      {
        id: "vis-display-1",
        component: "display",
        condition: "no_visible_damage",
        observation: "Screen glass intact; no visible cracks or surface delamination detected",
        confidence: 0.94,
      },
      {
        id: "vis-keyboard-1",
        component: "keyboard",
        condition: "minor_wear",
        observation: "Keyboard keycaps present; slight key shine on spacebar and E key",
        confidence: 0.85,
      },
      {
        id: "vis-hinge-1",
        component: "hinge",
        condition: "no_visible_damage",
        observation: "Hinge alignment appears normal with uniform gap clearance",
        confidence: 0.82,
      },
      {
        id: "vis-ports-1",
        component: "ports",
        condition: "no_visible_damage",
        observation: "USB-C and HDMI port housing clean and free of visible dust or debris",
        confidence: 0.87,
      },
    ];

    return NextResponse.json({
      success: true,
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
      { error: "Unable to analyze these images right now. Please try again." },
      { status: 500 }
    );
  }
}
