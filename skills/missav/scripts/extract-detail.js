(() => {
  const CODE_RE = /\b([A-Z]{2,10}-\d{2,5})\b/i;

  function parseDuration(text) {
    const t = (text || "").trim();
    if (!t || /无码|uncensored|leak/i.test(t)) return { raw: t, minutes: null };
    const parts = t.split(":").map(Number);
    if (parts.some(Number.isNaN)) return { raw: t, minutes: null };
    let seconds = 0;
    if (parts.length === 3) seconds = parts[0] * 3600 + parts[1] * 60 + parts[2];
    else if (parts.length === 2) seconds = parts[0] * 60 + parts[1];
    else return { raw: t, minutes: null };
    return { raw: t, minutes: Math.round((seconds / 60) * 10) / 10 };
  }

  const href = location.href;
  const slug = location.pathname.split("/").filter(Boolean).pop() || "";
  const cloudflare = /just a moment|请稍候/i.test(document.title);
  const isPopRedirect = /\/pop(\?|$)/i.test(href) || /tsyndicate|bit\.ly/i.test(href);
  const isVideoPage = /missav\.(ws|com)\/cn\/[a-z0-9-]+$/i.test(href.replace(/\/$/, ""));

  if (cloudflare || isPopRedirect || !isVideoPage) {
    return JSON.stringify(
      {
        href,
        slug,
        title: document.title,
        code: "",
        description: "",
        tags: [],
        performers: [],
        genres: [],
        duration: "",
        durationMinutes: null,
        blocked: true,
        blockReason: cloudflare ? "cloudflare" : isPopRedirect ? "ad-redirect" : "not-video-page",
      },
      null,
      2
    );
  }

  [...document.querySelectorAll("button, a, span")]
    .filter((el) => /^(展开|更多|显示更多|show more|read more)$/i.test(el.textContent.trim()))
    .forEach((el) => {
      try {
        el.click();
      } catch (_) {}
    });

  const descEl =
    document.querySelector("div.mb-1.text-secondary.break-all.line-clamp-none") ||
    document.querySelector("div.mb-1.text-secondary.break-all") ||
    document.querySelector("div.text-secondary.break-all") ||
    [...document.querySelectorAll("div.text-secondary")].find(
      (el) => (el.textContent || "").trim().length > 80
    );

  const description = descEl ? descEl.textContent.replace(/\s+/g, " ").trim() : "";

  const title =
    document.querySelector("h1")?.textContent.trim() ||
    document.querySelector('meta[property="og:title"]')?.content ||
    document.title;

  const codeMatch = title.match(CODE_RE);
  const slugMatch = slug.match(/^([a-z]{2,10})-(\d{2,5})/i);
  const code = codeMatch
    ? codeMatch[1].toUpperCase()
    : slugMatch
      ? `${slugMatch[1].toUpperCase()}-${slugMatch[2]}`
      : "";

  const tags = [...document.querySelectorAll('a[href*="/cn/genres/"], a[href*="/cn/tags/"]')]
    .map((a) => a.textContent.trim())
    .filter(Boolean);

  const performers = [
    ...document.querySelectorAll('a[href*="/cn/actresses/"], a[href*="/cn/actors/"]'),
  ]
    .map((a) => a.textContent.trim())
    .filter(Boolean);

  let duration = "";
  const timeEl = [...document.querySelectorAll("time, span")].find((el) =>
    /^\d{1,2}:\d{2}(:\d{2})?$/.test(el.textContent.trim())
  );
  if (timeEl) duration = timeEl.textContent.trim();
  const dur = parseDuration(duration);

  return JSON.stringify(
    {
      href,
      slug,
      title,
      code,
      description,
      tags: [...new Set(tags)],
      performers: [...new Set(performers)],
      genres: [...new Set(tags)],
      duration: dur.raw,
      durationMinutes: dur.minutes,
      blocked: !description && !code,
      blockReason: !description && !code ? "empty-detail" : null,
    },
    null,
    2
  );
})();
