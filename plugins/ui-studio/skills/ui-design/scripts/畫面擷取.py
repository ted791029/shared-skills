# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "playwright>=1.65,<2",
#     "axe-playwright-python>=0.1.9,<0.2",
# ]
# ///
"""以 Chromium 實際渲染畫面：shot 在多種寬度擷取截圖並偵測溢出、超出畫面、渲染後對比與 axe-core 違規；
motion 擷取一段動畫的關鍵影格與 filmstrip。結果寫入 --out 資料夾的 report.json，stdout 輸出摘要 JSON。
結束碼：0 成功；3 找不到 Chromium；4 目標無法開啟；1 其他失敗。"""

import argparse
import hashlib
import importlib.util
import json
import re
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

EXIT_NO_BROWSER = 3
EXIT_TARGET = 4
DEFAULT_WIDTHS = "390,768,1024,1440"
VIEWPORT_HEIGHT = 900
LOGIN_URL = re.compile(r"(login|signin|sign-in|log-in|auth)", re.IGNORECASE)
ISSUE_LIMIT = 50
INSTALL_HINT = "uv run --with playwright playwright install chromium"

PROBE_JS = r"""
(limit) => {
  const vw = window.innerWidth;
  const visible = (el) => {
    const s = getComputedStyle(el);
    if (s.display === 'none' || s.visibility === 'hidden' || Number(s.opacity) === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const selector = (el) => {
    if (el.id) return '#' + CSS.escape(el.id);
    const tid = el.getAttribute('data-testid');
    if (tid) return `[data-testid="${tid}"]`;
    const parts = [];
    let node = el;
    while (node && node.nodeType === 1 && parts.length < 4) {
      let part = node.tagName.toLowerCase();
      const cls = [...node.classList].slice(0, 2).map((c) => '.' + CSS.escape(c)).join('');
      part += cls;
      const parent = node.parentElement;
      if (parent) {
        const same = [...parent.children].filter((c) => c.tagName === node.tagName);
        if (same.length > 1) part += `:nth-of-type(${same.indexOf(node) + 1})`;
      }
      parts.unshift(part);
      if (node.id) break;
      node = parent;
    }
    return parts.join(' > ');
  };
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = 1;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  const rgba = (color) => {
    ctx.clearRect(0, 0, 1, 1);
    ctx.fillStyle = '#000';
    ctx.fillStyle = color;
    ctx.fillRect(0, 0, 1, 1);
    const d = ctx.getImageData(0, 0, 1, 1).data;
    return [d[0], d[1], d[2], d[3] / 255];
  };
  const over = (top, bottom) => {
    const a = top[3] + bottom[3] * (1 - top[3]);
    if (a === 0) return [0, 0, 0, 0];
    return [0, 1, 2].map((i) => (top[i] * top[3] + bottom[i] * bottom[3] * (1 - top[3])) / a).concat([a]);
  };
  const background = (el) => {
    const layers = [];
    let image = false;
    for (let node = el; node && node.nodeType === 1; node = node.parentElement) {
      const s = getComputedStyle(node);
      if (s.backgroundImage && s.backgroundImage !== 'none') image = true;
      const c = rgba(s.backgroundColor);
      if (c[3] > 0) layers.push(c);
      if (c[3] >= 1) break;
    }
    let result = [255, 255, 255, 1];
    for (const layer of layers.reverse()) result = over(layer, result);
    return { color: result, image };
  };
  const lum = (c) => {
    const ch = c.slice(0, 3).map((v) => {
      v /= 255;
      return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2];
  };
  const hex = (c) => '#' + c.slice(0, 3).map((v) => Math.round(v).toString(16).padStart(2, '0')).join('');
  const overflow = [], offscreen = [], contrast = [];
  let checked = 0;
  for (const el of document.body.querySelectorAll('*')) {
    if (!visible(el)) continue;
    const s = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    const clips = ['hidden', 'clip', 'scroll', 'auto'].includes(s.overflowX);
    if (!clips && el.scrollWidth > el.clientWidth + 1 && el.clientWidth > 0 && overflow.length < limit) {
      overflow.push({ selector: selector(el), overflow_px: el.scrollWidth - el.clientWidth });
    }
    if ((r.right > vw + 1 || r.left < -1) && s.position !== 'fixed' && offscreen.length < limit) {
      offscreen.push({ selector: selector(el), left: Math.round(r.left), right: Math.round(r.right), viewport: vw });
    }
    const ownText = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
    if (!ownText) continue;
    checked += 1;
    const bg = background(el);
    const fg = over(rgba(s.color), bg.color);
    const l1 = lum(fg), l2 = lum(bg.color);
    const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
    const size = parseFloat(s.fontSize);
    const bold = parseInt(s.fontWeight, 10) >= 700;
    const large = size >= 24 || (size >= 18.66 && bold);
    const required = large ? 3 : 4.5;
    if ((ratio < required || bg.image) && contrast.length < limit) {
      contrast.push({
        selector: selector(el), foreground: hex(fg), background: hex(bg.color),
        ratio: Math.round(ratio * 100) / 100, font_size_px: size, large, required,
        passes: ratio >= required, background_image: bg.image,
      });
    }
  }
  return {
    document_scroll_width: document.documentElement.scrollWidth, viewport_width: vw,
    horizontal_scroll: document.documentElement.scrollWidth > vw + 1,
    has_password_field: !!document.querySelector('input[type="password"]'),
    text_elements_checked: checked, overflow, offscreen, contrast,
  };
}
"""


