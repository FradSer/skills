#!/usr/bin/env node
/**
 * Analyze a detail-page description against ~/.missav preferences.
 *
 * Usage:
 *   node analyze-description.mjs --text "描述..." --prefs ~/.missav/preferences.json
 *   node analyze-description.mjs --item detail.json --prefs ~/.missav/preferences.json
 */

import fs from "node:fs";
import { analyzeDescription } from "./lib/analyze-description.mjs";
import { parseEvalJson } from "./lib/parse-eval-json.mjs";

function parseArgs(argv) {
  const opts = {};
  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    const next = argv[i + 1];
    switch (arg) {
      case "--text":
        opts.text = next;
        i++;
        break;
      case "--item":
        opts.itemFile = next;
        i++;
        break;
      case "--prefs":
        opts.prefsFile = next;
        i++;
        break;
      default:
        break;
    }
  }
  return opts;
}

function main() {
  const opts = parseArgs(process.argv);
  let description = opts.text || "";
  let item = null;

  if (opts.itemFile) {
    const raw = fs.readFileSync(opts.itemFile, "utf8");
    const parsed = parseEvalJson(raw);
    item = Array.isArray(parsed) ? parsed[0] : parsed;
    description = item?.description || description;
  }

  if (!description) {
    console.error("Usage: analyze-description.mjs --text '...' OR --item detail.json [--prefs PATH]");
    process.exit(1);
  }

  const prefs = opts.prefsFile
    ? JSON.parse(fs.readFileSync(opts.prefsFile, "utf8"))
    : {};
  const analysis = analyzeDescription(description, prefs);

  console.log(
    JSON.stringify(
      {
        descriptionLength: description.length,
        analysis,
        item: item ? { href: item.href, code: item.code, title: item.title } : null,
      },
      null,
      2
    )
  );
}

main();
