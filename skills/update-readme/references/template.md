# README structure

Choose the profile that matches the repository. Use the collection profile when the repository
ships several independent items in their own directories. Use the single-artifact profile when it
ships one package, app, library, or service.

Every section needs a real target. Add a `## License` section only when it exists as a licence
file, a badge only when it exists and its target is maintained, and a `README.zh-CN.md` link only
when it exists. When a section has no target, omit it.

An existing README keeps its own structure. Use these profiles for a new README, or for a
structural rewrite that the user requested.

## Collection repository

```markdown
# <Project Name> ![](https://img.shields.io/badge/<label>-<message>-<color>)

[![<Badge Label>](<badge-url>)](<link>)

**English** | [简体中文](README.zh-CN.md)

<One sentence: what this repository is and who it is for.>

## Available <Items>

### [<item-name>](<item-dir>/)

<One or two sentences: what it does and when to use it.>

**Installation:**
<code block with the install command>

<!-- Repeat the item block for each existing item. -->
## Adding a <Item>

1. Create a directory under `<items>/<item-name>/`.
2. Add the descriptor file with the required frontmatter and body.
3. Run the `update-readme` skill to sync both README files.

## License

[<Licence>](LICENSE)
```

## Single-artifact repository

```markdown
# <Project Name>

[English](README.md) | **简体中文**

<One sentence: what this is and who it is for.>

<The facts a reader needs to judge fit: platforms, minimum versions, toolchain, and status such
as private, unlicensed, or unreleased. State a limitation here rather than implying support.>

## Requirements

<Prerequisites that a reader must install first. Omit when the platform provides them.>

## Installation

<Code block with the exact command for the project's package manager.>

## Usage

<One minimal working example, then the one or two calls a reader makes next.>

## Scope and limits

<What the project deliberately does not do, and which failure it reports instead.>

## Verification

<Code block with the test command. Name the arguments and the environment.>

## License

[<Licence>](LICENSE)
```

Omit the language toggle when the repository has one README. Omit `Requirements` and `License`
when the repository supplies neither. Keep the order of the remaining sections.