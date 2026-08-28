#!/usr/bin/env node
/**
 * Score and rank missav listings against user preferences.
 *
 * Usage:
 *   node filter-recommendations.mjs listings.json --prefs ~/.missav/preferences.json
 *   node filter-recommendations.mjs listings.json \
 *     --genres "NTR,制服" \
 *     --performers "Fuua Kaede,枫ふうあ" \
 *     --labels "SSIS,MIDV" \
 *     --min-duration 90 --limit 10
 *
 * Aliases: --actresses/--actors → performers; --series → labels
 */

import fs from "node:fs";
import { prefsToFilterOpts } from "./lib/preferences.mjs";
import { analyzeDescription } from "./lib/analyze-description.mjs";

function parseArgs(argv) {
  const opts = {
    prefsFile: null,
    cliOverrides: {},
  };
  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    const next = argv[i + 1];
    const splitList = (s) =>
      s
        .split(",")
        .map((x) => x.trim())
        .filter(Boolean);
    switch (arg) {
      case "--prefs":
        opts.prefsFile = next;
        i++;
        break;
      case "--genres":
        opts.cliOverrides.genres = splitList(next);
        i++;
        break;
      case "--performers":
      case "--actresses":
      case "--actors":
        opts.cliOverrides.performers = splitList(next);
        i++;
        break;
      case "--labels":
      case "--series":
        opts.cliOverrides.labels = splitList(next).map((s) => s.toUpperCase());
        i++;
        break;
      case "--keywords":
        opts.cliOverrides.keywords = splitList(next);
        i++;
        break;
      case "--codes":
        opts.cliOverrides.codes = splitList(next).map((s) => s.toUpperCase());
        i++;
        break;
      case "--min-duration":
        opts.cliOverrides.minDuration = Number(next);
        i++;
        break;
      case "--max-duration":
        opts.cliOverrides.maxDuration = Number(next);
        i++;
        break;
      case "--limit":
        opts.cliOverrides.limit = Number(next);
        i++;
        break;
      default:
        if (!arg.startsWith("-") && !opts.inputFile) {
          opts.inputFile = arg;
        }
    }
  }
  return opts;
}

function labelPrefix(code, label) {
  if (!code || !label) return false;
  const upper = code.toUpperCase();
  const prefix = label.toUpperCase();
  return upper.startsWith(`${prefix}-`) || upper === prefix;
}

function matchesSearchTerm(text, term) {
  const value = String(term || "").trim().toLowerCase();
  if (!value) return false;
  if (/^[a-z0-9][a-z0-9 -]*$/.test(value)) {
    const escaped = value.replace(/[.*+?^${}()|[\\]\\]/g, "\\\\$&");
    return new RegExp(`(^|[^a-z0-9])${escaped}(?=$|[^a-z0-9])`, "i").test(text);
  }
  return text.includes(value);
}

