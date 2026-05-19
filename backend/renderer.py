import re

MERMAID_RESERVED = {"end", "start", "subgraph", "graph", "flowchart", "class", "click"}

def sanitise_label(label: str) -> str:
    # Remove characters that break Mermaid even inside quotes
    label = label.replace('"', "'")
    label = label.replace('\n', ' ')
    label = label.strip()
    return label

def sanitise_id(node_id: str, label: str) -> str:
    # If id or label is a reserved word, prefix it
    if node_id.lower() in MERMAID_RESERVED or label.lower() in MERMAID_RESERVED:
        return "N_" + node_id
    return node_id

def to_mermaid(data: dict) -> str:
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    # Build id remap in case of reserved words
    id_map = {}
    for node in nodes:
        original = node["id"]
        label = sanitise_label(node["label"])
        id_map[original] = sanitise_id(original, label)

    lines = ["flowchart TD"]

    for node in nodes:
        nid = id_map[node["id"]]
        label = sanitise_label(node["label"])
        shape = node.get("shape", "rect")

        # Use node id as display if label is reserved
        if label.lower() in MERMAID_RESERVED:
            label = label + " "

        if shape == "diamond":
            lines.append(f'    {nid}{{"{label}"}}')
        elif shape == "circle":
            lines.append(f'    {nid}(["{label}"])')
        elif shape == "cylinder":
            lines.append(f'    {nid}[("{label}")]')
        else:
            lines.append(f'    {nid}["{label}"]')

    for edge in edges:
        frm = id_map.get(edge["from"], edge["from"])
        to = id_map.get(edge["to"], edge["to"])
        label = sanitise_label(edge.get("label", ""))
        style = edge.get("style", "solid")

        arrow = "-->" if style == "solid" else "-.->"
        if label:
            lines.append(f'    {frm} {arrow}|"{label}"| {to}')
        else:
            lines.append(f'    {frm} {arrow} {to}')

    return "\n".join(lines)