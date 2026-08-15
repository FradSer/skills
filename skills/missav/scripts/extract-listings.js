(() => {
  const CODE_RE = /\b([A-Z]{2,10}-\d{2,5})\b/i;

  function isVideoHref(href) {
    try {
      const u = new URL(href);
      if (!/missav\.(ws|com)/i.test(u.hostname)) return false;
      if (/\/pop|\/search\/|\/actresses\/|\/genres\//i.test(u.pathname)) return false;
      const parts = u.pathname.split("/").filter(Boolean);
      const slug = parts[parts.length - 1] || "";
      return /^[a-z0-9][a-z0-9-]*[a-z0-9]$/.test(slug) && slug.length >= 4;
    } catch {
      return false;
    }
  }

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

  function codeFromSlug(slug) {
    const m = (slug || "").match(/^([a-z]{2,10})-(\d{2,5})/i);
    return m ? `${m[1].toUpperCase()}-${m[2]}` : "";
  }

  const byHref = new Map();
  const titleLinks = document.querySelectorAll(
    "a.text-secondary.group-hover\\:text-primary[href*='/cn/']"
  );

  titleLinks.forEach((a) => {
    const href = a.href;
    if (!isVideoHref(href)) return;
    const slug = a.getAttribute("alt") || "";
    const title = a.textContent.trim();
    if (!title) return;

    let duration = "";
    const card =
      a.closest(".thumbnail") ||
      a.closest('[class*="group"]') ||
      a.parentElement?.parentElement;
    if (card) {
      const span = card.querySelector(
        "span.absolute.bottom-1, span[class*='bottom-1'][class*='right-1']"
      );
      if (span) duration = span.textContent.trim();
    }

    const codeMatch = title.match(CODE_RE);
    const code = codeMatch ? codeMatch[1].toUpperCase() : codeFromSlug(slug);
    const dur = parseDuration(duration);

    byHref.set(href, {
      href,
      slug,
      title,
      code,
      duration: dur.raw,
      durationMinutes: dur.minutes,
    });
  });

  return JSON.stringify([...byHref.values()], null, 2);
})();
