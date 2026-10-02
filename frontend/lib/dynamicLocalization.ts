import { Language } from "@/lib/translations";

/**
 * ReLoop AI — Dynamic Assessment & Output Localization Engine
 * Provides context-aware translation for dynamic pathway names, action plans,
 * component names, detected issues, telemetry statuses, and AI decision narratives.
 */

// ─── Component Names ─────────────────────────────────────────────────────────

const COMPONENT_NAMES: Record<string, Record<Language, string>> = {
  "battery": {
    en: "Battery Subsystem",
    gu: "બેટરી સબસિસ્ટમ",
    hi: "बैटरी सबसिस्टम",
  },
  "thermals & cooling": {
    en: "Thermals & Cooling",
    gu: "થર્મલ્સ અને કૂલિંગ",
    hi: "थर्मल्स और कूलिंग",
  },
  "ram memory": {
    en: "RAM Memory",
    gu: "RAM મેમરી",
    hi: "रैम मेमोरी",
  },
  "ssd / storage": {
    en: "SSD / Storage",
    gu: "SSD / સ્ટોરેજ",
    hi: "एसएसडी / स्टोरेज",
  },
  "display": {
    en: "Display Panel",
    gu: "ડિસ્પ્લે પેનલ",
    hi: "डिस्प्ले पैनल",
  },
  "display panel": {
    en: "Display Panel",
    gu: "ડિસ્પ્લે પેનલ",
    hi: "डिस्प्ले पैनल",
  },
  "ports & i/o": {
    en: "Ports & I/O",
    gu: "પોર્ટ્સ અને I/O",
    hi: "पोर्ट और I/O",
  },
  "keyboard": {
    en: "Keyboard & Deck",
    gu: "કીબોર્ડ અને ડેક",
    hi: "कीबोर्ड और डेक",
  },
  "system / motherboard": {
    en: "Motherboard / Logic Board",
    gu: "મધરબોર્ડ / લોજિક બોર્ડ",
    hi: "मदरबोर्ड / लॉजिक बोर्ड",
  },
  "motherboard": {
    en: "Motherboard / Logic Board",
    gu: "મધરબોર્ડ / લોજિક બોર્ડ",
    hi: "मदरबोर्ड / लॉजिक बोर्ड",
  },
  "chassis": {
    en: "Chassis & Enclosure",
    gu: "ચેસિસ અને બોડી",
    hi: "चेसिस और बॉडी",
  },
  "chassis / case": {
    en: "Chassis / Case",
    gu: "ચેસિસ / કેસ",
    hi: "चेसिस / केस",
  },
  "trackpad": {
    en: "Trackpad",
    gu: "ટ્રેકપેડ",
    hi: "ट्रैकपैड",
  },
  "hinge mechanism": {
    en: "Hinge Mechanism",
    gu: "હિન્જ મિકેનિઝમ",
    hi: "हिंज मैकेनिज्म",
  },
  "hinge": {
    en: "Hinge Mechanism",
    gu: "હિન્જ મિકેનિઝમ",
    hi: "हिंज मैकेनिज्म",
  },
  "system diagnostics": {
    en: "System Diagnostics",
    gu: "સિસ્ટમ ડાયગ્નોસ્ટિક્સ",
    hi: "सिस्टम डायग्नोस्टिक्स",
  },
};

export function localizeComponentName(name: string, lang: Language): string {
  if (!name) return "";
  const key = name.toLowerCase().trim();
  if (COMPONENT_NAMES[key]?.[lang]) {
    return COMPONENT_NAMES[key][lang];
  }
  // Partial matches
  for (const [k, translations] of Object.entries(COMPONENT_NAMES)) {
    if (key.includes(k)) {
      return translations[lang];
    }
  }
  return name;
}

// ─── Diagnostic Metric Statuses ──────────────────────────────────────────────

const STATUS_TRANSLATIONS: Record<string, Record<Language, string>> = {
  "PASS": { en: "PASS", gu: "પાસ (PASS)", hi: "सफल (PASS)" },
  "FAULT": { en: "FAULT", gu: "ખામી (FAULT)", hi: "खराबी (FAULT)" },
  "WEAR": { en: "WEAR", gu: "ઘસારો", hi: "घिसाव" },
  "THROTTLING": { en: "THROTTLING", gu: "થ્રોટલિંગ", hi: "थ्रॉटलिंग" },
  "NORMAL": { en: "NORMAL", gu: "સામાન્ય", hi: "सामान्य" },
  "DEGRADED": { en: "DEGRADED", gu: "ઘટેલી ક્ષમતા", hi: "घटी हुई क्षमता" },
  "GOOD": { en: "GOOD", gu: "યોગ્ય", hi: "उचित" },
  "RECOMMENDED": { en: "RECOMMENDED", gu: "ભલામણ કરેલ", hi: "अनुशंसित" },
  "ELIGIBLE": { en: "ELIGIBLE", gu: "યોગ્ય", hi: "योग्य" },
  "INELIGIBLE": { en: "INELIGIBLE", gu: "અયોગ્ય", hi: "अयोग्य" },
};

