# Patent drafting reference

Use this file for the parts of a Chinese patent draft that need consistent terminology or a reproducible evidence record. It does not replace the law, current office rules, an official patent database, or professional legal review. Read only the sections relevant to the requested jurisdiction and output.

## Contents

- [Search and source ledger](#search-and-source-ledger)
- [Chinese application structure](#chinese-application-structure)
- [Language conventions](#language-conventions)
- [Feature comparison](#feature-comparison)

## Search and source ledger

Search through the tools and databases actually available in the runtime. An API provider, database, URL shape, authentication variable, result schema, and query syntax are implementation details of that provider; discover them from current documentation or CLI help rather than assuming this reference is executable.

Record each query and result in a ledger with:

| Field | What to record |
| --- | --- |
| Source | Database/site name and URL |
| Query | Exact query or local-file selection |
| Time | Search and page-access date/time with timezone when material |
| Identifier | Publication/application number and kind code when shown |
| Bibliographic facts | Title, jurisdiction, priority/publication dates, applicant/assignee/inventor when shown |
| Evidence | The claim, paragraph, figure, or passage actually inspected |
| Relevance | Which disclosed feature it overlaps or fails to show |
| Confidence | Verified full text, official record, secondary summary, snippet, or unresolved |

Use official patent records or the source's full text for material assertions. A search result snippet, generated summary, or a similar title is a lead, not proof. Deduplicate by stable publication identifier or canonical URL, preserve jurisdiction and kind code, and do not silently turn an application into a granted patent.

Search broadly enough to expose nearby combinations, but report the boundary: databases, jurisdictions, languages, date range, terms, and documents actually inspected. “No result” means no result in that recorded scope; it does not establish worldwide novelty, inventive step, validity, infringement status, or grantability.

## Chinese application structure

The bundled template uses these working sections:

- `背景技术`: relevant existing approaches and the concrete technical problem. Tie claims about existing technology to a source or label them as the inventor's understanding.
- `检索分析`: query record, source ledger, and feature-by-feature comparison. Separate identical, overlapping, missing, and unverified features.
- `发明内容`: problem, technical solution, and supported technical effects. Do not promise commercial or legal outcomes as technical effects.
- `具体实施方式`: enough implementation detail to explain the disclosed solution and its supported alternatives. Mark optional features and assumptions.
- `其他`: alternatives, limitations, dependencies, and open claim or drawing decisions.

The structure is a drafting aid. If the user chooses another jurisdiction or form, follow that jurisdiction's current requirements and preserve the requested structure where it does not conflict.

## Language conventions

Prefer precise technical nouns and causal statements. Define a term before using “所述” to refer to it. Keep component names stable across the background, claims or claim-like statements, and embodiments. Distinguish:

- a technical element from its intended use;
- a required limitation from an optional embodiment;
- an observed or measured effect from a predicted benefit;
- the inventor's disclosure from a source's disclosure.

Product names, brands, UI labels, and colloquial wording may be retained when they identify a real implementation, but do not convert them into technical limitations or remove them mechanically. The following forms are common drafting aids, not mandatory legal phrases:

| Purpose | Possible wording |
| --- | --- |
| Name | `一种……` |
| Inclusion | `包括` / `包含` |
| Purpose | `用于……` |
| Relationship | `根据……确定……` / `响应于……` |
| Optional function | `配置为……` |
| Distinction | `其特征在于……` |

## Feature comparison

Build a feature matrix before writing a novelty conclusion:

| Disclosed feature | Source passage/claim | Same or overlapping element | Missing or different element | Verification status |
| --- | --- | --- | --- | --- |
| [F1] | [URL + passage] | [what matches] | [what differs] | [verified/unverified] |

Do not combine unrelated documents into a single “disclosure” without clearly labelling the combination as an analysis hypothesis. Do not infer a technical effect solely because a source uses similar marketing language. If an effect, date, identifier, or feature cannot be verified, mark it as open and keep it out of an asserted conclusion.
