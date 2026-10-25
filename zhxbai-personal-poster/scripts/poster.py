#!/usr/bin/env python3
"""Build an editable poster or apply a recorded, reversible portrait translation."""
import argparse
import copy
import html
import json
import logging
import math
from pathlib import Path
import re
import shutil
import tempfile

PACKAGE = Path(__file__).resolve().parents[1]
DEFAULT_BOX = {"x": 304, "y": 203, "width": 700, "height": 700}
DEFAULT_COLORS = {"blue": "#0052D9", "ink": "#111C30", "pale": "#EEF4FF", "muted": "#607086"}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def number(value):
    if isinstance(value, bool):
        raise ValueError("Coordinates must be finite numbers.")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Coordinates must be finite numbers.")
    return result


def validate_box(box):
    if set(box) != set(DEFAULT_BOX):
        raise ValueError("portrait_box requires x, y, width, height.")
    result = {key: number(value) for key, value in box.items()}
    if result["width"] <= 0 or result["height"] <= 0:
        raise ValueError("Portrait dimensions must be positive.")
    if result["x"] < 0 or result["y"] < 0 or result["x"] + result["width"] > 1080 or result["y"] + result["height"] > 1440:
        raise ValueError("Portrait box exceeds the canvas; review placement explicitly.")
    return result


def text(value, field):
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string.")
    return value.strip()


def normalize(raw):
    if not isinstance(raw, dict):
        raise ValueError("Config must be a JSON object.")
    data = {}
    for field in ("name", "identity"):
        data[field] = text(raw.get(field, ""), field)
        if not data[field]:
            raise ValueError(f"{field} is required.")
    for field, maximum in (("roles", 2), ("statement", 3), ("credentials", 3)):
        values = raw.get(field, [])
        if not isinstance(values, list) or len(values) > maximum:
            raise ValueError(f"{field} must be a list of at most {maximum} strings.")
        data[field] = [text(item, field) for item in values]
    stats = raw.get("stats", [])
    if not isinstance(stats, list) or len(stats) > 3:
        raise ValueError("stats must contain at most three items.")
    data["stats"] = []
    for item in stats:
        if not isinstance(item, dict) or set(item) != {"value", "label"}:
            raise ValueError("Each stat requires exactly value and label.")
        data["stats"].append({key: text(value, key) for key, value in item.items()})
    for field, default in (("event", ""), ("brand_label", ""), ("kicker", "主讲嘉宾")):
        data[field] = text(raw.get(field, default), field)
    data["portrait_box"] = validate_box(raw.get("portrait_box", DEFAULT_BOX))
    data["colors"] = DEFAULT_COLORS.copy()
    colors = raw.get("colors", {})
    if not isinstance(colors, dict) or set(colors) - set(DEFAULT_COLORS):
        raise ValueError("Unknown brand color field.")
    for key, value in colors.items():
        if not isinstance(value, str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
            raise ValueError(f"Invalid color: {key}")
        data["colors"][key] = value
    return data


def copy_asset(value, base, target, stem, extensions):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing local asset: {stem}")
    path = Path(value).expanduser()
    path = path if path.is_absolute() else base / path
    path = path.resolve()
    if not path.is_file() or path.suffix.lower() not in extensions:
        raise ValueError(f"Missing or unsupported {stem} asset.")
    relative = Path("assets") / (stem + path.suffix.lower())
    shutil.copyfile(path, target / relative)
    return relative.as_posix()


def lines(values):
    return "<br>".join(html.escape(value) for value in values)


def render_html(data):
    escape = html.escape
    box = data["portrait_box"]
    style = ";".join(f"--portrait-{key}:{value:g}px" for key, value in box.items())
    style += ";" + ";".join(f"--{key}:{value}" for key, value in data["colors"].items())
    if data.get("font"):
        font_css = "@font-face{font-family:PosterFont;src:url('" + data["font"] + "');font-weight:700;font-display:block}"
    else:
        font_css = ""
    if data.get("logo"):
        brand = '<img class="logo" src="' + data["logo"] + '" alt="品牌标志">'
    else:
        brand = '<div class="brand-label">' + escape(data["brand_label"]) + '</div>'
    statement = "<br>".join('<span' + (' class="blue"' if i else '') + '>' + escape(value) + '</span>' for i, value in enumerate(data["statement"]))
    stats = "".join('<div class="stat"><div class="number">' + escape(item["value"]) + '</div><p>' + escape(item["label"]) + '</p></div>' for item in data["stats"])
    credentials = "".join('<div class="' + ('credential-main' if i == 0 else 'credential') + '">' + escape(value) + '</div>' for i, value in enumerate(data["credentials"]))
    values = {
        "FONT_CSS": font_css, "STYLE": style, "BRAND": brand,
        "NAME": escape(data["name"]), "IDENTITY": escape(data["identity"]),
        "ROLES": lines(data["roles"]), "STATEMENT": statement,
        "STATS": stats, "STAT_COUNT": str(max(1, len(data["stats"]))),
        "STATS_HIDDEN": " hidden" if not stats else "",
        "CREDENTIALS": credentials, "KICKER": escape(data["kicker"]),
        "EVENT": escape(data["event"]), "EVENT_HIDDEN": " hidden" if not data["event"] else "",
        "PORTRAIT": data["portrait"],
    }
    template = (PACKAGE / "assets/poster.html").read_text(encoding="utf-8")
    return re.sub(r"\{\{([A-Z_]+)\}\}", lambda match: values[match[1]], template)


def publish_directory(output, callback):
    output = output.resolve()
    if output.exists():
        raise ValueError("Output directory already exists; choose a new version.")
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".poster-", dir=output.parent))
    try:
        callback(staging)
        staging.rename(output)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    logging.info("Saved editable poster to %s; render it before delivery", output)


