#!/usr/bin/env node
/**
 * Build missav search or listing URLs.
 *
 * Usage:
 *   node build-search-url.mjs search ssis
 *   node build-search-url.mjs search "枫ふうあ" --filter chinese-subtitle
 *   node build-search-url.mjs category dm247
 */

function parseArgs(argv) {
  const opts = { filter: null };
  const positional = [];
  for (let i = 2; i < argv.length; i++) {
    if (argv[i] === "--filter" && argv[i + 1]) {
      opts.filter = argv[++i];
    } else {
      positional.push(argv[i]);
    }
  }
  return { ...opts, positional };
}

function buildUrl(mode, query, filter) {
  const base = "https://missav.ws";
  if (mode === "search") {
    const segment = encodeURIComponent(query).replace(/%20/g, "+");
    let url = `${base}/cn/search/${segment}`;
    if (filter) url += `?filters=${encodeURIComponent(filter)}`;
    return url;
  }
  if (mode === "category") {
    const slug = query.replace(/^\/+|\/+$/g, "");
    return `${base}/${slug}${slug.endsWith("/cn") ? "" : "/cn"}`;
  }
  throw new Error(`Unknown mode: ${mode}. Use "search" or "category".`);
}

function main() {
  const { positional, filter } = parseArgs(process.argv);
  const [mode, query] = positional;
  if (!mode || !query) {
    console.error(`Usage:
  node build-search-url.mjs search <keyword> [--filter chinese-subtitle|english-subtitle]
  node build-search-url.mjs category <slug>   # e.g. dm247

Examples:
  node build-search-url.mjs search ssis
  node build-search-url.mjs search "枫ふうあ" --filter chinese-subtitle
  node build-search-url.mjs category dm247`);
    process.exit(1);
  }
  console.log(buildUrl(mode, query, filter));
}

main();
