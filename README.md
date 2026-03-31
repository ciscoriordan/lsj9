# LSJ9: A Digitized Greek-English Lexicon

A structured, machine-readable version of Liddell, Scott, Jones, *A Greek-English Lexicon*, 9th edition (1940). The base text is in the public domain. This dataset adds OCR corrections, structured parsing, and grammatical annotations. Used by [Dilemma](https://github.com/ciscoriordan/dilemma) (Greek lemmatizer).

## Data Files

| File | Description |
|------|-------------|
| `lsj9_headwords.json` | 119,450 headwords with grammar, etymology, genitive, homograph markers |
| `lsj9_forms.tsv` | 63,389 entries with explicit grammatical info (article/adjective type, genitive ending) |
| `lsj9_glosses.jsonl` | 177,190 hierarchical glosses (definitions with citations stripped) |
| `lsj9_refs.tsv` | 211,585 structured references (author, work, passage) |
| `lsj9_frequency.json` | Reference counts per headword (55,495 entries) |
| `lsj9_indeclinables.json` | Indeclinable entries with POS categories (adverbs, prepositions, conjunctions, particles, interjections) |
| `lsj9_authors.json` | Authors & works abbreviation table (from front matter) |
| `lsj9_abbreviations.json` | General abbreviations, epigraphical publications, papyri, periodicals |

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
- `genitive`: genitive ending extracted from the first line, where available (17,667 entries)
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

## Processed Exports

These derived files are built from the raw data by `build_exports.py`. They provide ready-to-use formats for downstream consumers.

| File | Description | Consumers |
|------|-------------|-----------|
| `lsj9_headwords_flat.json` | 118,764 headword strings (deduplicated, length-marks stripped) | dilemma (headword-set filtering) |
| `lsj9_headword_pos.json` | 135,180 headword-to-UPOS mappings (NOUN, ADJ, VERB, ADV, ADP, etc.) | dilemma (POS disambiguation) |
| `lsj9_crossrefs.json` | 7,678 cross-reference mappings (headword to target headwords) | LSJ10 Kindle edition |
| `lsj9_short_defs.json` | 111,506 clean English short definitions per headword (includes 3,625 resolved cross-references) | dilemma |
| `lsj9_glosses_flat.json` | 115,330 headwords with 173,317 flattened English glosses | dilemma |

To rebuild after updating raw data:

```bash
python build_exports.py
```

### Headword POS Format

`lsj9_headword_pos.json` maps each headword to a UPOS tag:

```json
{
  "ἄβαξ": "NOUN",
  "ἀγαθός": "ADJ",
  "ἄγω": "VERB",
  "ἄγαν": "ADV"
}
```

Sources: grammar field (ὁ/ἡ/τό -> NOUN, ον/ές -> ADJ), verb-ending heuristics (-ω/-μι/-μαι -> VERB), and `lsj9_indeclinables.json` (ADV, ADP, CCONJ, PART, INTJ).

### Short Definitions Format

`lsj9_short_defs.json` provides one concise English definition per headword, with Greek text, citations, and abbreviations stripped:

```json
{
  "ἀγαθός": "good",
  "ἄγω": "lead, carry, bring",
  "ἀδράφαξυς": "orach, Atriplex rosea (see ἀτράφαξυς)"
}
```

Entries that are pure cross-references ("v. X", "= X") with no direct English definition get the target's definition with a `(see X)` note, resolved via `lsj9_crossrefs.json`.

### Cross-References Format

`lsj9_crossrefs.json` maps headwords that are cross-references to their resolved target headword(s). Chains (A -> B -> C) are resolved so A points directly to C.

```json
{
  "ἀδικήω": ["ἀδικέω"],
  "ἀασιφροσύνη": ["ἀεσιφροσύνη", "ἀεσίφρων"]
}
```

Parsed from "v. X", "v. sub X", and "= X" patterns in gloss text. Editorial hyphens in targets (e.g. "ἀεσι-φροσύνη") are removed to match headword forms. Only targets that exist in the headword list are included.

## How This Differs from Other Digital LSJ Projects

Two other digital LSJ datasets are widely used:

- [**LSJLogeion**](https://github.com/helmadik/LSJLogeion) (Helma Dik, U. of Chicago) - 86 XML files derived from the Perseus Digital Library TEI markup. Corrections focus on character encoding, entry reorganization, and language tagging. Used by the Logeion search tool.
- [**lsj-js**](https://github.com/perseids-project/lsj-js) (Perseids Project) - A single JSON blob of the same Perseus/Internet Archive text, bundled into a JavaScript web app for offline searching.

LSJLogeion derives from the **Perseus Project's manual keyboard entry of LSJ** (mid-1990s, funded by the National Science Foundation), converted from TLG Beta Code to Unicode with extensive editorial corrections by Helma Dik. LSJ9 and lsj-js both use the [Internet Archive `lsj.txt`](https://archive.org/details/Lsj--LiddellScott).

All digital LSJ versions contain errors from their respective digitization processes. lsj9 is correcting these systematically via OCR against high-resolution scans of the original printed edition. Typical issues:

| Error type | Example (before) | Corrected |
|---|---|---|
| Missing breathing marks | `αγαθός` | `ἀγαθός` |
| Citation spacing | `E.Rh.990,cf.Supp.208` | `E. Rh. 990, cf. Supp. 208` |
| Garbled diacritics | `δστα` | `ὀστᾶ` |
| Line-break artifacts | `causing\nhoarseness` | `causing hoarseness` |
| Character confusions | `FVarso` | `PVarsov.` (θ/δ, P/F) |

The differences between projects are in what is done with the text:

| | LSJ9 (this project) | LSJLogeion | lsj-js |
|---|---|---|---|
| **Format** | Structured files (JSON, TSV, JSONL) | TEI XML (86 files) | Single JSON blob |
| **OCR corrections** | Systematic, pipeline-based | Manual, incremental | None |
| **Headword parsing** | 119,450 with grammar, genitive, etymology | Headwords in XML tags | Flat key-value |
| **Gloss extraction** | 176,622 hierarchical glosses (I.1.a structure) | Embedded in XML prose | None |
| **Reference parsing** | 211,731 structured refs (author, work, passage) | Inline citations | None |
| **Designed for** | Programmatic consumption (NLP, apps, inflection tools) | Human reading, Logeion integration | Browser-based lookup |

The key difference: LSJLogeion and lsj-js preserve the dictionary as formatted text (XML or JSON). LSJ9 decomposes it into structured, independently queryable data - headwords, grammatical forms, sense hierarchies, and citation networks - suitable for building applications, training models, or cross-referencing with other corpora.

## OCR Pipeline

### Base text corrections (lsj9)

The base text (`lsj.txt`) comes from the [Internet Archive](https://archive.org/details/Lsj--LiddellScott). Its exact provenance is unknown. It contains thousands of OCR errors, particularly in polytonic Greek (missing breathing marks, garbled diacritics, character confusions between similar glyphs like θ/δ). We are systematically correcting these using a multi-model OCR pipeline against a high-resolution scan of the original 1940 Oxford edition:

- **Qwen3-VL** (primary): Vision-language model run on column images. Produces proper polytonic Greek with breathing marks and accents. Run locally on GPU.
- **Google Cloud Vision** (secondary): Document text detection API. Better at English text, citation punctuation, and reference numbers. Weaker on Greek diacritics.
- **Dilemma** spell-checker: Validates Greek tokens against a 12.3M-form lookup table and suggests corrections by edit distance.

The two OCR sources are cross-validated, and corrections are applied programmatically. This is an ongoing process.

### Supplement OCR (lsj10 only)

LSJ9 does **not** include content from the 1996 Revised Supplement - that is part of the separate LSJ10 project. For context, the supplement OCR pipeline tested three vision-language models on the 348-page supplement PDF:

| Model | Details | Notes |
|-------|---------|-------|
| Qwen2.5-VL-7B-Instruct | float16, 1024px column images | Original run, good baseline |
| Qwen3-VL-8B-Instruct | Re-OCR of worst pages | Some hallucinations on complex pages |
| Qwen3-VL-30B-A3B-Instruct | MoE model, bf16 on A100 80GB | Zero hallucinations, best quality |

The Qwen3-VL-30B MoE model produced the cleanest output with no hallucinations, making it the preferred choice for high-fidelity Greek lexicon OCR.

## License

CC BY 4.0. Attribution required. See [LICENSE](LICENSE).

## Source

Digitized from the public domain 9th edition (Oxford, 1940). Base text from the [Internet Archive scan](https://archive.org/details/Lsj--LiddellScott).
