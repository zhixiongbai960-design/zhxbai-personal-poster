#!/usr/bin/env python3
"""Apply conservative local sharpening without overwriting the source portrait."""
import argparse
import logging
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--radius", type=float, default=0.8)
    parser.add_argument("--percent", type=int, default=70)
    parser.add_argument("--threshold", type=int, default=3)
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve() or args.output.exists():
        parser.error("Output must be a new file, separate from the source.")
    if args.output.suffix.lower() != ".png":
        parser.error("Output must have a .png suffix.")
    if not (0 < args.radius <= 5 and 0 <= args.percent <= 200 and 0 <= args.threshold <= 255):
        parser.error("Invalid sharpening parameters.")
    try:
        from PIL import Image, ImageFilter, ImageOps
    except ImportError:
        parser.error("Pillow is required for this optional operation.")
    try:
        with Image.open(args.source) as original:
            image = ImageOps.exif_transpose(original)
            icc = original.info.get("icc_profile")
            alpha = image.convert("RGBA").getchannel("A") if "A" in image.getbands() or "transparency" in image.info else None
            result = image.convert("RGB").filter(ImageFilter.UnsharpMask(
                radius=args.radius, percent=args.percent, threshold=args.threshold))
            if alpha is not None:
                result.putalpha(alpha)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            result.save(args.output, format="PNG", optimize=True, icc_profile=icc)
        logging.info("Saved %s (%s); source unchanged", args.output, result.size)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Portrait enhancement failed: {exc}\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