def build(config, output):
    raw = read_json(config)
    data = normalize(raw)

    def create(target):
        (target / "assets").mkdir()
        data["portrait"] = copy_asset(raw.get("portrait"), config.resolve().parent, target, "portrait", {".png", ".jpg", ".jpeg", ".webp", ".svg"})
        for field, extensions in (("logo", {".svg", ".png", ".webp"}), ("font", {".otf", ".ttf", ".woff", ".woff2"})):
            if raw.get(field):
                data[field] = copy_asset(raw[field], config.resolve().parent, target, field, extensions)
        write_json(target / "poster_state.json", {"schema_version": 1, "data": data, "moves": []})
        (target / "poster.html").write_text(render_html(data), encoding="utf-8")

    publish_directory(output, create)


def move(source, output, dx, dy, fraction):
    source = source.resolve()
    if source == output.resolve() or source in output.resolve().parents:
        raise ValueError("Move output must be separate from the source directory.")
    state = read_json(source / "poster_state.json")
    if state.get("schema_version") != 1:
        raise ValueError("Unsupported poster state schema.")
    previous = copy.deepcopy(state["data"]["portrait_box"])
    if fraction is not None:
        if dx is not None or dy is not None or not 0 < fraction <= 1:
            raise ValueError("Use --undo-fraction in (0, 1] without --dx/--dy.")
        if not state["moves"]:
            raise ValueError("No previous recorded move; inspect earlier source coordinates first.")
        last = state["moves"][-1]["delta"]
        dx, dy = -last["x"] * fraction, -last["y"] * fraction
    else:
        dx, dy = number(dx or 0), number(dy or 0)
    if dx == 0 and dy == 0:
        raise ValueError("No displacement requested.")
    current = {**previous, "x": previous["x"] + dx, "y": previous["y"] + dy}
    validate_box(current)
    state["data"]["portrait_box"] = current
    state["moves"].append({"from": previous, "to": current, "delta": {"x": dx, "y": dy}})

    def create(target):
        shutil.copytree(source / "assets", target / "assets")
        # Retain manual HTML edits; translate only the two coordinate variables.
        source_html = (source / "poster.html").read_text(encoding="utf-8")
        for axis in ("x", "y"):
            pattern = rf"(--portrait-{axis}:)[-+\d.eE]+px"
            source_html, count = re.subn(pattern, lambda match: match[1] + f"{current[axis]:g}px", source_html)
            if count != 1:
                raise ValueError(f"Expected exactly one editable portrait {axis} coordinate.")
        (target / "poster.html").write_text(source_html, encoding="utf-8")
        write_json(target / "poster_state.json", state)

    publish_directory(output, create)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("build")
    create.add_argument("config", type=Path)
    create.add_argument("output", type=Path)
    adjust = commands.add_parser("move")
    adjust.add_argument("source", type=Path)
    adjust.add_argument("output", type=Path)
    adjust.add_argument("--dx", type=float)
    adjust.add_argument("--dy", type=float)
    adjust.add_argument("--undo-fraction", type=float)
    args = parser.parse_args()
    try:
        if args.command == "build":
            build(args.config, args.output)
        else:
            move(args.source, args.output, args.dx, args.dy, args.undo_fraction)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        logging.error("Poster operation failed: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