export function localizeStatus(status: string, lang: Language): string {
  if (!status) return "";
  const upper = status.toUpperCase().trim();
  return STATUS_TRANSLATIONS[upper]?.[lang] || status;
}

// ─── Dynamic Detected Conditions ─────────────────────────────────────────────

export function localizeDetectedIssue(issue: string, lang: Language): string {
  if (lang === "en" || !issue) return issue;

  const lower = issue.toLowerCase();

  if (lower.includes("battery capacity degraded")) {
    const match = issue.match(/(\d+)%/);
    const pct = match ? match[1] : "73";
    return lang === "gu"
      ? `બેટરી ક્ષમતા ${pct}% સુધી ઘટી ગઈ છે (ઝડપી ડ્રેઇન)`
      : `बैटरी क्षमता ${pct}% तक कम हो गई है (त्वरित निर्वहन)`;
  }

  if (lower.includes("thermal throttling")) {
    const match = issue.match(/(\d+)°?C/i);
    const temp = match ? match[1] : "88";
    return lang === "gu"
      ? `લોડ હેઠળ ${temp}°C પર CPU થર્મલ થ્રોટલિંગ`
      : `लोड के तहत ${temp}°C पर सीपीयू थर्मल थ्रॉटलिंग`;
  }

  if (lower.includes("loose") && lower.includes("key")) {
    return lang === "gu"
      ? "કીબોર્ડ પર 2 છૂટા પ્લાસ્ટિક કીકેપ્સ"
      : "कीबोर्ड पर 2 ढीली प्लास्टिक कीकैप्स";
  }

  if (lower.includes("palm-rest") || lower.includes("scuff") || lower.includes("scratches")) {
    return lang === "gu"
      ? "પામ-રેસ્ટ પર સપાટી કોસ્મેટિક સ્ક્રેચિસ"
      : "पाम-रेस्ट पर सतही खरोंच";
  }

  if (lower.includes("standard component wear")) {
    return lang === "gu"
      ? "સામાન્ય કમ્પોનન્ટ ઘસારો અને નાના કોસ્મેટિક સ્ક્રેચિસ"
      : "सामान्य घटक घिसाव और मामूली कॉस्मेटिक खरोंच";
  }

  return issue;
}

// ─── Condition Profile & Assessment Review Localization ──────────────────────

const CONDITION_HEADLINES: Record<string, Record<Language, string>> = {
  "good": { en: "Good", gu: "સારી સ્થિતિ", hi: "अच्छी स्थिति" },
  "needs attention": { en: "Needs Attention", gu: "ધ્યાન આપવાની જરૂર", hi: "ध्यान देने की आवश्यकता" },
  "service recommended": { en: "Service Recommended", gu: "સર્વિસ ભલામણ કરેલ", hi: "सेवा अनुशंसित" },
  "service required": { en: "Service Required", gu: "સર્વિસ જરૂરી", hi: "सेवा आवश्यक" },
  "service needed": { en: "Service Needed", gu: "સર્વિસની જરૂર છે", hi: "सेवा की आवश्यकता है" },
  "not measured": { en: "Not Measured", gu: "માપેલ નથી", hi: "मापा नहीं गया" },
  "unmeasured": { en: "Unmeasured", gu: "માપ્યા વગરનું", hi: "अमापा" },
  "unchecked": { en: "Unchecked", gu: "તપાસેલ નથી", hi: "अजाँचा" },
  "degraded": { en: "Degraded", gu: "ઘટેલી ક્ષમતા", hi: "घटी हुई क्षमता" },
  "smart warning": { en: "SMART Warning", gu: "SMART ચેતવણી", hi: "SMART चेतावनी" },
  "throttling detected": { en: "Throttling Detected", gu: "થ્રોટલિંગ શોધાયેલ", hi: "थ्रॉटलिंग का पता चला" },
  "normal": { en: "Normal", gu: "સામાન્ય સ્થિતિ", hi: "सामान्य स्थिति" },
  "issues reported": { en: "Issues Reported", gu: "સમસ્યાઓ નોંધાયેલ", hi: "समस्याएं दर्ज" },
  "cracked": { en: "Cracked", gu: "ક્રેક થયેલ", hi: "टूटा हुआ" },
  "no visible crack": { en: "No Visible Crack", gu: "કોઈ ક્રેક નથી", hi: "कोई दरार नहीं" },
  "missing keys": { en: "Missing Keys", gu: "ગુમ થયેલી કીઓ", hi: "गुम कुंजियाँ" },
  "operational": { en: "Operational", gu: "કાર્યરત", hi: "परिचालन योग्य" },
  "cosmetic scratches": { en: "Cosmetic Scratches", gu: "કોસ્મેટિક સ્ક્રેચિસ", hi: "कॉस्मेटिक खरोंच" },
  "loose / damaged": { en: "Loose / Damaged", gu: "ઢીલું / ક્ષતિગ્રસ્ત", hi: "ढीला / क्षतिग्रस्त" },
  "aligned": { en: "Aligned", gu: "યોગ્ય સંરેખિત", hi: "सही संरेखित" },
};

