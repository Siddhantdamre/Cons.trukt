export const OSHA_LINKS = {
  soil: "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926SubpartPAppA",
  protection: "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.652",
  access: "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.651",
  slopes: "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926SubpartPAppB",
};

export const SOIL_TYPES = ["Unclassified", "Stable Rock", "Type A", "Type B", "Type C"];

const SLOPES = {
  "Stable Rock": { ratio: 0, angle: 90 },
  "Type A": { ratio: 0.75, angle: 53 },
  "Type B": { ratio: 1, angle: 45 },
  "Type C": { ratio: 1.5, angle: 34 },
};

const REQUIRED_CHECKS = [
  ["utilities", "Underground installations located and protected"],
  ["spoil", "Spoil, materials, and equipment kept at least 2 ft from the edge"],
  ["egress", "Safe egress provided when the trench is 4 ft or deeper"],
  ["inspection", "Competent-person inspection completed before entry"],
  ["weather", "Conditions rechecked after rain, vibration, or other hazard increase"],
];

function finiteNumber(value, name, minimum, maximum) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < minimum || parsed > maximum) {
    throw new Error(`${name} must be between ${minimum} and ${maximum}.`);
  }
  return parsed;
}

function round(value, digits = 2) {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

function downgradeSoil(reported, conditions) {
  const reasons = [];
  let effective = reported;

  if (reported === "Unclassified") {
    effective = "Type C";
    reasons.push("Unclassified soil is shown with the conservative Type C planning envelope.");
  }

  if (conditions.waterSeepage || conditions.submerged) {
    effective = "Type C";
    reasons.push("Submerged or freely seeping soil is Type C under OSHA Appendix A.");
  } else if (conditions.layeredDipping) {
    effective = "Type C";
    reasons.push("Adversely layered soil is treated as Type C until a competent person classifies it.");
  } else if (
    reported === "Type A"
    && (conditions.fissured || conditions.vibration || conditions.previouslyDisturbed)
  ) {
    effective = "Type B";
    const triggers = [
      conditions.fissured && "fissures",
      conditions.vibration && "vibration",
      conditions.previouslyDisturbed && "previous disturbance",
    ].filter(Boolean);
    reasons.push(`Type A is disallowed because of ${triggers.join(", ")}; Type B is used.`);
  }

  return { effective, reasons };
}

function protectiveSystem(depth, effective, competentPersonConfirmed) {
  if (!competentPersonConfirmed) {
    return {
      status: "stop",
      required: true,
      headline: "Stop: competent-person classification required",
      detail:
        "OSHA requires soil classification from visual and manual analysis by a competent person. "
        + "The calculator can show a Type C planning envelope, but it cannot authorize entry.",
    };
  }

  if (depth < 5 && effective !== "Stable Rock") {
    return {
      status: "conditional",
      required: false,
      headline: "Conditional under-5-ft exception",
      detail:
        "A protective system is not automatically waived. The exception applies only when a "
        + "competent person finds no indication of a potential cave-in.",
    };
  }

  if (effective === "Stable Rock") {
    return {
      status: "review",
      required: false,
      headline: "Stable-rock classification must remain valid",
      detail:
        "Vertical sides are shown only for natural solid mineral matter that can remain intact "
        + "while exposed. Reclassify if conditions change.",
    };
  }

  return {
    status: "required",
    required: true,
    headline: "Cave-in protective system required",
    detail:
      "Use an OSHA-compliant sloping/benching, support, or shield system selected by the "
      + "competent person and installed within its tabulated data.",
  };
}

export function evaluateTrench(raw) {
  const depthFt = finiteNumber(raw.depthFt, "Depth", 0.5, 100);
  const bottomWidthFt = finiteNumber(raw.bottomWidthFt, "Bottom width", 0.5, 100);
  const reportedSoil = SOIL_TYPES.includes(raw.reportedSoil) ? raw.reportedSoil : "Unclassified";
  const conditions = {
    fissured: Boolean(raw.fissured),
    vibration: Boolean(raw.vibration),
    previouslyDisturbed: Boolean(raw.previouslyDisturbed),
    waterSeepage: Boolean(raw.waterSeepage),
    submerged: Boolean(raw.submerged),
    layeredDipping: Boolean(raw.layeredDipping),
    adjacentStructure: Boolean(raw.adjacentStructure),
    surcharge: Boolean(raw.surcharge),
    hazardousAtmosphere: Boolean(raw.hazardousAtmosphere),
  };
  const competentPersonConfirmed = Boolean(raw.competentPersonConfirmed);
  const { effective, reasons: classificationReasons } = downgradeSoil(reportedSoil, conditions);
  const slope = SLOPES[effective] ?? SLOPES["Type C"];
  const rpeRequired = depthFt > 20;
  const egressRequired = depthFt >= 4;
  const topWidthFt = slope.ratio === 0
    ? bottomWidthFt
    : round(bottomWidthFt + (2 * slope.ratio * depthFt));
  const sideRunFt = round(slope.ratio * depthFt);
  const system = protectiveSystem(depthFt, effective, competentPersonConfirmed);

  const warnings = [...classificationReasons];
  if (rpeRequired) {
    warnings.push("Excavations deeper than 20 ft require an RPE-designed protective system.");
  }
  if (conditions.waterSeepage || conditions.submerged) {
    warnings.push("Do not permit work in accumulating water without adequate protective measures.");
  }
  if (conditions.adjacentStructure) {
    warnings.push("Evaluate and support adjoining structures before excavation affects stability.");
  }
  if (conditions.surcharge) {
    warnings.push("A competent person must reduce the actual slope as needed for surcharge loads.");
  }
  if (conditions.hazardousAtmosphere && depthFt > 4) {
    warnings.push("Test the atmosphere before entry and apply required controls and rescue planning.");
  }
  if (!egressRequired) {
    warnings.push("The federal 4-ft egress trigger is not reached; site-specific rules may be stricter.");
  }

  const checks = REQUIRED_CHECKS.map(([id, label]) => ({
    id,
    label,
    checked: Boolean(raw.checks?.[id]),
    required: id !== "egress" || egressRequired,
  }));

  const incompleteChecks = checks.filter((item) => item.required && !item.checked);
  const readyForReview = competentPersonConfirmed
    && incompleteChecks.length === 0
    && !rpeRequired
    && !(conditions.waterSeepage || conditions.submerged);

  return {
    project: String(raw.project ?? "").trim(),
    location: String(raw.location ?? "").trim(),
    competentPerson: String(raw.competentPerson ?? "").trim(),
    depthFt,
    bottomWidthFt,
    reportedSoil,
    effectiveSoil: effective,
    competentPersonConfirmed,
    slopeRatio: slope.ratio,
    slopeAngle: slope.angle,
    sideRunFt,
    topWidthFt,
    rpeRequired,
    egressRequired,
    system,
    conditions,
    warnings,
    checks,
    incompleteChecks,
    disposition: readyForReview ? "ready-for-review" : "hold",
    generatedAt: new Date().toISOString(),
    citations: [
      {
        clause: "29 CFR 1926 Subpart P, Appendix A",
        note: "Soil classification and required visual/manual analysis",
        url: OSHA_LINKS.soil,
      },
      {
        clause: "29 CFR 1926.652",
        note: "Cave-in protective-system requirements",
        url: OSHA_LINKS.protection,
      },
      {
        clause: "29 CFR 1926 Subpart P, Appendix B",
        note: "Maximum allowable slope table for excavations up to 20 ft",
        url: OSHA_LINKS.slopes,
      },
      {
        clause: "29 CFR 1926.651",
        note: "Access, water, inspections, utilities, and adjacent hazards",
        url: OSHA_LINKS.access,
      },
    ],
  };
}

export function reportSummary(result) {
  const slopeText = result.rpeRequired
    ? "RPE design required; table slope is not a design"
    : `${result.slopeRatio}:1 H:V (${result.slopeAngle} degrees), ${result.topWidthFt} ft top width`;
  return [
    `Project: ${result.project || "Not entered"}`,
    `Location: ${result.location || "Not entered"}`,
    `Depth / bottom width: ${result.depthFt} ft / ${result.bottomWidthFt} ft`,
    `Soil: ${result.reportedSoil} reported; ${result.effectiveSoil} planning classification`,
    `Protective-system decision: ${result.system.headline}`,
    `Sloping envelope: ${slopeText}`,
    `Egress: ${result.egressRequired ? "Required within 25 ft lateral travel" : "Federal 4-ft trigger not reached"}`,
    `Disposition: ${result.disposition === "ready-for-review" ? "Pre-plan complete for competent-person review" : "Hold before entry"}`,
  ].join("\n");
}