function scoreItem(item, opts) {
  let score = 0;
  const reasons = [];
  const haystack = `${item.title} ${item.slug} ${item.code} ${item.description || ""} ${(item.tags || []).join(" ")}`.toLowerCase();
  const searchableText = [item.title, item.description, ...(item.tags || [])]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  const w = opts.weights;

  if (opts.dislikes?.hrefs?.includes(item.href)) {
    return { ...item, score: -9999, reasons: ["blocked:href"] };
  }

  for (const code of opts.dislikes?.codes || []) {
    if (item.code && item.code.toUpperCase() === code.toUpperCase()) {
      score += w.dislikePenalty;
      reasons.push(`dislike:code:${code}`);
    }
  }

  for (const label of opts.dislikes?.labels || []) {
    if (labelPrefix(item.code, label)) {
      score += w.dislikePenalty;
      reasons.push(`dislike:label:${label}`);
    }
  }

  for (const performer of opts.dislikes?.performers || []) {
    if (matchesSearchTerm(searchableText, performer)) {
      score += w.dislikePenalty;
      reasons.push(`dislike:performer:${performer}`);
    }
  }

  for (const genre of opts.dislikes?.genres || []) {
    if (matchesSearchTerm(searchableText, genre)) {
      score += w.dislikePenalty;
      reasons.push(`dislike:genre:${genre}`);
    }
  }

  for (const kw of opts.dislikes?.keywords || []) {
    if (matchesSearchTerm(searchableText, kw)) {
      score += w.dislikePenalty;
      reasons.push(`dislike:keyword:${kw}`);
    }
  }

  for (const code of opts.codes) {
    if (item.code && item.code.toUpperCase() === code.toUpperCase()) {
      score += w.code;
      reasons.push(`code:${code}`);
    }
  }

  for (const label of opts.labels) {
    if (labelPrefix(item.code, label)) {
      score += w.label;
      reasons.push(`label:${label}`);
    }
  }

  for (const performer of opts.performers) {
    if (matchesSearchTerm(searchableText, performer)) {
      score += w.performer;
      reasons.push(`performer:${performer}`);
    }
  }

  for (const genre of opts.genres) {
    if (matchesSearchTerm(searchableText, genre)) {
      score += w.genre;
      reasons.push(`genre:${genre}`);
    }
  }

  for (const kw of opts.keywords) {
    if (matchesSearchTerm(searchableText, kw)) {
      score += w.keyword;
      reasons.push(`keyword:${kw}`);
    }
  }

  if (item.durationMinutes != null) {
    const inRange =
      (opts.minDuration == null || item.durationMinutes >= opts.minDuration) &&
      (opts.maxDuration == null || item.durationMinutes <= opts.maxDuration);
    if (inRange) {
      score += w.durationOk;
      reasons.push("duration:ok");
    } else if (opts.minDuration != null || opts.maxDuration != null) {
      score += w.durationOut;
      reasons.push("duration:out-of-range");
    }
  }

  if (item.description && opts.prefsRaw) {
    const analysis = analyzeDescription(item.description, opts.prefsRaw);
    score += analysis.fitScore;
    for (const r of analysis.reasons) reasons.push(`desc:${r}`);
    if (analysis.matchedDislikes.length) score += w.dislikePenalty * analysis.matchedDislikes.length;
  }

  return { ...item, score, reasons };
}

function resolveOpts(parsed) {
  const baseWeights = {
    code: 100,
    label: 30,
    performer: 40,
    genre: 25,
    keyword: 20,
    durationOk: 10,
    durationOut: -50,
    dislikePenalty: -80,
  };

  if (parsed.prefsFile) {
    const raw = JSON.parse(fs.readFileSync(parsed.prefsFile, "utf8"));
    const opts = prefsToFilterOpts(raw, parsed.cliOverrides);
    opts.prefsRaw = raw;
    return opts;
  }

  const opts = prefsToFilterOpts(
    { likes: {}, dislikes: {}, duration: {}, limit: 10, weights: baseWeights },
    parsed.cliOverrides
  );
  opts.prefsRaw = null;
  return opts;
}

function hasActiveFilters(opts) {
  return (
    opts.genres.length ||
    opts.performers.length ||
    opts.labels.length ||
    opts.keywords.length ||
    opts.codes.length ||
    opts.minDuration != null ||
    opts.maxDuration != null ||
    (opts.dislikes &&
      (opts.dislikes.genres.length ||
        opts.dislikes.performers.length ||
        opts.dislikes.labels.length ||
        opts.dislikes.keywords.length ||
        opts.dislikes.codes.length ||
        opts.dislikes.hrefs.length))
  );
}

function main() {
  const parsed = parseArgs(process.argv);
  if (!parsed.inputFile) {
    console.error(`Usage: node filter-recommendations.mjs <listings.json> [--prefs ~/.missav/preferences.json] [options]`);
    process.exit(1);
  }

  const opts = resolveOpts(parsed);
  const listings = JSON.parse(fs.readFileSync(parsed.inputFile, "utf8"));

  const byHref = new Map();
  for (const item of listings) {
    const key = item.href || `${item.code || ""}:${item.title || ""}`;
    if (!key || byHref.has(key)) continue;
    byHref.set(key, item);
  }
  const deduped = [...byHref.values()];
  const hasFilters = hasActiveFilters(opts);

  const scored = deduped
    .map((item) => scoreItem(item, opts))
    .filter((item) => item.score > -9999)
    .filter((item) => !hasFilters || item.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, opts.limit);

  console.log(
    JSON.stringify(
      {
        total: deduped.length,
        rawTotal: listings.length,
        shown: scored.length,
        prefs: parsed.prefsFile || null,
        items: scored,
      },
      null,
      2
    )
  );
}

main();
