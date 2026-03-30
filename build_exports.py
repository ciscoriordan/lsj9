#!/usr/bin/env python3
"""Build processed exports from raw lsj9 data files.

Generates ready-to-use files that downstream consumers (dilemma, iliad-align)
can import directly without doing their own processing.

Input files (raw exports from lsjpre):
  lsj9_headwords.json   - structured headword entries
  lsj9_forms.tsv        - entries with explicit grammar
  lsj9_glosses.jsonl    - hierarchical glosses
  lsj9_indeclinables.json - indeclinable POS entries

Output files:
  lsj9_headwords_flat.json  - simple list of headword strings
  lsj9_headword_pos.json    - {headword: UPOS} from grammar field
  lsj9_short_defs.json      - {headword: short_definition}
  lsj9_glosses_flat.json    - {headword: [list of English glosses]}

Usage:
    python build_exports.py
"""

import json
import re
import unicodedata
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
HEADWORDS_PATH = SCRIPT_DIR / "lsj9_headwords.json"
FORMS_PATH = SCRIPT_DIR / "lsj9_forms.tsv"
GLOSSES_PATH = SCRIPT_DIR / "lsj9_glosses.jsonl"
INDECLINABLES_PATH = SCRIPT_DIR / "lsj9_indeclinables.json"


def _strip_length_marks(s: str) -> str:
    """Strip combining breve (U+0306) and macron (U+0304)."""
    nfd = unicodedata.normalize("NFD", s)
    return unicodedata.normalize("NFC",
        "".join(c for c in nfd if ord(c) not in (0x0306, 0x0304)))


# Grammar field -> UPOS mapping
_GRAMMAR_TO_UPOS = {
    "ὁ": "NOUN",
    "ἡ": "NOUN",
    "τό": "NOUN",
    "ον": "ADJ",
    "ές": "ADJ",
}

# Indeclinable category -> UPOS mapping
_INDECL_TO_UPOS = {
    "adverb": "ADV",
    "preposition": "ADP",
    "conjunction": "CCONJ",
    "particle": "PART",
    "interjection": "INTJ",
}


def build_headwords_flat():
    """Build lsj9_headwords_flat.json - simple list of headword strings.

    Strips editorial hyphens, deduplicates, and strips vowel-length marks
    for consistent matching. Used by dilemma for headword-set filtering.
    """
    print("Building headwords_flat...", end=" ", flush=True)

    with open(HEADWORDS_PATH, encoding="utf-8") as f:
        headwords_raw = json.load(f)

    seen = set()
    headwords = []
    for entry in headwords_raw:
        hw = entry["headword"]
        hw_clean = _strip_length_marks(hw)
        if hw_clean not in seen:
            seen.add(hw_clean)
            headwords.append(hw_clean)

    out_path = SCRIPT_DIR / "lsj9_headwords_flat.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(headwords, f, ensure_ascii=False)

    size_kb = out_path.stat().st_size / 1024
    print(f"{len(headwords):,} headwords ({size_kb:.0f} KB)")
    return headwords


