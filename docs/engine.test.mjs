import assert from "node:assert/strict";
import test from "node:test";

import { evaluateTrench } from "./engine.mjs";

const completeChecks = {
  utilities: true,
  spoil: true,
  egress: true,
  inspection: true,
  weather: true,
};

test("vibration downgrades reported Type A to Type B", () => {
  const result = evaluateTrench({
    depthFt: 8,
    bottomWidthFt: 3,
    reportedSoil: "Type A",
    vibration: true,
    competentPersonConfirmed: true,
    checks: completeChecks,
  });
  assert.equal(result.effectiveSoil, "Type B");
  assert.equal(result.slopeRatio, 1);
  assert.equal(result.topWidthFt, 19);
});

test("freely seeping water forces Type C", () => {
  const result = evaluateTrench({
    depthFt: 8,
    bottomWidthFt: 3,
    reportedSoil: "Type A",
    waterSeepage: true,
    competentPersonConfirmed: true,
    checks: completeChecks,
  });
  assert.equal(result.effectiveSoil, "Type C");
  assert.equal(result.slopeRatio, 1.5);
  assert.equal(result.disposition, "hold");
});

test("under five feet is a conditional exception, not an automatic clearance", () => {
  const result = evaluateTrench({
    depthFt: 4,
    bottomWidthFt: 3,
    reportedSoil: "Type B",
    competentPersonConfirmed: true,
    checks: completeChecks,
  });
  assert.equal(result.system.status, "conditional");
  assert.match(result.system.detail, /not automatically waived/i);
});

test("unclassified soil cannot produce a ready disposition", () => {
  const result = evaluateTrench({
    depthFt: 8,
    bottomWidthFt: 3,
    reportedSoil: "Unclassified",
    competentPersonConfirmed: false,
    checks: completeChecks,
  });
  assert.equal(result.effectiveSoil, "Type C");
  assert.equal(result.system.status, "stop");
  assert.equal(result.disposition, "hold");
});

test("excavations deeper than twenty feet require an RPE", () => {
  const result = evaluateTrench({
    depthFt: 22,
    bottomWidthFt: 4,
    reportedSoil: "Type C",
    competentPersonConfirmed: true,
    checks: completeChecks,
  });
  assert.equal(result.rpeRequired, true);
  assert.equal(result.disposition, "hold");
});
