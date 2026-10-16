#!/usr/bin/env python3
"""Create a generic candidate table from run-scoped OAIBOX MongoDB telemetry."""
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

source, output, validation = map(Path, sys.argv[1:4])
keywords = re.compile(
    r"(?:ul.?mcs|\bmcs\b|ul.?bler|\bbler\b|nprb|prb|ulsch_round|harq|"
    r"pusch.*snr|snr.*pusch|ulsch_error)", re.I
)

rows = []
documents = 0
document_counts = Counter()

def walk(value, path=""):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk(child, f"{path}.{key}" if path else key)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, f"{path}[{index}]")
    else:
        yield path, value

for line_number, line in enumerate(source.read_text(errors="replace").splitlines(), 1):
    if not line.strip():
        continue
    try:
        document = json.loads(line)
    except json.JSONDecodeError:
        continue
    documents += 1
    doc_id = str(document.get("_id", ""))
    flattened = list(walk(document))
    document_text = " ".join(f"{path} {value}" for path, value in flattened).lower()
    for name, pattern in {
        "mcs": r"mcs", "bler": r"bler", "nprb_or_prb": r"nprb|\bprb",
        "harq_or_ulsch_rounds": r"harq|ulsch_round",
        "pusch_snr": r"(?:pusch.*snr|snr.*pusch|ulsch_round.*snr)",
    }.items():
        if re.search(pattern, document_text):
            document_counts[name] += 1
    for path, value in flattened:
        text = str(value)
        if keywords.search(path) or keywords.search(text):
            rows.append((line_number, doc_id, path, text))

with output.open("w", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow(("jsonl_line", "document_id", "field_path", "value"))
    writer.writerows(rows)

with validation.open("w") as handle:
    handle.write(f"json_documents={documents}\n")
    handle.write(f"candidate_fields={len(rows)}\n")
    for name in ("mcs", "bler", "nprb_or_prb", "harq_or_ulsch_rounds", "pusch_snr"):
        handle.write(f"{name}_documents={document_counts[name]}\n")