class ScriptError(Exception):
    def __init__(self, message: str, code: int = 1):
        super().__init__(message)
        self.code = code


def log(message: str) -> None:
    print(message, file=sys.stderr)


def target_url(target: str) -> str:
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", target):
        return target
    path = Path(target).expanduser().resolve()
    if not path.is_file():
        raise ScriptError(f"找不到目標檔案 {path}。請傳入存在的 HTML 檔路徑，或以 http:// 開頭的網址。", EXIT_TARGET)
    return path.as_uri()


def with_state(url: str, state: str | None) -> str:
    if not state:
        return url
    parts = urlsplit(url)
    query = f"{parts.query}&state={state}" if parts.query else f"state={state}"
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))


def out_dir(value: str | None, prefix: str) -> Path:
    path = Path(value).expanduser().resolve() if value else Path(tempfile.mkdtemp(prefix=prefix))
    path.mkdir(parents=True, exist_ok=True)
    return path


def axe_source() -> str:
    spec = importlib.util.find_spec("axe_playwright_python")
    if spec is None or not spec.submodule_search_locations:
        raise ScriptError("找不到 axe-playwright-python。請以 uv run 執行本腳本，讓 PEP 723 宣告的依賴自動安裝。")
    path = Path(next(iter(spec.submodule_search_locations))) / "axe.min.js"
    return path.read_text(encoding="utf-8")


def launch(playwright):
    try:
        return playwright.chromium.launch()
    except Exception as error:  # Playwright 找不到瀏覽器時丟出一般 Error
        text = str(error)
        if "Executable doesn't exist" in text or "playwright install" in text:
            raise ScriptError(f"找不到 Chromium。請先執行：{INSTALL_HINT}", EXIT_NO_BROWSER)
        raise ScriptError(f"無法啟動 Chromium：{text.splitlines()[0]}")


def open_page(context, url: str, timeout: int):
    page = context.new_page()
    try:
        page.goto(url, wait_until="load", timeout=timeout)
    except Exception as error:
        raise ScriptError(f"無法開啟 {url}：{str(error).splitlines()[0]}。請確認檔案存在或開發伺服器已啟動。", EXIT_TARGET)
    try:
        page.wait_for_load_state("networkidle", timeout=min(timeout, 5000))
    except Exception:
        log(f"警告：{url} 在 5 秒內沒有進入 networkidle，照目前畫面擷取")
    return page