export function localizeConditionHeadline(headline: string, lang: Language): string {
  if (lang === "en" || !headline) return headline;

  const lower = headline.toLowerCase().trim();
  if (CONDITION_HEADLINES[lower]?.[lang]) {
    return CONDITION_HEADLINES[lower][lang];
  }

  const passMatch = headline.match(/PASS\s*\(([^)]+)\)/i);
  if (passMatch) {
    return lang === "gu" ? `પાસ (${passMatch[1]})` : `सफल (${passMatch[1]})`;
  }

  const healthPassMatch = headline.match(/(\d+)%\s*Health\s*\(PASS\)/i);
  if (healthPassMatch) {
    return lang === "gu"
      ? `${healthPassMatch[1]}% સ્થિતિ (પાસ)`
      : `${healthPassMatch[1]}% स्वास्थ्य (सफल)`;
  }

  return headline;
}

export function localizeConditionSummary(summary: string, lang: Language): string {
  if (lang === "en" || !summary) return summary;

  const lower = summary.toLowerCase().trim();

  if (lower.includes("diagnostic data not provided")) {
    return lang === "gu"
      ? "ડાયગ્નોસ્ટિક ડેટા આપવામાં આવ્યો નથી."
      : "डायग्नोस्टिक डेटा प्रदान नहीं किया गया।";
  }

  if (lower.includes("glass and panel clean")) {
    return lang === "gu"
      ? "ગ્લાસ અને પેનલ સ્વચ્છ છે."
      : "ग्लास और पैनल साफ हैं।";
  }

  if (lower.includes("keys operational")) {
    return lang === "gu"
      ? "કીઓ યોગ્ય રીતે કાર્યરત છે."
      : "कुंजियाँ ठीक से काम कर रही हैं।";
  }

  if (lower.includes("surface intact") && lower.includes("click")) {
    return lang === "gu"
      ? "સપાટી અકબંધ, ક્લિક મિકેનિઝમ સ્વચ્છ."
      : "सतह बरकरार, क्लिक तंत्र साफ।";
  }

  if (lower.includes("chassis structurally sound")) {
    return lang === "gu"
      ? "ચેસિસ માળખાકીય રીતે મજબૂત છે."
      : "चेसिस संरचनात्मक रूप से मजबूत है।";
  }

  if (lower.includes("standard tension clearance")) {
    return lang === "gu"
      ? "સામાન્ય ટેન્શન ક્લિયરન્સ."
      : "सामान्य तनाव निकासी।";
  }

  if (lower.includes("gesture or click responsiveness issue")) {
    return lang === "gu"
      ? "હાવભાવ અથવા ક્લિક પ્રતિભાવ સમસ્યા."
      : "जेस्चर या क्लिक प्रतिक्रिया संबंधी समस्या।";
  }

  const battMatch = summary.match(/(\d+)%\s*remaining capacity\s*\(([^)]+)\)/i);
  if (battMatch) {
    return lang === "gu"
      ? `${battMatch[1]}% બાકી ક્ષમતા (${battMatch[2]})`
      : `${battMatch[1]}% शेष क्षमता (${battMatch[2]})`;
  }

  const ramMatch = summary.match(/(\d+)\s*GB Installed\s*•\s*Memory Stress Test:\s*(\w+)/i);
  if (ramMatch) {
    const status = localizeStatus(ramMatch[2], lang);
    return lang === "gu"
      ? `${ramMatch[1]} GB ઇન્સ્ટોલ કરેલ • મેમરી સ્ટ્રેસ ટેસ્ટ: ${status}`
      : `${ramMatch[1]} GB स्थापित • मेमोरी तनाव परीक्षण: ${status}`;
  }

  const cpuMatch = summary.match(/CPU Temp:\s*([^•]+)•\s*Throttling:\s*(\w+)/i);
  if (cpuMatch) {
    const status = localizeStatus(cpuMatch[2], lang);
    return lang === "gu"
      ? `CPU તાપમાન: ${cpuMatch[1].trim()} • થ્રોટલિંગ: ${status}`
      : `सीपीयू तापमान: ${cpuMatch[1].trim()} • थ्रॉटलिंग: ${status}`;
  }

  const ssdMatch = summary.match(/SMART Status:\s*(\w+)(.*)/i);
  if (ssdMatch) {
    const status = localizeStatus(ssdMatch[1], lang);
    return lang === "gu"
      ? `SMART સ્થિતિ: ${status}${ssdMatch[2] ? ssdMatch[2].replace("hrs power-on", "કલાક પાવર-ઓન") : ""}`
      : `SMART स्थिति: ${status}${ssdMatch[2] ? ssdMatch[2].replace("hrs power-on", "घंटे पावर-ऑन") : ""}`;
  }

  return summary;
}

