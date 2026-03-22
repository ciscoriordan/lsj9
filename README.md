# LSJ9: A Digitized Greek-English Lexicon

A structured, machine-readable version of Liddell, Scott, Jones, *A Greek-English Lexicon*, 9th edition (1940). The base text is in the public domain. This dataset adds OCR corrections, structured parsing, and grammatical annotations.

## Data Files

| File | Description |
|------|-------------|
| `lsj9_headwords.json` | 119,450 headwords with grammar, etymology, genitive, homograph markers |
| `lsj9_forms.tsv` | 63,389 entries with explicit grammatical info (article/adjective type, genitive ending) |
| `lsj9_glosses.jsonl` | 176,622 hierarchical glosses (definitions with citations stripped) |
| `lsj9_refs.tsv` | 211,731 structured references (author, work, passage) |
| `lsj9_frequency.json` | Reference counts per headword (55,549 entries) |

## Headword Format

Each entry in `lsj9_headwords.json`:

```json
{
  "id": 42,
  "headword": "ἄβαξ",
  "grammar": "ὁ",
  "genitive": "ᾰκος",
  "etymology": null
}
```

- `grammar`: article (ὁ/ἡ/τό) for nouns, adjective ending (ον/ές) for adjectives, null for verbs
- `genitive`: genitive ending extracted from the first line, where available (17,668 entries)
- `etymology`: parenthesized etymology note, where present (11,335 entries)
- `homograph`: (A)/(B) marker for entries sharing a headword

## Gloss Hierarchy

Glosses follow the LSJ numbering system:

- **major** (I, II, III): top-level sense divisions
- **minor** (1, 2, 3): sub-senses within a major division
- **sub** (a, b, c): sub-sub-senses
- **unnumbered**: entries without numbered divisions (single gloss)

Each gloss has a `parent_id` linking to its containing sense.

## Forms TSV

Tab-separated: `headword`, `grammar`, `genitive`, `etymology`. Designed for consumption by inflection generators (e.g., Wiktionary template expansion).

## License

CC BY 4.0. Attribution required. See [LICENSE](LICENSE).

## Source

Digitized from the public domain 9th edition (Oxford, 1940). Base text from the [Internet Archive scan](https://archive.org/details/Lsj--LiddellScott).
