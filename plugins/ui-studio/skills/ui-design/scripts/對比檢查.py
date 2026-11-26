# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""計算前景色與背景色的 WCAG 2.x 對比值，判斷一般文字、大字與介面元件是否達標。"""

import argparse
import colorsys
import json
import math
import re
import sys

NORMAL_TEXT_MIN = 4.5
LARGE_TEXT_MIN = 3.0
UI_COMPONENT_MIN = 3.0
NAMED = {"white": "#ffffff", "black": "#000000"}
SUPPORTED = "#rgb、#rgba、#rrggbb、#rrggbbaa、rgb()/rgba()、hsl()/hsla()、oklch()、white、black"
NUMBER = r"[-+]?\d*\.?\d+(?:e[-+]?\d+)?"


class ColorError(ValueError):
    pass


def parse_alpha(token: str | None) -> float:
    if token is None:
        return 1.0
    token = token.strip()
    value = float(token[:-1]) / 100 if token.endswith("%") else float(token)
    return min(max(value, 0.0), 1.0)


def split_components(body: str) -> tuple[list[str], str | None]:
    body = body.strip()
    alpha = None
    if "/" in body:
        body, alpha = body.split("/", 1)
    parts = [p for p in re.split(r"[\s,]+", body.strip()) if p]
    if alpha is None and len(parts) == 4:
        alpha = parts.pop()
    return parts, alpha


def parse_hex(text: str) -> tuple[float, float, float, float]:
    digits = text[1:]
    if not re.fullmatch(r"[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8}", digits):
        raise ColorError(f"十六進位色碼 {text} 格式錯誤，應為 #rgb、#rgba、#rrggbb 或 #rrggbbaa")
    if len(digits) in (3, 4):
        digits = "".join(ch * 2 for ch in digits)
    channels = [int(digits[i:i + 2], 16) / 255 for i in range(0, len(digits), 2)]
    if len(channels) == 3:
        channels.append(1.0)
    return channels[0], channels[1], channels[2], channels[3]


def parse_rgb(body: str) -> tuple[float, float, float, float]:
    parts, alpha = split_components(body)
    if len(parts) != 3:
        raise ColorError(f"rgb({body}) 需要 3 個色彩分量")
    channels = []
    for part in parts:
        value = float(part[:-1]) * 2.55 if part.endswith("%") else float(part)
        channels.append(min(max(value, 0.0), 255.0) / 255)
    return channels[0], channels[1], channels[2], parse_alpha(alpha)


def parse_hsl(body: str) -> tuple[float, float, float, float]:
    parts, alpha = split_components(body)
    if len(parts) != 3:
        raise ColorError(f"hsl({body}) 需要色相、飽和度、亮度 3 個分量")
    hue = float(parts[0].removesuffix("deg")) % 360 / 360
    saturation = float(parts[1].rstrip("%")) / 100
    lightness = float(parts[2].rstrip("%")) / 100
    r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
    return r, g, b, parse_alpha(alpha)


def parse_oklch(body: str) -> tuple[float, float, float, float]:
    parts, alpha = split_components(body)
    if len(parts) != 3:
        raise ColorError(f"oklch({body}) 需要亮度、彩度、色相 3 個分量")
    lightness = float(parts[0][:-1]) / 100 if parts[0].endswith("%") else float(parts[0])
    chroma = float(parts[1][:-1]) * 0.004 if parts[1].endswith("%") else float(parts[1])
    hue = math.radians(float(parts[2].removesuffix("deg")))
    a, b = chroma * math.cos(hue), chroma * math.sin(hue)
    l_ = (lightness + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (lightness - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (lightness - 0.0894841775 * a - 1.2914855480 * b) ** 3
    linear = (
        4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
        -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
        -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_,
    )
    r, g, b = (encode_srgb(min(max(c, 0.0), 1.0)) for c in linear)
    return r, g, b, parse_alpha(alpha)


def parse_color(text: str) -> tuple[float, float, float, float]:
    value = NAMED.get(text.strip().lower(), text.strip().lower())
    if value.startswith("#"):
        return parse_hex(value)
    match = re.fullmatch(r"(rgba?|hsla?|oklch)\((.*)\)", value)
    if not match:
        raise ColorError(f"無法辨識的顏色 {text}；支援 {SUPPORTED}")
    func, body = match.groups()
    if not re.fullmatch(rf"(?:\s|,|/|%|deg|{NUMBER})*", body):
        raise ColorError(f"顏色 {text} 含有無法辨識的內容；分量只能是數字、百分比或 deg")
    if func.startswith("rgb"):
        return parse_rgb(body)
    if func.startswith("hsl"):
        return parse_hsl(body)
    return parse_oklch(body)


def encode_srgb(channel: float) -> float:
    return 12.92 * channel if channel <= 0.0031308 else 1.055 * channel ** (1 / 2.4) - 0.055


def decode_srgb(channel: float) -> float:
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: tuple[float, float, float]) -> float:
    r, g, b = (decode_srgb(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def composite(fg: tuple[float, float, float, float], bg: tuple[float, float, float]) -> tuple[float, float, float]:
    alpha = fg[3]
    return tuple(fg[i] * alpha + bg[i] * (1 - alpha) for i in range(3))


def check_pair(pair: str) -> dict:
    if "|" not in pair:
        raise ColorError(f"配對 {pair} 缺少分隔符號 |；格式為 \"前景色|背景色\"，例如 \"#666|#fff\"")
    fg_text, bg_text = (part.strip() for part in pair.split("|", 1))
    fg, bg = parse_color(fg_text), parse_color(bg_text)
    if bg[3] < 1.0:
        raise ColorError(f"背景色 {bg_text} 帶有透明度，無法單獨判斷；請改傳它疊在底色上之後的實際顏色")
    fg_rgb = composite(fg, bg[:3])
    lighter, darker = sorted((relative_luminance(fg_rgb), relative_luminance(bg[:3])), reverse=True)
    ratio = (lighter + 0.05) / (darker + 0.05)
    shown = math.floor(ratio * 100) / 100
    return {
        "foreground": fg_text,
        "background": bg_text,
        "ratio": shown,
        "normal_text_pass": ratio >= NORMAL_TEXT_MIN,
        "large_text_pass": ratio >= LARGE_TEXT_MIN,
        "ui_component_pass": ratio >= UI_COMPONENT_MIN,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="計算前景色與背景色的 WCAG 2.x 對比值，判斷一般文字（4.5:1）、大字（3:1）與介面元件（3:1）是否達標。"
    )
    parser.add_argument(
        "pairs",
        nargs="+",
        help=f"一組或多組 \"前景色|背景色\"，例如 \"#666|#fff\" \"oklch(0.6 0.1 250)|#0b0b0f\"；支援 {SUPPORTED}",
    )
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    results, failed = [], False
    for pair in args.pairs:
        try:
            results.append(check_pair(pair))
        except (ColorError, ValueError) as error:
            print(f"錯誤：{pair}：{error}", file=sys.stderr)
            failed = True
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