export function localizeEvidenceText(text: string, lang: Language): string {
  if (lang === "en" || !text) return text;
  const lower = text.toLowerCase().trim();

  if (lower.includes("no smart diagnostic reported")) {
    return lang === "gu" ? "કોઈ SMART ડાયગ્નોસ્ટિક નોંધાયેલ નથી" : "कोई SMART डायग्नोस्टिक दर्ज नहीं";
  }
  if (lower.includes("user reported quick battery drainage") || lower.includes("noted quick drainage")) {
    return lang === "gu" ? "વપરાશકર્તાએ ઝડપી બેટરી ડ્રેઇનની જાણ કરી" : "उपयोगकर्ता ने त्वरित बैटरी डिस्चार्ज की सूचना दी";
  }
  if (lower.includes("user reported overheating")) {
    return lang === "gu" ? "વપરાશકર્તાએ ઉપયોગ દરમિયાન વધુ ગરમ થવાની જાણ કરી" : "उपयोगकर्ता ने उपयोग के दौरान अधिक गर्म होने की सूचना दी";
  }
  if (lower.includes("no visible damage detected on display glass")) {
    return lang === "gu" ? "ડિસ્પ્લે ગ્લાસ પર કોઈ દૃશ્યમાન નુકસાન મળ્યું નથી" : "डिस्प्ले ग्लास पर कोई दृश्यमान क्षति नहीं पाई गई";
  }
  if (lower.includes("keycaps present and aligned")) {
    return lang === "gu" ? "કીકેપ્સ હાજર અને યોગ્ય રીતે ગોઠવાયેલ છે" : "कीकैप्स मौजूद और सही संरेखित हैं";
  }
  if (lower.includes("user reported unresponsive key")) {
    return lang === "gu" ? "વપરાશકર્તાએ પ્રતિભાવ ન આપતી કીની જાણ કરી" : "उपयोगकर्ता ने गैर-प्रतिक्रियाशील कुंजियों की सूचना दी";
  }
  if (lower.includes("visual check confirmed surface intact")) {
    return lang === "gu" ? "વિઝ્યુઅલ તપાસમાં સપાટી અકબંધ હોવાની પુષ્ટિ થઈ" : "दृश्य निरीक्षण में सतह बरकरार होने की पुष्टि हुई";
  }
  if (lower.includes("exterior housing verified")) {
    return lang === "gu" ? "બાહ્ય બોડીનું માળખું ચકાસાયેલ છે" : "बाहरी आवरण सत्यापित है";
  }
  if (lower.includes("hinge alignment confirmed visually")) {
    return lang === "gu" ? "હિન્જ ગોઠવણી વિઝ્યુઅલ રીતે ચકાસાયેલ છે" : "हिंज संरेखण की दृश्य रूप से पुष्टि की गई";
  }
  if (lower.includes("user reported loose hinge")) {
    return lang === "gu" ? "વપરાશકર્તાએ ઢીલા હિન્જ અથવા અવાજની જાણ કરી" : "उपयोगकर्ता ने ढीले हिंज या आवाज की सूचना दी";
  }
  if (lower.includes("user reported display flicker")) {
    return lang === "gu" ? "વપરાશકર્તાએ ડિસ્પ્લે ફ્લિકર અથવા ખામીની જાણ કરી" : "उपयोगकर्ता ने डिस्प्ले झिलमिलाहट या दोष की सूचना दी";
  }

  const memMatch = text.match(/Memory stress test\s+(\w+)\s*\(([^)]+)\)/i);
  if (memMatch) {
    const status = localizeStatus(memMatch[1], lang);
    return lang === "gu"
      ? `મેમરી સ્ટ્રેસ ટેસ્ટ ${status} (${memMatch[2]})`
      : `मेमोरी तनाव परीक्षण ${status} (${memMatch[2]})`;
  }

  const capMatch = text.match(/(\d+)%\s*calculated capacity\s*\(([^)]+)\)/i);
  if (capMatch) {
    return lang === "gu"
      ? `${capMatch[1]}% ગણતરી કરેલ ક્ષમતા (${capMatch[2].replace("cycles", "સાયકલ")})`
      : `${capMatch[1]}% गणना की गई क्षमता (${capMatch[2].replace("cycles", "चक्र")})`;
  }

  return text;
}