def build_headword_pos():
    """Build lsj9_headword_pos.json - headword to UPOS mapping.

    Sources:
    1. lsj9_forms.tsv grammar field (ὁ/ἡ/τό -> NOUN, ον/ές -> ADJ)
    2. lsj9_headwords.json grammar field (same mapping, fills gaps)
    3. lsj9_indeclinables.json (adverbs, prepositions, etc.)

    For headwords with grammar ὁ/ἡ/τό -> NOUN, ον/ές -> ADJ.
    Verbs (no grammar in forms data, ending in -ω/-μι/-μαι) -> VERB.

    Output: {headword_stripped: UPOS}
    """
    print("Building headword_pos...", end=" ", flush=True)

    pos_map = {}

    # 1. Forms TSV (entries with explicit grammar)
    forms_count = 0
    with open(FORMS_PATH, encoding="utf-8") as f:
        f.readline()  # skip header
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            hw_raw, grammar = parts[0], parts[1]
            hw = _strip_length_marks(hw_raw)
            upos = _GRAMMAR_TO_UPOS.get(grammar)
            if upos and hw not in pos_map:
                pos_map[hw] = upos
                forms_count += 1

    # 2. Headwords JSON (fills in entries not in forms.tsv)
    with open(HEADWORDS_PATH, encoding="utf-8") as f:
        headwords_raw = json.load(f)

    hw_count = 0
    verb_count = 0
    for entry in headwords_raw:
        hw = _strip_length_marks(entry["headword"])
        grammar = entry.get("grammar", "")

        if hw in pos_map:
            continue

        upos = _GRAMMAR_TO_UPOS.get(grammar)
        if upos:
            pos_map[hw] = upos
            hw_count += 1
        elif not grammar:
            # No grammar field - check if it looks like a verb
            hw_plain = unicodedata.normalize("NFD", hw)
            hw_plain = "".join(c for c in hw_plain if not unicodedata.combining(c))
            if (hw_plain.endswith("ω") or hw_plain.endswith("μι")
                    or hw_plain.endswith("μαι")):
                pos_map[hw] = "VERB"
                verb_count += 1

    # 3. Indeclinables (adverbs, prepositions, etc.)
    indecl_count = 0
    if INDECLINABLES_PATH.exists():
        with open(INDECLINABLES_PATH, encoding="utf-8") as f:
            indeclinables = json.load(f)
        for hw_raw, category in indeclinables.items():
            hw = _strip_length_marks(hw_raw)
            upos = _INDECL_TO_UPOS.get(category)
            if upos and hw not in pos_map:
                pos_map[hw] = upos
                indecl_count += 1

    out_path = SCRIPT_DIR / "lsj9_headword_pos.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(pos_map, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = out_path.stat().st_size / 1024
    from collections import Counter
    pos_counts = Counter(pos_map.values())
    breakdown = ", ".join(f"{p}: {n:,}" for p, n in pos_counts.most_common())
    print(f"{len(pos_map):,} entries ({breakdown})")
    print(f"  sources: forms={forms_count:,}, headwords={hw_count:,}, "
          f"verbs={verb_count:,}, indecl={indecl_count:,}")
    return pos_map


def _parse_xref_targets(text, hw_set):
    """Extract cross-reference target headword(s) from a gloss text.

    Handles patterns like:
      "v. βαλλ-αντίδιον"       -> ["βαλλαντίδιον"]
      "v. sub ἁνδάνω"          -> ["ἁνδάνω"]
      "= ἀβακέω, Anacr.74"     -> ["ἀβακέω"]
      "v. ἀεσι-φροσύνη, ἀεσίφρων" -> ["ἀεσιφροσύνη", "ἀεσίφρων"]

    Returns a list of target headwords that exist in hw_set, or empty list.
    """
    _GK_RE = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF]")

    # Match "v. sub X", "v. X", or "= X" at the start
    m = re.match(r"^(?:v\.\s+sub\s+|v\.\s+|=\s+)", text)
    if not m:
        return []

    rest = text[m.end():]

    # Split on commas and semicolons to get candidate tokens
    # But stop at citation patterns (uppercase Latin, numbers, abbreviations)
    candidates = []
    for chunk in re.split(r"[;]", rest):
        for part in chunk.split(","):
            part = part.strip()
            # Extract Greek tokens from this part
            tokens = part.split()
            for tok in tokens:
                tok = tok.strip(".,;:() ")
                if not tok:
                    continue
                # Skip sense numbers like "II", "III", "I.1b"
                if re.match(r"^[IViv]+\.?$", tok) or re.match(r"^[0-9]", tok):
                    continue
                # Skip "sub", "sq.", "q.v.", Latin citation words
                if tok.lower() in ("sub", "sq.", "q.v.", "foreg.", "supr.",
                                    "infr.", "l.c."):
                    continue
                # Must contain Greek characters to be a headword ref
                if _GK_RE.search(tok):
                    # Remove editorial hyphens
                    clean = _strip_length_marks(tok.replace("-", "").replace(" ", ""))
                    if clean in hw_set:
                        candidates.append(clean)
                    # Also try without trailing sense markers
                    clean2 = re.sub(r"[IViv0-9]+$", "", clean)
                    if clean2 and clean2 != clean and clean2 in hw_set:
                        candidates.append(clean2)
                else:
                    # Non-Greek token - stop scanning this chunk
                    break

    # Deduplicate while preserving order
    seen = set()
    result = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            result.append(c)
    return result


