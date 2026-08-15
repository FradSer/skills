/**
 * Analyze missav detail-page description against user preferences.
 */

const GENRE_HINTS = {
  SM: ["绑", "深喉", "受虐", "调教", "虐", "喉咙", "子宫", "sm", "鞭", "蜡烛", "滴蜡", "母狗"],
  NTR: ["ntr", "寝取", "男友", "出轨", "绿", "男朋友", "丈夫"],
  制服: ["制服", "jk", "水手服", "ol", "女仆"],
  中出: ["中出", "内射", "射精", "精液", "怀孕"],
  催眠: ["催眠", "昏迷", "睡眠"],
  凌辱: ["凌辱", "侵犯", "强奸", "轮奸", "人权"],
};

export function analyzeDescription(description, prefs = {}) {
  const text = (description || "").toLowerCase();
  const likes = prefs.likes || {};
  const dislikes = prefs.dislikes || {};
  const matchedLikes = [];
  const matchedDislikes = [];
  const inferredGenres = [];
  const reasons = [];

  const checkTerms = (terms, bucket, weightLabel) => {
    for (const term of terms) {
      const t = String(term).toLowerCase();
      if (!t || !text.includes(t)) continue;
      bucket.push(term);
      reasons.push(`${weightLabel}:${term}`);
    }
  };

  checkTerms(likes.genres || [], matchedLikes, "genre");
  checkTerms(likes.keywords || [], matchedLikes, "keyword");
  checkTerms(dislikes.genres || [], matchedDislikes, "dislike-genre");
  checkTerms(dislikes.keywords || [], matchedDislikes, "dislike-keyword");

  for (const [genre, hints] of Object.entries(GENRE_HINTS)) {
    if (hints.some((h) => text.includes(h.toLowerCase()))) {
      inferredGenres.push(genre);
    }
  }

  for (const genre of likes.genres || []) {
    const hints = GENRE_HINTS[genre] || [genre];
    if (hints.some((h) => text.includes(String(h).toLowerCase()))) {
      if (!matchedLikes.includes(genre)) matchedLikes.push(genre);
      reasons.push(`genre-hint:${genre}`);
    }
  }

  let fitScore = matchedLikes.length * 25 + inferredGenres.length * 10;
  fitScore -= matchedDislikes.length * 40;

  const summary =
    description.length > 200
      ? `${description.slice(0, 200)}…`
      : description;

  return {
    fitScore,
    matchedLikes: [...new Set(matchedLikes)],
    matchedDislikes: [...new Set(matchedDislikes)],
    inferredGenres: [...new Set(inferredGenres)],
    reasons: [...new Set(reasons)],
    summary,
    descriptionLength: description.length,
  };
}

export function genresFromDescription(description) {
  const text = (description || "").toLowerCase();
  const found = [];
  for (const [genre, hints] of Object.entries(GENRE_HINTS)) {
    if (hints.some((h) => text.includes(h.toLowerCase()))) found.push(genre);
  }
  return found;
}