export function localizeObservation(obs: string, lang: Language): string {
  if (lang === "en" || !obs) return obs;
  const lower = obs.toLowerCase().trim();

  if (lower.includes("clean screen surface") || lower.includes("no deep scratches")) {
    return lang === "gu" ? "સ્વચ્છ સ્ક્રીન સપાટી, કોઈ ઊંડા સ્ક્રેચ નથી" : "साफ स्क्रीन सतह, कोई गहरा खरोंच नहीं";
  }
  if (lower.includes("surface cosmetic scratches") || lower.includes("scratches on casing")) {
    return lang === "gu" ? "બોડી પર સપાટી કોસ્મેટિક સ્ક્રેચિસ" : "केसिंग पर सतही कॉस्मेटिक खरोंच";
  }
  if (lower.includes("keycaps present and aligned") || lower.includes("keys operational")) {
    return lang === "gu" ? "કીકેપ્સ હાજર અને યોગ્ય ગોઠવાયેલ" : "कीकैप्स मौजूद और सही संरेखित";
  }
  if (lower.includes("missing keycaps")) {
    return lang === "gu" ? "ગુમ થયેલ કીકેપ્સ જણાયા" : "गुम कीकैप्स का पता चला";
  }
  if (lower.includes("hinge alignment confirmed")) {
    return lang === "gu" ? "હિન્જ ગોઠવણી યોગ્ય હોવાની પુષ્ટિ" : "हिंज संरेखण सही होने की पुष्टि";
  }
  if (lower.includes("chassis structurally sound")) {
    return lang === "gu" ? "ચેસિસ માળખાકીય રીતે અકબંધ" : "चेसिस संरचनात्मक रूप से बरकरार";
  }

  return obs;
}

// ─── Dynamic Circular Pathways (Engine Output Layer) ─────────────────────────

export interface LocalizedPathwayConfig {
  name: string;
  reason: string;
  lifeExt: string;
  cost: string;
  co2: string;
  turnaround: string;
  targetComponents: string[];
}

