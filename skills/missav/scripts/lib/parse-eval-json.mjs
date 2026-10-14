import { readFileSync } from "node:fs";

/** Parse JSON returned by agent-browser eval (handles double-encoded strings and stdout noise). */
export function parseEvalJson(raw) {
  const data = (raw || "").trim();
  if (!data) return [];

  const tryParse = (str) => {
    try {
      let parsed = JSON.parse(str);
      if (typeof parsed === "string") {
        parsed = JSON.parse(parsed);
      }
      return parsed;
    } catch {
      return null;
    }
  };

  let parsed = tryParse(data);

  if (parsed == null) {
    const startArr = data.indexOf("[");
    const endArr = data.lastIndexOf("]");
    if (startArr !== -1 && endArr > startArr) {
      parsed = tryParse(data.slice(startArr, endArr + 1));
    }
  }

  if (parsed == null) {
    const startObj = data.indexOf("{");
    const endObj = data.lastIndexOf("}");
    if (startObj !== -1 && endObj > startObj) {
      parsed = tryParse(data.slice(startObj, endObj + 1));
    }
  }

  if (Array.isArray(parsed)) return parsed;
  if (parsed && typeof parsed === "object") return [parsed];
  return [];
}

export function loadJsonFile(path) {
  return parseEvalJson(readFileSync(path, "utf8"));
}
