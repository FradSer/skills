#!/usr/bin/env node
/**
 * Manage ~/.missav/ preference store.
 *
 * Commands:
 *   init                          Create ~/.missav/ with default preferences.json
 *   show [--dir PATH]             Print current preferences
 *   set [--genres ...] [...]      Merge explicit preference updates
 *   feedback <type> [--item FILE] Apply user feedback and persist
 *
 * Feedback types: like | dislike | more_like_this | never_again | too_short | too_long
 */

import fs from "node:fs";
import {
  initPreferences,
  loadPreferences,
  applyFeedback,
  mergeExplicitUpdates,
  extractSignalsFromItem,
  prefsPath,
  feedbackPath,
} from "./lib/preferences.mjs";

function parseArgs(argv) {
  const positional = [];
  const opts = {};
  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    const next = argv[i + 1];
    if (arg === "--dir" && next) {
      opts.dir = next;
      i++;
      continue;
    }
    if (arg === "--item" && next) {
      opts.itemFile = next;
      i++;
      continue;
    }
    if (arg === "--note" && next) {
      opts.note = next;
      i++;
      continue;
    }
    if (arg.startsWith("--")) {
      const key = arg.slice(2);
      if (next && !next.startsWith("--")) {
        opts[key] = next;
        i++;
      } else {
        opts[key] = true;
      }
      continue;
    }
    positional.push(arg);
  }
  return { positional, opts };
}

function loadItem(opts) {
  if (!opts.itemFile) return {};
  const raw = fs.readFileSync(opts.itemFile, "utf8");
  return JSON.parse(raw);
}

function cmdInit(opts) {
  const prefs = initPreferences(opts.dir);
  console.log(JSON.stringify({ ok: true, path: prefsPath(opts.dir), preferences: prefs }, null, 2));
}

function cmdShow(opts) {
  const prefs = loadPreferences(opts.dir);
  if (!prefs) {
    console.error(`No preferences at ${prefsPath(opts.dir)}. Run: node preferences.mjs init`);
    process.exit(1);
  }
  console.log(JSON.stringify({ path: prefsPath(opts.dir), feedbackLog: feedbackPath(opts.dir), preferences: prefs }, null, 2));
}

function cmdSet(opts) {
  let prefs = loadPreferences(opts.dir);
  if (!prefs) prefs = initPreferences(opts.dir);
  const updated = mergeExplicitUpdates(prefs, { ...opts, dir: opts.dir });
  console.log(JSON.stringify({ ok: true, path: prefsPath(opts.dir), preferences: updated }, null, 2));
}

function cmdFeedback(type, opts) {
  let prefs = loadPreferences(opts.dir);
  if (!prefs) prefs = initPreferences(opts.dir);
  const item = loadItem(opts);
  const updated = applyFeedback(prefs, {
    type,
    item,
    note: opts.note || null,
    dir: opts.dir,
    minMinutes: opts.minMinutes != null ? Number(opts.minMinutes) : null,
    maxMinutes: opts.maxMinutes != null ? Number(opts.maxMinutes) : null,
    extraLikes: opts.likes ? parseList(opts.likes) : null,
    extraDislikes: opts.dislikes ? parseList(opts.dislikes) : null,
  });
  const signals = extractSignalsFromItem(item);
  console.log(
    JSON.stringify(
      { ok: true, type, signals, path: prefsPath(opts.dir), preferences: updated },
      null,
      2
    )
  );
}

function parseList(value) {
  if (Array.isArray(value)) return value;
  return String(value)
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

function usage() {
  console.error(`Usage:
  node preferences.mjs init [--dir ~/.missav]
  node preferences.mjs show [--dir ~/.missav]
  node preferences.mjs set [--dir DIR] [--genres G] [--performers P] [--labels L] [--keywords K] [--codes C]
                         [--dislike-genres G] [--dislike-performers P] [--dislike-labels L]
                         [--min-duration N] [--max-duration N]
                         [--default-keyword ssis] [--default-filter chinese-subtitle]

  Aliases: --actresses/--actors → performers; --series → labels
  node preferences.mjs feedback <type> [--item item.json] [--note TEXT] [--dir DIR]

Feedback types:
  like             Boost label/performer/genre/code from item (e.g. SSIS-825 → label SSIS)
  more_like_this   Same as like (alias)
  dislike          Penalize extracted signals; block href
  never_again      Same as dislike (alias)
  too_short        Raise minDuration; dislike item
  too_long         Lower maxDuration; dislike item

Store layout:
  ~/.missav/preferences.json   Persistent likes/dislikes/duration/search defaults
  ~/.missav/feedback.jsonl     Append-only feedback audit log`);
}

function main() {
  const { positional, opts } = parseArgs(process.argv);
  const cmd = positional[0];
  if (!cmd) {
    usage();
    process.exit(1);
  }
  switch (cmd) {
    case "init":
      cmdInit(opts);
      break;
    case "show":
      cmdShow(opts);
      break;
    case "set":
      cmdSet(opts);
      break;
    case "feedback":
      if (!positional[1]) {
        usage();
        process.exit(1);
      }
      cmdFeedback(positional[1], opts);
      break;
    default:
      usage();
      process.exit(1);
  }
}

main();