def build_crossrefs(hw_set):
    """Build lsj9_crossrefs.json - cross-reference resolution map.

    Parses "v. X" and "= X" patterns from glosses to find headwords that
    are pure cross-references (their only content points to another entry).
    Resolves chains (A -> B -> C becomes A -> C).

    Output: {headword: [target_headword, ...]}
    """
    print("Building crossrefs...", end=" ", flush=True)

    # Collect first gloss per headword
    first_glosses = {}
    with open(GLOSSES_PATH, encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            hw = _strip_length_marks(obj["headword"])
            if hw not in first_glosses:
                first_glosses[hw] = obj["text"]

    # Parse cross-references from entries with short xref-only text
    raw_xrefs = {}
    for hw, text in first_glosses.items():
        # Only treat as xref if the text is short (pure cross-reference)
        if len(text) > 120:
            continue
        targets = _parse_xref_targets(text, hw_set)
        # Don't include self-references
        targets = [t for t in targets if t != hw]
        if targets:
            raw_xrefs[hw] = targets

    # Resolve chains: if A -> B and B -> C, then A -> C
    # Limit depth to avoid cycles
    resolved = {}
    for hw, targets in raw_xrefs.items():
        final_targets = []
        for t in targets:
            visited = {hw}
            current = t
            depth = 0
            while current in raw_xrefs and depth < 5:
                if current in visited:
                    break  # cycle detected
                visited.add(current)
                # Follow first target in the chain
                current = raw_xrefs[current][0]
                depth += 1
            final_targets.append(current)
        # Deduplicate and remove self-references
        seen = set()
        deduped = []
        for t in final_targets:
            if t not in seen and t != hw:
                seen.add(t)
                deduped.append(t)
        if deduped:
            resolved[hw] = deduped

    out_path = SCRIPT_DIR / "lsj9_crossrefs.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(resolved, f, ensure_ascii=False, indent=1)

    size_kb = out_path.stat().st_size / 1024
    # Count how many resolve to a single target
    single = sum(1 for v in resolved.values() if len(v) == 1)
    multi = len(resolved) - single
    print(f"{len(resolved):,} cross-refs ({single:,} single, {multi:,} multi) "
          f"({size_kb:.0f} KB)")
    return resolved


def build_short_defs(crossrefs=None):
    """Build lsj9_short_defs.json - clean English short definitions per headword.

    Extracts from lsj9_glosses.jsonl. For each headword, takes the first
    gloss text and extracts the English definition portion, stripping:
    - Greek text
    - LSJ abbreviations and cross-references (cf., v., etc.)
    - Citation references (author names, work abbreviations)
    - Parenthetical notes
    - Trailing punctuation

    If crossrefs is provided, headwords with no direct definition but a
    cross-reference target that has one will get the target's definition
    with a "(see X)" note appended.

    Output: {headword: "short definition string"}
    """
    print("Building short_defs...", end=" ", flush=True)

    # Greek character ranges
    _GK_RE = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF]")

    # Citation/reference patterns to strip
    _CITE_RE = re.compile(
        r"\b(?:cf\.|v\.|v\.l\.|q\.v\.|l\.c\.|s\.v\.|sc\.|prob\.|perh\.|"
        r"acc\. to|Hom\.|Hes\.|Hdt\.|Thuc\.|Xen\.|Plat\.|Arist\.|Aesch\.|"
        r"Soph\.|Eur\.|Ar\.|Pind\.|Dem\.|Lys\.|Isoc\.|Polyb\.|Plut\.|"
        r"Diosc\.|Gal\.|Hsch\.|Phot\.|EM\.|Et\.Gud\.|Suid\.|Sch\.|"
        r"Eust\.|Strab\.|Paus\.|Ath\.|D\.L\.|A\.D\.|"
        r"Il\.|Od\.|Hel\.|Ag\.|Supp\.|Med\.|Andr\.|Hec\.|Tro\.|"
        r"Phoen\.|Or\.|Bacch\.|Ion|IT|IA|Cyc\.|Rh\.|Alc\.|"
        r"Eq\.|Ach\.|Nub\.|Vesp\.|Av\.|Ran\.|Eccl\.|Pl\.|Lys\.|"
        r"Thesm\.|Pax|N\.T\.|LXX|Sept\.|Inscr\.|Pap\.|"
        r"BGU|PHib|POxy|PLond|PAmh)"
        r"[^,;:]*",
        re.IGNORECASE,
    )

    short_defs = {}

    with open(GLOSSES_PATH, encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            hw = _strip_length_marks(obj["headword"])
            if hw in short_defs:
                continue  # keep first gloss only

            text = obj["text"]

            # Strip parenthetical notes
            text = re.sub(r"\([^)]*\)", "", text)

            # Strip Greek text
            tokens = text.split()
            en_tokens = []
            for tok in tokens:
                if _GK_RE.search(tok):
                    continue
                en_tokens.append(tok)
            text = " ".join(en_tokens)

            # Strip citation/reference patterns
            text = _CITE_RE.sub("", text)

            # Strip remaining reference-like patterns (numbers, dots)
            text = re.sub(r"\d+\.\d+", "", text)

            # Clean up: collapse whitespace, strip punctuation edges
            text = re.sub(r"\s+", " ", text).strip()
            text = text.strip(".,;: ")

            # Strip leading grammar labels
            text = re.sub(
                r"^(indecl\.,?\s*|[Aa]dv\.\s*|[Pp]rep\.\s*|[Cc]onj\.\s*|"
                r"[Pp]article\s*|[Ii]nterj\.\s*)",
                "", text
            ).strip()

            if text and len(text) >= 3:
                # Truncate overly long definitions
                if len(text) > 200:
                    text = text[:200].rsplit(" ", 1)[0]
                short_defs[hw] = text

    # Resolve cross-references: fill in missing definitions from targets
    xref_filled = 0
    if crossrefs:
        for hw, targets in crossrefs.items():
            if hw in short_defs:
                continue
            # Try each target until we find one with a definition
            for target in targets:
                if target in short_defs:
                    short_defs[hw] = f"{short_defs[target]} (see {target})"
                    xref_filled += 1
                    break

    out_path = SCRIPT_DIR / "lsj9_short_defs.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(short_defs, f, ensure_ascii=False, indent=1)

    size_kb = out_path.stat().st_size / 1024
    print(f"{len(short_defs):,} definitions ({size_kb:.0f} KB)")
    if xref_filled:
        print(f"  including {xref_filled:,} resolved from cross-references")
    return short_defs


def build_glosses_flat():
    """Build lsj9_glosses_flat.json - flattened glosses ready for alignment.

    Processes lsj9_glosses.jsonl into: {headword: [list of English glosses]}
    Each gloss is cleaned of Greek text, citations, and sense numbering.

    Output: {headword: ["gloss1", "gloss2", ...]}
    """
    print("Building glosses_flat...", end=" ", flush=True)

    _GK_RE = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF]")

    glosses_flat = {}

    with open(GLOSSES_PATH, encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            hw = _strip_length_marks(obj["headword"])
            text = obj["text"]

            # Strip parenthetical notes
            text = re.sub(r"\([^)]*\)", "", text)

            # Strip Greek text tokens
            tokens = text.split()
            en_tokens = [tok for tok in tokens if not _GK_RE.search(tok)]
            text = " ".join(en_tokens)

            # Clean up
            text = re.sub(r"\s+", " ", text).strip()
            text = text.strip(".,;: ")

            if text and len(text) >= 3:
                glosses_flat.setdefault(hw, []).append(text)

    out_path = SCRIPT_DIR / "lsj9_glosses_flat.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(glosses_flat, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = out_path.stat().st_size / 1024
    total_glosses = sum(len(v) for v in glosses_flat.values())
    print(f"{len(glosses_flat):,} headwords, {total_glosses:,} glosses ({size_kb:.0f} KB)")
    return glosses_flat


def main():
    print("Building lsj9 processed exports\n")

    if not HEADWORDS_PATH.exists():
        print(f"Error: {HEADWORDS_PATH} not found")
        print("Run lsjpre export_lsj9.py first to generate raw data files.")
        return

    headwords = build_headwords_flat()
    build_headword_pos()
    hw_set = set(headwords)
    crossrefs = build_crossrefs(hw_set)
    build_short_defs(crossrefs)
    build_glosses_flat()

    print("\nDone.")


if __name__ == "__main__":
    main()