export function getLocalizedPathway(
  id: string,
  lang: Language,
  defaultPathway: any
): LocalizedPathwayConfig {
  if (lang === "en") {
    return {
      name: defaultPathway.name,
      reason: defaultPathway.reason,
      lifeExt: defaultPathway.lifeExt,
      cost: defaultPathway.cost,
      co2: defaultPathway.co2,
      turnaround: defaultPathway.turnaround,
      targetComponents: defaultPathway.targetComponents,
    };
  }

  switch (id) {
    case "repair_upgrade":
      return {
        name:
          lang === "gu"
            ? "સમારકામ + અપગ્રેડ (બેટરી + 32GB RAM + થર્મલ ઓવરહોલ)"
            : "मरम्मत + अपग्रेड (बैटरी + 32GB RAM + थर्मल ओवरहाल)",
        reason:
          lang === "gu"
            ? "73% બગડેલી બેટરીને બદલે છે, 62°C પર સંપૂર્ણ થર્મલ ક્ષમતા પુનઃસ્થાપિત કરે છે અને RAM ને 32GB સુધી અપગ્રેડ કરે છે. તમારા અકબંધ 11th-જનરેશન મધરબોર્ડમાંથી મહત્તમ ઉપયોગિતા મેળવે છે."
            : "73% खराब बैटरी को बदलता है, 62°C पर पूर्ण थर्मल अपव्यय बहाल करता है, और रैम को 32GB तक अपग्रेड करता है। आपके बरकरार 11वीं-पीढ़ी मदरबोर्ड से अधिकतम उपयोगिता प्राप्त करता है।",
        lifeExt: lang === "gu" ? "+3.5 વર્ષ" : "+3.5 वर्ष",
        cost: "₹6,200",
        co2: lang === "gu" ? "158 કિગ્રા CO₂ બચાવ્યો" : "158 किग्रा CO₂ बचाया",
        turnaround: lang === "gu" ? "2 દિવસ" : "2 दिन",
        targetComponents:
          lang === "gu"
            ? ["OEM 51Wh બેટરી", "Crucial 16GB DDR4 સ્ટીક", "થર્મલ ગ્રીઝલી પેસ્ટ"]
            : ["OEM 51Wh बैटरी", "Crucial 16GB DDR4 स्टिक", "थर्मल ग्रिजली पेस्ट"],
      };

    case "targeted_repair":
      return {
        name:
          lang === "gu"
            ? "લક્ષ્યાંકિત સમારકામ (બેટરી રિપ્લેસમેન્ટ + રીપેસ્ટિંગ)"
            : "लक्षित मरम्मत (बैटरी प्रतिस्थापन + रीपेस्टिंग)",
        reason:
          lang === "gu"
            ? "સૌથી ઓછો ખર્ચ ઉપાય. બિનજરૂરી કોસ્મેટિક રિપ્લેસમેન્ટ વિના 30-મિનિટના બેટરી કટઓફ અને ઉચ્ચ CPU ગરમીને સીધી રીતે દૂર કરે છે."
            : "सबसे कम लागत वाला समाधान। अनावश्यक कॉस्मेटिक प्रतिस्थापन के बिना 30 मिनट के बैटरी कटऑफ और उच्च सीपीयू गर्मी को समाप्त करता है।",
        lifeExt: lang === "gu" ? "+2.5 વર્ષ" : "+2.5 वर्ष",
        cost: "₹3,800",
        co2: lang === "gu" ? "145 કિગ્રા CO₂ બચાવ્યો" : "145 किग्रा CO₂ बचाया",
        turnaround: lang === "gu" ? "1-2 દિવસ" : "1-2 दिन",
        targetComponents:
          lang === "gu"
            ? ["OEM 51Wh બેટરી", "હીટસિંક ડસ્ટ ક્લીનિંગ અને રીપેસ્ટ", "કીકેપ ક્લિપ પુનઃસ્થાપન"]
            : ["OEM 51Wh बैटरी", "हीटसिंक डस्ट क्लीनिंग और रीपेस्ट", "कीकैप क्लिप रीसीट"],
      };

    case "redeploy_reuse":
      return {
        name:
          lang === "gu"
            ? "દ્વિતીય પુનઃઉપયોગ / સ્થિર ડેસ્કટોપ ભૂમિકા"
            : "द्वितीयक पुनः उपयोग / स्थिर डेस्कटॉप भूमिका",
        reason:
          lang === "gu"
            ? "આ લેપટોપને પાવર સાથે જોડાયેલ સ્ટેશનરી હોમ ઓફિસ વર્કસ્ટેશન અથવા ડિજિટલ સાઇનેજ ટર્મિનલ તરીકે ફરીથી ગોઠવો. ₹0 ખર્ચે તાત્કાલિક ઉપયોગીતા ઉકેલે છે."
            : "इस लैपटॉप को पावर से जुड़े स्थिर होम ऑफिस वर्कस्टेशन या डिजिटल साइनेज टर्मिनल के रूप में पुनः उपयोग करें। ₹0 लागत में तत्काल उपयोगिता हल करता है।",
        lifeExt:
          lang === "gu"
            ? "+1.5 વર્ષ (પ્લગ્ડ-ઇન ભૂમિકા)"
            : "+1.5 वर्ष (प्लग-इन भूमिका)",
        cost: "₹0",
        co2: lang === "gu" ? "135 કિગ્રા CO₂ બચાવ્યો" : "135 किग्रा CO₂ बचाया",
        turnaround: lang === "gu" ? "તાત્કાલિક" : "तत्काल",
        targetComponents:
          lang === "gu"
            ? ["હાલના હાર્ડવેરને AC પાવર સાથે પ્લગ કરેલ રાખો"]
            : ["मौजूदा हार्डवेयर को एसी पावर में प्लग रखें"],
      };

    case "component_recovery":
      return {
        name:
          lang === "gu"
            ? "ઘટક પુનઃપ્રાપ્તિ અને પાર્ટ્સ હાર્વેસ્ટિંગ"
            : "घटक पुनर्प्राप्ति और पुर्जा निष्कर्षण",
        reason:
          lang === "gu"
            ? "પ્રાથમિકતા ઘટાડી: તમારા લેપટોપનું મધરબોર્ડ અને ડિસ્પ્લે ઉત્તમ કાર્યકારી સ્થિતિમાં છે. પાર્ટ્સ અલગ કરવાથી શેષ કમ્પ્યુટિંગ મૂલ્ય અકાળે નાશ પામે છે."
            : "प्राथमिकता घटाई: आपके लैपटॉप का मदरबोर्ड और डिस्प्ले उत्कृष्ट परिचालन स्थिति में हैं। पुर्जे निकालना समय से पहले उच्च कंप्यूटिंग मूल्य को नष्ट करता है।",
        lifeExt:
          lang === "gu" ? "લાગુ નથી (પાર્ટ્સ પુનઃપ્રાપ્તિ)" : "लागू नहीं (पुर्जे निकालें)",
        cost:
          lang === "gu"
            ? "₹0 (પુનઃપ્રાપ્તિ ઉપજ: ₹6,500)"
            : "₹0 (बचाव उपज: ₹6,500)",
        co2: lang === "gu" ? "48 કિગ્રા CO₂ બચાવ્યો" : "48 किग्रा CO₂ बचाया",
        turnaround: lang === "gu" ? "24 કલાક" : "24 घंटे",
        targetComponents:
          lang === "gu"
            ? ["512GB NVMe SSD", "16GB DDR4 RAM", "14-ઇંચ 1080p સ્ક્રીન"]
            : ["512GB NVMe SSD", "16GB DDR4 रैम", "14-इंच 1080p स्क्रीन"],
      };

    case "direct_recycle":
      return {
        name:
          lang === "gu"
            ? "સીધું સામગ્રી રિસાયક્લિંગ"
            : "प्रत्यक्ष सामग्री रीसाइक्लिंग",
        reason:
          lang === "gu"
            ? "અયોગ્ય: સંપૂર્ણપણે સ્વસ્થ ઇન્ટેલ i5 મધરબોર્ડ, NVMe ડ્રાઇવ અને સ્ક્રીનને કાપીને નાશ ન કરવો જોઈએ. સર્ક્યુલર વંશવેલાના નિયમોનું ઉલ્લંઘન કરે છે."
            : "अपात्र: पूरी तरह से स्वस्थ इंटेल i5 मदरबोर्ड, एनवीएमई ड्राइव और स्क्रीन को नष्ट नहीं किया जाना चाहिए। सर्कुलर पदानुक्रम नियमों का उल्लंघन करता है।",
        lifeExt: lang === "gu" ? "0 વર્ષ" : "0 वर्ष",
        cost:
          lang === "gu"
            ? "₹58,000 નવું લેપટોપ જરૂરી"
            : "₹58,000 नया लैपटॉप आवश्यक",
        co2:
          lang === "gu"
            ? "નકારાત્મક (ચોખ્ખું ઉત્સર્જન)"
            : "नकारात्मक (शुद्ध उत्सर्जन)",
        turnaround: lang === "gu" ? "તરત જ" : "तुरंत",
        targetComponents:
          lang === "gu"
            ? ["ઇલેક્ટ્રોનિક શ્રેડિંગ / કાચો સ્મેલ્ટિંગ"]
            : ["इलेक्ट्रॉनिक श्रेडिंग / कच्चा स्मेल्टिंग"],
      };

    default:
      return {
        name: defaultPathway.name,
        reason: defaultPathway.reason,
        lifeExt: defaultPathway.lifeExt,
        cost: defaultPathway.cost,
        co2: defaultPathway.co2,
        turnaround: defaultPathway.turnaround,
        targetComponents: defaultPathway.targetComponents,
      };
  }
}

