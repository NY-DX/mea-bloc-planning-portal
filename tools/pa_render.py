"""Render a control tree to Power Apps paste YAML and split it into pastes under a line limit."""

def node(name, control, props, children=None, variant=None):
    return {"name": name, "control": control, "variant": variant, "props": props, "children": children or []}

def render(n, ind=0):
    sp = " " * ind
    out = [f"{sp}- {n['name']}:", f"{sp}    Control: {n['control']}"]
    if n["variant"]:
        out.append(f"{sp}    Variant: {n['variant']}")
    out.append(f"{sp}    Properties:")
    for k in sorted(n["props"]):
        v = n["props"][k].strip("\n")
        if "\n" in v or ": " in v or " #" in v:  # block scalar keeps YAML from misreading the formula
            out.append(f"{sp}      {k}: |-")
            lines = v.split("\n")
            out.append(f"{sp}        ={lines[0]}")
            out += [f"{sp}        {l}" if l else "" for l in lines[1:]]
        else:
            out.append(f"{sp}      {k}: ={v}")
    if n["children"]:
        out.append(f"{sp}    Children:")
        for c in n["children"]:
            out += render(c, ind + 6)
    return out

def split(nodes, target, limit=85):
    """Return [(target, [lines])] so that each paste stays under the limit."""
    pastes, cur = [], []
    def flush():
        nonlocal cur
        if cur: pastes.append((target, cur)); cur = []
    for n in nodes:
        full = render(n)
        if len(full) <= limit:
            if len(cur) + len(full) > limit: flush()
            cur += full
        else:
            flush()
            pastes.append((target, render(dict(n, children=[]))))
            pastes.extend(split(n["children"], n["name"], limit))
    flush()
    return pastes

def split_bfs(nodes, target, limit=85):
    """Like split(), but paste all direct children of a container first (big ones empty),
    then fill each big child. Fewer pastes; order inside each container is preserved."""
    pastes, cur, later = [], [], []
    for n in nodes:
        full = render(n)
        lines = full if len(full) <= limit else render(dict(n, children=[]))
        if len(full) > limit: later.append(n)
        if cur and len(cur) + len(lines) > limit:
            pastes.append((target, cur)); cur = []
        cur += lines
    if cur: pastes.append((target, cur))
    for n in later:
        pastes.extend(split_bfs(n["children"], n["name"], limit))
    return pastes
