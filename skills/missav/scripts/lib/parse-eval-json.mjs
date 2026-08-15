import { readFileSync } from "node:fs";

/** Parse JSON returned by agent-browser eval (handles double-encoded strings). */
export function parseEvalJson(raw) {
  let data = raw.trim();
  if (!data) return [];
  let parsed = JSON.parse(data);
  if (typeof parsed === "string") {
    parsed = JSON.parse(parsed);
  }
  if (Array.isArray(parsed)) return parsed;
  if (parsed && typeof parsed === "object") return [parsed];
  return [];
}

export function loadJsonFile(path) {
  return parseEvalJson(readFileSync(path, "utf8"));
}