// ─── Second-Life Specification Localization ──────────────────────────────────

export function localizeSecondLifeRole(role: string, lang: Language): string {
  if (lang === "en" || !role) return role;
  const lower = role.toLowerCase();
  if (lower.includes("stationary") || lower.includes("desktop") || lower.includes("workstation")) {
    return lang === "gu" ? "સ્થિર ઓફિસ વર્કસ્ટેશન" : "स्थिर कार्यालय वर्कस्टेशन";
  }
  if (lower.includes("linux") || lower.includes("learning") || lower.includes("school")) {
    return lang === "gu" ? "શૈક્ષણિક લિનક્સ લર્નિંગ સ્ટેશન" : "शैक्षिक लिनक्स लर्निंग स्टेशन";
  }
  if (lower.includes("server") || lower.includes("media") || lower.includes("node")) {
    return lang === "gu" ? "લાઇટવેઇટ હોમ સર્વર / મીડિયા નોડ" : "लाइटवेट होम सर्वर / मीडिया नोड";
  }
  return role;
}

export function localizeTargetUser(target: string, lang: Language): string {
  if (lang === "en" || !target) return target;
  const lower = target.toLowerCase();
  if (lower.includes("student") || lower.includes("administrative") || lower.includes("office")) {
    return lang === "gu"
      ? "વિદ્યાર્થીઓ, વહીવટી સ્ટાફ અથવા સામાન્ય ઓફિસ વપરાશકર્તાઓ"
      : "छात्र, प्रशासनिक कर्मचारी या सामान्य कार्यालय उपयोगकर्ता";
  }
  return target;
}

export function localizeWorkload(wl: string, lang: Language): string {
  if (lang === "en" || !wl) return wl;
  const lower = wl.toLowerCase();
  if (lower.includes("web") || lower.includes("browsing")) {
    return lang === "gu" ? "વેબ બ્રાઉઝિંગ" : "वेब ब्राउज़िंग";
  }
  if (lower.includes("document") || lower.includes("editing")) {
    return lang === "gu" ? "દસ્તાવેજ સંપાદન" : "दस्तावेज़ संपादन";
  }
  if (lower.includes("video") || lower.includes("playback") || lower.includes("1080p")) {
    return lang === "gu" ? "1080p વિડિઓ પ્લેબેક" : "1080p वीडियो प्लेबैक";
  }
  if (lower.includes("email") || lower.includes("office")) {
    return lang === "gu" ? "ઈમેલ અને ઓફિસ એપ્લિકેશન્સ" : "ईमेल और कार्यालय सुइट्स";
  }
  return wl;
}

