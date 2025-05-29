"""This script adds newly inferred cross-references for MONDO from Biomappings.

These are added directly to the version controlled MONDO OBO file.
"""

from bioregistry import parse_curie

from biomappings import load_mappings

EDITABLE_OBO_PATH = "/home/buzgalbraith/workspace/neu/mondo/src/ontology/mondo-edit.obo"
PREFIX_MAP = {
    "icd10": "ICD10WHO",
    "omim.ps": "OMIMPS",
    "omim": "OMIM",
    "mesh": "MESH",
    "ncit": "NCIT",
    "icd11": "icd11.foundation",
    "doid": "DOID",
    "mondo": "MONDO",
}


def format_curie_for_mondo(curie):
    """Format a curie to match the MONDO standard."""
    curie = parse_curie(curie)
    return f"{PREFIX_MAP[curie.prefix]}:{curie.identifier.split(':')[-1]}"


def add_xref(lines, mapping):
    """Add xref to OBO file lines in the appropriate place."""
    look_for_xref = False
    start_xref_idx = None
    def_idx = None
    name_idx = None
    xref_entries = []

    node = format_curie_for_mondo(f"{mapping['source prefix']}:{mapping['source identifier']}")
    xref = format_curie_for_mondo(f"{mapping['target prefix']}:{mapping['target identifier']}")

    for idx, line in enumerate(lines):
        # If this is the block for the given node, we start looking for xrefs
        if line == f"id: {node}\n":
            look_for_xref = True
            continue
        # If we are looking for xrefs
        elif look_for_xref:
            # If we find the definition, we save its index
            if line.startswith("def"):
                def_idx = idx
            if line.startswith("name"):
                name_idx = idx
            # If we find an xref, we keep track of it
            if line.startswith("xref"):
                if not start_xref_idx:
                    start_xref_idx = idx
                xref_entries.append(line[6:].strip())
            # If we've already found some xrefs and then hit a line that
            # is not an xref, then we are done collecting xrefs
            if start_xref_idx and not line.startswith("xref"):
                break
            # If we then find an empty line, we are at the end of the
            # OBO entry and never found any xrefs. In this case, we put
            # the xref after the definition line or the name line
            if not line.strip():
                if def_idx:
                    start_xref_idx = def_idx + 1
                else:
                    start_xref_idx = name_idx + 1
                break

    # make sure the xref is not already present MODNO and if so add
    xref_classes = [c.split()[0] for c in xref_entries]
    if xref not in xref_classes:
        xref_entries.append(xref)
        xref_entries = sorted(xref_entries)
        xr_idx = xref_entries.index(xref)
        lines.insert(start_xref_idx + xr_idx, f'xref: {xref} {{source="MONDO:equivalentTo"}}\n')
    return lines


if __name__ == "__main__":
    mappings = load_mappings()
    mondo_mappings = [m for m in mappings if m["source prefix"] == "mondo"]
    with open(EDITABLE_OBO_PATH) as fh:
        lines = fh.readlines()

    for mapping in mondo_mappings:
        lines = add_xref(lines, mapping)

    with open(EDITABLE_OBO_PATH, "w") as fh:
        fh.writelines(lines)