def run_shot(args) -> dict:
    from playwright.sync_api import sync_playwright

    url = target_url(args.target)
    widths = [int(item) for item in args.widths.split(",") if item.strip()]
    states = [item.strip() for item in args.states.split(",") if item.strip()] if args.states else [None]
    schemes = [item.strip() for item in args.color_scheme.split(",") if item.strip()]
    folder = out_dir(args.out, "ui-design-shot-")
    axe = axe_source()
    shots = []
    with sync_playwright() as playwright:
        browser = launch(playwright)
        for scheme in schemes:
            for width in widths:
                context = browser.new_context(viewport={"width": width, "height": VIEWPORT_HEIGHT}, color_scheme=scheme)
                for state in states:
                    page_url = with_state(url, state)
                    page = open_page(context, page_url, args.timeout)
                    name = f"{scheme}-{width}" + (f"-{state}" if state else "") + ".png"
                    page.screenshot(path=str(folder / name), full_page=not args.viewport_only)
                    probe = page.evaluate(PROBE_JS, ISSUE_LIMIT)
                    page.evaluate(axe)
                    result = page.evaluate("() => axe.run(document, { resultTypes: ['violations'] })")
                    violations = [
                        {"id": item["id"], "impact": item.get("impact"), "help": item["help"], "help_url": item.get("helpUrl"),
                         "targets": [", ".join(map(str, node.get("target", []))) for node in item.get("nodes", [])][:ISSUE_LIMIT]}
                        for item in result.get("violations", [])
                    ]
                    final_url = page.url
                    shots.append({
                        "file": str(folder / name), "width": width, "color_scheme": scheme, "state": state,
                        "url": page_url, "final_url": final_url,
                        "suspected_login": bool(LOGIN_URL.search(urlsplit(final_url).path)) or probe.pop("has_password_field"),
                        **{key: value for key, value in probe.items() if key != "has_password_field"},
                        "axe_violations": violations,
                    })
                    page.close()
                context.close()
        browser.close()
    report = {"command": "shot", "target": args.target, "out": str(folder), "shots": shots}
    (folder / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return {
        "out": str(folder), "report": str(folder / "report.json"), "screenshots": len(shots),
        "suspected_login": [item["file"] for item in shots if item["suspected_login"]],
        "overflow": sum(len(item["overflow"]) for item in shots), "offscreen": sum(len(item["offscreen"]) for item in shots),
        "contrast_issues": sum(len(item["contrast"]) for item in shots),
        "axe_violations": sum(len(item["axe_violations"]) for item in shots),
    }


def load_steps(path: str | None) -> list[dict]:
    if not path:
        return []
    file = Path(path).expanduser().resolve()
    try:
        steps = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ScriptError(f"無法讀取步驟檔 {file}（{error}）。格式為陣列，例如 [{{\"click\": \"#open\"}}, {{\"wait\": 200}}]。")
    if not isinstance(steps, list) or not all(isinstance(item, dict) and len(item) == 1 for item in steps):
        raise ScriptError(f"{file} 的格式不對：必須是陣列，每個元素只有 click、hover、press 或 wait 其中一個鍵。")
    for item in steps:
        key = next(iter(item))
        if key not in ("click", "hover", "press", "wait"):
            raise ScriptError(f"{file} 有不支援的步驟「{key}」。只接受 click、hover、press、wait。")
    return steps


def apply_steps(page, steps: list[dict]) -> None:
    for item in steps:
        key, value = next(iter(item.items()))
        if key == "click":
            page.click(value)
        elif key == "hover":
            page.hover(value)
        elif key == "press":
            page.keyboard.press(value)
        else:
            page.wait_for_timeout(int(value))


REGION_JS = """(selector) => {
  const el = document.querySelector(selector);
  if (!el) return null;
  const r = el.getBoundingClientRect();
  const pad = 24;
  const x = Math.max(r.left - pad, 0), y = Math.max(r.top - pad, 0);
  return { x, y, width: Math.min(r.right + pad, innerWidth) - x, height: Math.min(r.bottom + pad, innerHeight) - y };
}"""


def capture_region(page, selector: str) -> bytes:
    # 不用 locator.screenshot：它會等元素靜止，動畫進行中拍不到；改為每次讀取位置後裁切畫面
    box = page.evaluate(REGION_JS, selector)
    if not box or box["width"] < 1 or box["height"] < 1:
        return page.screenshot(animations="allow")
    return page.screenshot(clip=box, animations="allow")


def run_motion(args) -> dict:
    from playwright.sync_api import sync_playwright

    url = target_url(args.target)
    folder = out_dir(args.out, "ui-design-motion-")
    setup = load_steps(args.setup)
    steps = [{"click": args.click}] if args.click else load_steps(args.steps)
    limitations = []
    frames: list[tuple[float, bytes]] = []
    with sync_playwright() as playwright:
        browser = launch(playwright)
        context = browser.new_context(viewport={"width": args.width, "height": VIEWPORT_HEIGHT},
                                      reduced_motion="reduce" if args.reduced_motion else "no-preference")
        slow = max(args.slowdown, 1)

        def slow_down(target_page) -> None:
            # 以 CDP 放慢 CSS 動畫、transition 與 Web Animations，讓截圖跟得上；requestAnimationFrame 驅動的動畫不受影響
            session = context.new_cdp_session(target_page)
            session.send("Animation.enable")
            session.send("Animation.setPlaybackRate", {"playbackRate": 1 / slow})

        if steps:
            page = open_page(context, url, args.timeout)
            apply_steps(page, setup)
            page.wait_for_timeout(args.settle)
            before = capture_region(page, args.region)
            slow_down(page)
            start = time.monotonic()
            apply_steps(page, steps)
        else:
            page = context.new_page()
            slow_down(page)
            start = time.monotonic()
            try:
                page.goto(url, wait_until="commit", timeout=args.timeout)
            except Exception as error:
                raise ScriptError(f"無法開啟 {url}：{str(error).splitlines()[0]}", EXIT_TARGET)
            before = None
            limitations.append("沒有 --click 或 --steps：從頁面載入開始擷取，沒有 before 影格")
        stable_since = None
        last_hash = None
        if slow > 1:
            limitations.append(f"動畫以 1/{slow} 速度播放後擷取，影格時間已換算回實際毫秒；requestAnimationFrame 或計時器驅動的 JS 動畫不會被放慢")
        while (time.monotonic() - start) * 1000 / slow < args.duration:
            data = capture_region(page, args.region)
            stamp = (time.monotonic() - start) * 1000 / slow
            digest = hashlib.sha1(data).hexdigest()
            frames.append((stamp, data))
            if digest == last_hash:
                stable_since = stable_since if stable_since is not None else stamp
                if (stamp - stable_since) * slow >= args.settle:
                    break
            else:
                stable_since = None
            last_hash = digest
        running = page.evaluate("() => document.getAnimations().filter(a => a.playState === 'running').length")
        if running:
            limitations.append(f"擷取結束時仍有 {running} 個動畫在執行（可能是循環動畫，或超過 --duration）")
        hashes = [hashlib.sha1(item[1]).hexdigest() for item in frames]
        first_change = next((i for i, h in enumerate(hashes) if before is None or h != hashlib.sha1(before).hexdigest()), None)
        last_change = max((i for i in range(1, len(hashes)) if hashes[i] != hashes[i - 1]), default=first_change)
        if first_change is None:
            limitations.append("擷取期間畫面沒有變化：選擇器可能不對，或動畫由 JS 在擷取前就完成")
        chosen = []
        if before is not None:
            chosen.append(("before", 0.0, before))
        if first_change is not None:
            chosen.append(("first", *frames[first_change]))
            span = max(last_change - first_change, 0)
            for n in (1, 2, 3):
                index = first_change + round(span * n / 4)
                chosen.append((f"middle-{n}", *frames[index]))
            chosen.append(("last", *frames[last_change]))
        if frames:
            chosen.append(("settled", *frames[-1]))
        saved = []
        for label, stamp, data in chosen:
            path = folder / f"{len(saved):02d}-{label}.png"
            path.write_bytes(data)
            saved.append({"label": label, "ms": round(stamp), "file": str(path)})
        if saved:
            strip = "".join(f'<figure><img src="{Path(item["file"]).as_uri()}"><figcaption>{item["label"]} {item["ms"]}ms</figcaption></figure>' for item in saved)
            html = folder / "filmstrip.html"
            html.write_text(f'<!doctype html><meta charset="utf-8"><style>body{{margin:0;display:flex;flex-wrap:wrap;gap:8px;padding:8px;background:#fff;font:12px sans-serif;width:1000px}}figure{{margin:0;width:320px}}img{{width:100%;border:1px solid #ccc}}</style>{strip}', encoding="utf-8")
            view = browser.new_page(viewport={"width": 1016, "height": 600})
            view.goto(html.as_uri())
            view.screenshot(path=str(folder / "filmstrip.png"), full_page=True)
        context.close()
        browser.close()
    report = {"command": "motion", "target": args.target, "reduced_motion": args.reduced_motion, "region": args.region,
              "captured_frames": len(frames), "frames": saved, "limitations": limitations}
    (folder / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"out": str(folder), "report": str(folder / "report.json"), "frames": len(saved), "limitations": limitations}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="以 Chromium 實際渲染畫面，擷取截圖與檢查結果，或擷取動畫影格。")
    commands = parser.add_subparsers(dest="command", required=True)
    shot = commands.add_parser("shot", help="在多種寬度擷取截圖並檢查溢出、超出畫面、渲染後對比與 axe-core")
    shot.add_argument("target", help="本機 HTML 檔路徑或網址")
    shot.add_argument("--out", help="輸出資料夾；預設為系統暫存下的新資料夾")
    shot.add_argument("--widths", default=DEFAULT_WIDTHS, help=f"逗號分隔的寬度，預設 {DEFAULT_WIDTHS}")
    shot.add_argument("--states", help="逗號分隔的狀態值，以 ?state= 或 &state= 附加，例如 loading,empty,error")
    shot.add_argument("--color-scheme", default="light", help="逗號分隔的色彩模式：light、dark，預設 light")
    shot.add_argument("--viewport-only", action="store_true", help="只擷取第一個畫面，預設擷取完整頁面")
    shot.add_argument("--timeout", type=int, default=30000, help="開啟頁面的逾時毫秒數，預設 30000")
    motion = commands.add_parser("motion", help="擷取一段動畫的關鍵影格")
    motion.add_argument("target", help="本機 HTML 檔路徑或網址")
    motion.add_argument("--region", required=True, help="要擷取的區域選擇器，在步驟執行後才查找")
    trigger = motion.add_mutually_exclusive_group()
    trigger.add_argument("--click", help="觸發動畫要點擊的選擇器")
    trigger.add_argument("--steps", help="觸發動畫的步驟 JSON 檔；都不給時從頁面載入開始擷取")
    motion.add_argument("--setup", help="觸發前先執行並等待穩定的步驟 JSON 檔（例如擷取退場前先開啟對話框）")
    motion.add_argument("--reduced-motion", action="store_true", help="以 prefers-reduced-motion: reduce 擷取")
    motion.add_argument("--width", type=int, default=1024, help="視窗寬度，預設 1024")
    motion.add_argument("--duration", type=int, default=2000, help="最長擷取的動畫毫秒數（實際時間），預設 2000")
    motion.add_argument("--slowdown", type=int, default=10, help="動畫放慢的倍數，讓截圖跟得上，預設 10；1 表示不放慢")
    motion.add_argument("--settle", type=int, default=300, help="畫面連續不變多少毫秒視為結束，預設 300")
    motion.add_argument("--out", help="輸出資料夾；預設為系統暫存下的新資料夾")
    motion.add_argument("--timeout", type=int, default=30000, help="開啟頁面的逾時毫秒數，預設 30000")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    try:
        result = run_shot(args) if args.command == "shot" else run_motion(args)
    except ScriptError as error:
        log(f"錯誤：{error}")
        return error.code
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