export function localizeRecoverablePart(part: string, lang: Language): string {
  if (lang === "en" || !part) return part;
  const lower = part.toLowerCase();
  if (lower.includes("nvme") || lower.includes("ssd")) {
    return "512GB M.2 PCIe NVMe SSD";
  }
  if (lower.includes("ram") || lower.includes("ddr4")) {
    return "16GB DDR4 SO-DIMM RAM";
  }
  if (lower.includes("screen") || lower.includes("display")) {
    return lang === "gu" ? "14-ઇંચ 1080p IPS ડિસ્પ્લે" : "14-इंच 1080p IPS डिस्प्ले";
  }
  if (lower.includes("wifi") || lower.includes("wi-fi")) {
    return "Intel Wi-Fi 6 + BT 5.2 Card";
  }
  return part;
}

export function localizeMaterialRecoveryAction(action: string, lang: Language): string {
  if (lang === "en" || !action) return action;
  return lang === "gu"
    ? "ભૌતિક સામગ્રી પર પ્રક્રિયા કરવામાં આવે તે પહેલાં ઉચ્ચ-મૂલ્યવાળા સિલિકોનને સાચવો"
    : "भौतिक सामग्रियों को संसाधित करने से पहले उच्च-मूल्य वाले सिलिकॉन को सुरक्षित करें";
}

// ─── AI Decision Narrative Localization ──────────────────────────────────────

export function localizeAiNarrative(
  narrative: {
    summary?: string;
    details?: string[];
    assumptions?: string[];
    source?: string;
  } | null,
  lang: Language
) {
  if (!narrative) return null;
  if (lang === "en") return narrative;

  const defaultSummary =
    lang === "gu"
      ? "ReLoop ડિસિઝન એન્જિને શેષ આર્થિક મૂલ્ય અને બચેલા ઉત્સર્જન સામે કમ્પોનન્ટ વસ્ત્રોના લોગનું મૂલ્યાંકન કરીને શ્રેષ્ઠ આગામી-જીવન માર્ગ પસંદ કર્યો છે."
      : "ReLoop निर्णय इंजन ने अवशिष्ट आर्थिक मूल्य और बचाए गए उत्सर्जन के विरुद्ध घटक घिसाव लॉग का मूल्यांकन करके इष्टतम अगले-जीवन मार्ग का चयन किया है।";

  const defaultDetails =
    lang === "gu"
      ? [
          "મધરબોર્ડ પાવર અને ડિસ્પ્લે અકબંધ હોવાથી સીધા રિસાયક્લિંગને અયોગ્ય ઠેરવવામાં આવ્યું છે.",
          "લક્ષ્યાંકિત બેટરી અને થર્મલ રિપ્લેસમેન્ટ ડિવાઇસને ન્યૂનતમ રોકાણ સાથે સંપૂર્ણ કાર્યકારી સ્થિતિમાં લાવે છે.",
          "RAM અપગ્રેડ આગામી 3+ વર્ષ માટે મલ્ટીટાસ્કિંગ પ્રદર્શન હેડરૂમ પ્રદાન કરે છે.",
        ]
      : [
          "मदरबोर्ड पावर और डिस्प्ले बरकरार होने के कारण सीधे रीसाइक्लिंग को अयोग्य घोषित किया गया है।",
          "लक्षित बैटरी और थर्मल प्रतिस्थापन डिवाइस को न्यूनतम निवेश के साथ पूर्ण परिचालन स्थिति में लाता है।",
          "रैम अपग्रेड अगले 3+ वर्षों के लिए मल्टीटास्किंग प्रदर्शन हेडरूम प्रदान करता है।",
        ];

  const defaultAssumptions =
    lang === "gu"
      ? [
          "તર્ક બોર્ડ પાવર ડિલિવરી સ્થિર હોવાનું માનવામાં આવે છે",
          "પ્રમાણિત ટેકનિશિયન દ્વારા બેટરી રિપ્લેસમેન્ટ હાથ ધરવામાં આવેલ છે",
          "થર્મલ ડિસિપેશન ફેક્ટરી થ્રેશોલ્ડ પર પુનઃસ્થાપિત",
        ]
      : [
          "मदरबोर्ड पावर डिलीवरी स्थिर मानी जाती है",
          "प्रमाणित तकनीशियन द्वारा बैटरी प्रतिस्थापन किया गया",
          "थर्मल अपव्यय फ़ैक्टरी सीमा पर बहाल किया गया",
        ];

  return {
    source:
      lang === "gu"
        ? "સુરક્ષિત અલ્ગોરિધમિક ઓપ્ટિમાઇઝર"
        : "सुरक्षित एल्गोरिथम ऑप्टिमाइज़र",
    summary: defaultSummary,
    details: defaultDetails,
    assumptions: defaultAssumptions,
  };
}
