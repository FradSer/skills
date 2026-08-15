import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { genresFromDescription } from "./analyze-description.mjs";

const PREFS_VERSION = 2;
const DEFAULT_DIR = path.join(os.homedir(), ".missav");
const PREFS_FILE = "preferences.json";
const FEEDBACK_FILE = "feedback.jsonl";

function prefsDir(customDir) {
  return customDir || process.env.MISSAV_HOME || DEFAULT_DIR;
}

function prefsPath(customDir) {
  return path.join(prefsDir(customDir), PREFS_FILE);
}

function feedbackPath(customDir) {
  return path.join(prefsDir(customDir), FEEDBACK_FILE);
}

function defaultPreferences() {
  return {
    version: PREFS_VERSION,
    updatedAt: new Date().toISOString(),
    likes: {
      genres: [],
      performers: [],
      labels: [],
      keywords: [],
      codes: [],
    },
    dislikes: {
      genres: [],
      performers: [],
      labels: [],
      keywords: [],
      codes: [],
      hrefs: [],
    },
    duration: {
      minMinutes: null,
      maxMinutes: null,
    },
    search: {
      defaultKeyword: null,
      defaultFilter: null,
      defaultCategory: "dm247",
    },
    weights: {
      code: 100,
      label: 30,
      performer: 40,
      genre: 25,
      keyword: 20,
      durationOk: 10,
      durationOut: -50,
      dislikePenalty: -80,
    },
    limit: 10,
    stats: {
      likedCount: 0,
      dislikedCount: 0,
      sessions: 0,
    },
  };
}

