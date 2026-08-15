#!/usr/bin/env node
/** Normalize agent-browser eval stdout → valid JSON file.
 *  Usage: eval ... | node normalize-eval-output.mjs [--object] <output.json> */
import { writeFileSync } from "node:fs";
import { parseEvalJson } from "./lib/parse-eval-json.mjs";

const args = process.argv.slice(2);
const asObject = args[0] === "--object";
const out = asObject ? args[1] : args[0];

if (!out) {
  console.error("Usage: ... | node normalize-eval-output.mjs [--object] <output.json>");
  process.exit(1);
}

let raw = "";
for await (const chunk of process.stdin) raw += chunk;
let data = parseEvalJson(raw);
if (asObject) {
  data = Array.isArray(data) ? data[0] : data;
  writeFileSync(out, JSON.stringify(data, null, 2) + "\n");
  console.error(`Wrote detail object → ${out}`);
} else {
  if (!Array.isArray(data)) data = data ? [data] : [];
  writeFileSync(out, JSON.stringify(data, null, 2) + "\n");
  console.error(`Wrote ${data.length} listings → ${out}`);
}