function uniq(list) {
  const seen = new Set();
  return list.filter((v) => {
    const key = String(v).toLowerCase();
    if (!v || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function mergeList(...lists) {
  return uniq(lists.flat().filter(Boolean));
}

function migrateLikes(rawLikes = {}) {
  return {
    genres: mergeList(rawLikes.genres || []),
    performers: mergeList(
      rawLikes.performers || [],
      rawLikes.actresses || [],
      rawLikes.actors || []
    ),
    labels: mergeList(
      (rawLikes.labels || []).map((s) => String(s).toUpperCase()),
      (rawLikes.series || []).map((s) => String(s).toUpperCase())
    ),
    keywords: mergeList(rawLikes.keywords || []),
    codes: mergeList((rawLikes.codes || []).map((s) => String(s).toUpperCase())),
  };
}

function migrateDislikes(rawDislikes = {}) {
  return {
    genres: mergeList(rawDislikes.genres || []),
    performers: mergeList(
      rawDislikes.performers || [],
      rawDislikes.actresses || [],
      rawDislikes.actors || []
    ),
    labels: mergeList(
      (rawDislikes.labels || []).map((s) => String(s).toUpperCase()),
      (rawDislikes.series || []).map((s) => String(s).toUpperCase())
    ),
    keywords: mergeList(rawDislikes.keywords || []),
    codes: mergeList((rawDislikes.codes || []).map((s) => String(s).toUpperCase())),
    hrefs: mergeList(rawDislikes.hrefs || []),
  };
}

function loadPreferences(customDir) {
  const file = prefsPath(customDir);
  if (!fs.existsSync(file)) {
    return null;
  }
  const raw = JSON.parse(fs.readFileSync(file, "utf8"));
  return normalizePreferences(raw);
}

function normalizePreferences(raw) {
  const base = defaultPreferences();
  const weights = { ...base.weights, ...(raw.weights || {}) };
  if (weights.series != null && weights.label == null) weights.label = weights.series;
  if (weights.actress != null && weights.performer == null) weights.performer = weights.actress;

  return {
    ...base,
    ...raw,
    version: PREFS_VERSION,
    likes: migrateLikes(raw.likes),
    dislikes: migrateDislikes(raw.dislikes),
    duration: { ...base.duration, ...(raw.duration || {}) },
    search: { ...base.search, ...(raw.search || {}) },
    weights,
    stats: { ...base.stats, ...(raw.stats || {}) },
  };
}

function savePreferences(prefs, customDir) {
  ensureDir(prefsDir(customDir));
  const next = normalizePreferences({
    ...prefs,
    updatedAt: new Date().toISOString(),
  });
  fs.writeFileSync(prefsPath(customDir), JSON.stringify(next, null, 2) + "\n");
  return next;
}

function initPreferences(customDir) {
  const existing = loadPreferences(customDir);
  if (existing) return existing;
  return savePreferences(defaultPreferences(), customDir);
}

function appendFeedbackLog(entry, customDir) {
  ensureDir(prefsDir(customDir));
  const line = JSON.stringify({ ...entry, at: new Date().toISOString() }) + "\n";
  fs.appendFileSync(feedbackPath(customDir), line);
}

function labelFromCode(code) {
  if (!code) return null;
  const m = String(code).match(/^([A-Z]{2,10})-/i);
  return m ? m[1].toUpperCase() : null;
}

function keywordsFromSlug(slug) {
  if (!slug) return [];
  return slug
    .split("-")
    .filter((part) => /subtitle|chinese|english|uncensored|leak/i.test(part))
    .map((part) => part.toLowerCase());
}

function performersFromTitle(title) {
  if (!title) return [];
  const out = [];
  const parts = title.split(" - ").map((s) => s.trim()).filter(Boolean);
  if (parts.length >= 2) {
    const tail = parts[parts.length - 1];
    if (tail && tail.length <= 40) {
      tail.split(/[,、/]/).map((s) => s.trim()).filter(Boolean).forEach((n) => out.push(n));
    }
    const prev = parts[parts.length - 2];
    const latin = prev.match(/([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)$/);
    if (latin) out.push(latin[1]);
    prev.split(/[,、/]/).map((s) => s.trim()).filter(Boolean).forEach((n) => {
      if (/^[A-Z][a-z]+(\s+[A-Z][a-z]+)*$/.test(n)) out.push(n);
    });
  }
  return uniq(out);
}

function extractSignalsFromItem(item) {
  const code = item.code ? item.code.toUpperCase() : "";
  const label = labelFromCode(code);
  const descGenres = item.description ? genresFromDescription(item.description) : [];
  return {
    code: code || null,
    labels: label ? [label] : [],
    performers: performersFromTitle(item.title || ""),
    genres: mergeList(item.genres || [], item.tags || [], descGenres),
    keywords: keywordsFromSlug(item.slug || ""),
    href: item.href || null,
    durationMinutes: item.durationMinutes ?? null,
  };
}

function addLikes(prefs, signals) {
  if (signals.code) prefs.likes.codes = mergeList(prefs.likes.codes, [signals.code.toUpperCase()]);
  if (signals.labels?.length) prefs.likes.labels = mergeList(prefs.likes.labels, signals.labels.map((s) => s.toUpperCase()));
  if (signals.performers?.length) prefs.likes.performers = mergeList(prefs.likes.performers, signals.performers);
  if (signals.genres?.length) prefs.likes.genres = mergeList(prefs.likes.genres, signals.genres);
  if (signals.keywords?.length) prefs.likes.keywords = mergeList(prefs.likes.keywords, signals.keywords);
  return prefs;
}

function addDislikes(prefs, signals) {
  if (signals.code) prefs.dislikes.codes = mergeList(prefs.dislikes.codes, [signals.code.toUpperCase()]);
  if (signals.labels?.length) prefs.dislikes.labels = mergeList(prefs.dislikes.labels, signals.labels.map((s) => s.toUpperCase()));
  if (signals.performers?.length) prefs.dislikes.performers = mergeList(prefs.dislikes.performers, signals.performers);
  if (signals.genres?.length) prefs.dislikes.genres = mergeList(prefs.dislikes.genres, signals.genres);
  if (signals.keywords?.length) prefs.dislikes.keywords = mergeList(prefs.dislikes.keywords, signals.keywords);
  if (signals.href) prefs.dislikes.hrefs = mergeList(prefs.dislikes.hrefs, [signals.href]);
  return prefs;
}

function removeFromDislikes(prefs, signals) {
  const dropCode = signals.code ? signals.code.toLowerCase() : null;
  const dropLabels = new Set((signals.labels || []).map((s) => s.toLowerCase()));
  const dropPerformers = new Set((signals.performers || []).map((s) => s.toLowerCase()));
  const dropGenres = new Set((signals.genres || []).map((s) => s.toLowerCase()));
  const dropKeywords = new Set((signals.keywords || []).map((s) => s.toLowerCase()));
  const dropHref = signals.href || null;

  if (dropCode) {
    prefs.dislikes.codes = prefs.dislikes.codes.filter((v) => v.toLowerCase() !== dropCode);
  }
  prefs.dislikes.labels = prefs.dislikes.labels.filter((v) => !dropLabels.has(v.toLowerCase()));
  prefs.dislikes.performers = prefs.dislikes.performers.filter((v) => !dropPerformers.has(v.toLowerCase()));
  prefs.dislikes.genres = prefs.dislikes.genres.filter((v) => !dropGenres.has(v.toLowerCase()));
  prefs.dislikes.keywords = prefs.dislikes.keywords.filter((v) => !dropKeywords.has(v.toLowerCase()));
  if (dropHref) {
    prefs.dislikes.hrefs = prefs.dislikes.hrefs.filter((v) => v !== dropHref);
  }
  return prefs;
}

function applyFeedback(prefs, feedback) {
  const next = normalizePreferences(prefs);
  const item = feedback.item || {};
  const signals = extractSignalsFromItem(item);
  const type = feedback.type;

  appendFeedbackLog({ type, signals, note: feedback.note || null, item }, feedback.dir);

  switch (type) {
    case "like":
    case "more_like_this":
      addLikes(next, signals);
      removeFromDislikes(next, signals);
      next.stats.likedCount += 1;
      break;
    case "dislike":
    case "never_again":
      addDislikes(next, signals);
      next.stats.dislikedCount += 1;
      break;
    case "too_short":
      if (signals.durationMinutes != null) {
        next.duration.minMinutes = Math.max(next.duration.minMinutes || 0, Math.ceil(signals.durationMinutes + 5));
      } else if (feedback.minMinutes != null) {
        next.duration.minMinutes = feedback.minMinutes;
      }
      addDislikes(next, signals);
      next.stats.dislikedCount += 1;
      break;
    case "too_long":
      if (signals.durationMinutes != null) {
        const cap = Math.floor(signals.durationMinutes - 5);
        next.duration.maxMinutes = next.duration.maxMinutes == null ? cap : Math.min(next.duration.maxMinutes, cap);
      } else if (feedback.maxMinutes != null) {
        next.duration.maxMinutes = feedback.maxMinutes;
      }
      addDislikes(next, signals);
      next.stats.dislikedCount += 1;
      break;
    default:
      throw new Error(`Unknown feedback type: ${type}`);
  }

  if (feedback.extraLikes) addLikes(next, feedback.extraLikes);
  if (feedback.extraDislikes) addDislikes(next, feedback.extraDislikes);

  return savePreferences(next, feedback.dir);
}

function splitCsv(value) {
  return String(value)
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

function mergeField(next, group, field, value, transform) {
  if (value == null) return;
  const parts = splitCsv(value).map(transform || ((s) => s));
  next[group][field] = mergeList(next[group][field], parts);
}

function mergeExplicitUpdates(prefs, updates) {
  const next = normalizePreferences(prefs);

  mergeField(next, "likes", "genres", updates.genres);
  mergeField(next, "likes", "performers", updates.performers);
  mergeField(next, "likes", "performers", updates.actresses);
  mergeField(next, "likes", "performers", updates.actors);
  mergeField(next, "likes", "labels", updates.labels, (s) => s.toUpperCase());
  mergeField(next, "likes", "labels", updates.series, (s) => s.toUpperCase());
  mergeField(next, "likes", "keywords", updates.keywords);
  mergeField(next, "likes", "codes", updates.codes, (s) => s.toUpperCase());

  mergeField(next, "dislikes", "genres", updates["dislike-genres"]);
  mergeField(next, "dislikes", "performers", updates["dislike-performers"]);
  mergeField(next, "dislikes", "performers", updates["dislike-actresses"]);
  mergeField(next, "dislikes", "performers", updates["dislike-actors"]);
  mergeField(next, "dislikes", "labels", updates["dislike-labels"], (s) => s.toUpperCase());
  mergeField(next, "dislikes", "labels", updates["dislike-series"], (s) => s.toUpperCase());
  mergeField(next, "dislikes", "keywords", updates["dislike-keywords"]);
  mergeField(next, "dislikes", "codes", updates["dislike-codes"], (s) => s.toUpperCase());

  if (updates["min-duration"] != null) next.duration.minMinutes = Number(updates["min-duration"]);
  if (updates["max-duration"] != null) next.duration.maxMinutes = Number(updates["max-duration"]);
  if (updates.minDuration != null) next.duration.minMinutes = Number(updates.minDuration);
  if (updates.maxDuration != null) next.duration.maxMinutes = Number(updates.maxDuration);
  if (updates["default-keyword"] != null) next.search.defaultKeyword = updates["default-keyword"];
  if (updates["default-filter"] != null) next.search.defaultFilter = updates["default-filter"];
  if (updates.limit != null) next.limit = Number(updates.limit);

  return savePreferences(next, updates.dir);
}

function mergeOverrideList(stored, override) {
  return mergeList(stored, override || []);
}

function prefsToFilterOpts(prefs, overrides = {}) {
  const p = normalizePreferences(prefs);
  const performerOverride = mergeList(
    overrides.performers || [],
    overrides.actresses || [],
    overrides.actors || []
  );
  const labelOverride = mergeList(
    (overrides.labels || []).map((s) => s.toUpperCase()),
    (overrides.series || []).map((s) => s.toUpperCase())
  );

  return {
    genres: mergeOverrideList(p.likes.genres, overrides.genres),
    performers: mergeOverrideList(p.likes.performers, performerOverride),
    labels: mergeOverrideList(p.likes.labels, labelOverride).map((s) => s.toUpperCase()),
    keywords: mergeOverrideList(p.likes.keywords, overrides.keywords),
    codes: mergeOverrideList(p.likes.codes, overrides.codes).map((s) => s.toUpperCase()),
    minDuration: overrides.minDuration ?? p.duration.minMinutes,
    maxDuration: overrides.maxDuration ?? p.duration.maxMinutes,
    limit: overrides.limit ?? p.limit,
    dislikes: p.dislikes,
    weights: p.weights,
  };
}

export {
  DEFAULT_DIR,
  prefsDir,
  prefsPath,
  feedbackPath,
  defaultPreferences,
  initPreferences,
  loadPreferences,
  savePreferences,
  appendFeedbackLog,
  extractSignalsFromItem,
  applyFeedback,
  mergeExplicitUpdates,
  prefsToFilterOpts,
  labelFromCode,
  performersFromTitle,
  labelFromCode as seriesFromCode,
  performersFromTitle as actressesFromTitle,
};
