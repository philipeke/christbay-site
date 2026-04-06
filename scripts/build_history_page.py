"""Build history/index.html from store-copy-v2.md (run from repo: python scripts/build_history_page.py)."""
import html as html_mod
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MD_PATH = ROOT / "store-copy-v2.md"


def parse_md_sections(text):
    lines = text.splitlines()
    sections = []
    current = None
    buf = []
    for line in lines:
        if line.startswith("## "):
            if current is not None:
                sections.append((current, buf))
            current = line[3:].strip()
            buf = []
        elif current is not None:
            buf.append(line)
    if current is not None:
        sections.append((current, buf))
    return sections


def paragraphs(block):
    out = []
    cur = []
    for line in block:
        s = line.strip()
        if not s:
            if cur:
                out.append(" ".join(cur))
                cur = []
        else:
            cur.append(s)
    if cur:
        out.append(" ".join(cur))
    return out


def slug(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def build_body_fragment():
    md = MD_PATH.read_text(encoding="utf-8")
    chunks = []
    for title, block in parse_md_sections(md):
        pid = slug(title)
        ps = paragraphs(block)
        if title == "Promotional Text":
            chunks.append(f'<section class="story-promo" id="{pid}" aria-labelledby="{pid}-heading">')
            chunks.append('  <div class="container story-narrow">')
            chunks.append(f'    <p class="story-section-label" id="{pid}-heading">Promotional</p>')
            chunks.append('    <blockquote class="story-lede">')
            for p in ps:
                chunks.append(f"      <p>{html_mod.escape(p)}</p>")
            chunks.append("    </blockquote>")
            chunks.append("  </div>")
            chunks.append("</section>")
            continue

        tone = "story-section--paper" if title == "Store Description" else "story-section--warm"
        chunks.append(
            f'<section class="story-section {tone}" id="{pid}" aria-labelledby="{pid}-h2">'
        )
        chunks.append('  <div class="container story-narrow">')
        label = "Version 2.0" if "2.0" in title else "Story"
        chunks.append(f'    <p class="story-section-label">{label}</p>')
        chunks.append(f'    <h2 class="story-h2" id="{pid}-h2">{html_mod.escape(title)}</h2>')
        chunks.append('    <div class="story-divider" aria-hidden="true"></div>')
        for p in ps:
            chunks.append(f'    <p class="story-p">{html_mod.escape(p)}</p>')
        chunks.append("  </div>")
        chunks.append("</section>")
    return "\n".join(chunks)

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="description" content="The story of ChristBay — from fifteen reflection doors to a full daily Christian companion. Store description and what is new in version 2.0." />
  <meta name="robots" content="index, follow" />
  <title>Our Story &amp; History — ChristBay</title>
  <link rel="icon" type="image/png" href="/assets/brand.png" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="/assets/css/site-nav.css" />
  <style>
    :root {
      --navy:           #1a2744;
      --navy-light:     #243355;
      --navy-deep:      #121d35;
      --navy-darker:    #0d1526;
      --gold:           #c9a84c;
      --gold-light:     #dfc980;
      --gold-subtle:    #f5edcc;
      --warm-white:     #f9f7f4;
      --cream:          #f0ece4;
      --white:          #ffffff;
      --text-primary:   #1a2744;
      --text-secondary: #4a5a7a;
      --text-muted:     #7a8ba5;
      --border:         #e0dbd0;
      --shadow-md:      0 4px 16px rgba(26,39,68,.10);
      --radius:         12px;
      --radius-sm:      8px;
      --radius-lg:      20px;
      --transition:     0.25s ease;
      --max-width:      1100px;
      --read-width:     42rem;
    }
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
    html{{scroll-behavior:smooth;font-size:16px}}
    body{{font-family:'Inter',system-ui,-apple-system,BlinkMacSystemFont,sans-serif;background:var(--warm-white);color:var(--text-primary);line-height:1.6;-webkit-font-smoothing:antialiased;overflow-x:hidden}}
    a{{color:inherit;text-decoration:none}}
    ul{{list-style:none}}

    .skip-link{{position:absolute;top:-120px;left:1rem;background:var(--navy);color:var(--white);padding:.5rem 1rem;border-radius:var(--radius-sm);font-size:.875rem;font-weight:600;z-index:9999;transition:top var(--transition)}}
    .skip-link:focus{{top:1rem}}

    .container{{width:100%;max-width:var(--max-width);margin:0 auto;padding:0 1.5rem}}
    .story-narrow{{max-width:var(--read-width);margin:0 auto}}

    .page-hero{{background:linear-gradient(160deg,var(--navy-darker) 0%,var(--navy-deep) 35%,var(--navy) 70%,var(--navy-light) 100%);color:var(--white);text-align:center;padding:5.5rem 1.5rem 5rem;position:relative;overflow:hidden}}
    .page-hero::before{{content:'';position:absolute;inset:0;background:radial-gradient(ellipse 70% 55% at 20% 30%,rgba(201,168,76,.09) 0%,transparent 55%),radial-gradient(ellipse 55% 65% at 85% 70%,rgba(201,168,76,.06) 0%,transparent 55%);pointer-events:none}}
    .page-hero-inner{{position:relative;z-index:1;max-width:36rem;margin:0 auto}}
    .page-hero-label{{display:inline-block;font-size:.6875rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--gold-light);margin-bottom:1rem}}
    .page-hero h1{{font-size:clamp(2rem,4.5vw,3.25rem);font-weight:800;letter-spacing:-.035em;line-height:1.12;margin-bottom:1.125rem}}
    .page-hero h1 em{{font-style:normal;color:var(--gold-light)}}
    .page-hero-lead{{font-size:1.0625rem;color:rgba(255,255,255,.74);line-height:1.75;max-width:32rem;margin:0 auto 2rem}}
    .hero-wave{{display:block;width:100%;height:clamp(40px,6vw,56px);margin-bottom:-1px;color:var(--cream)}}

    .story-layout{{display:grid;grid-template-columns:minmax(0,220px) minmax(0,1fr);gap:3rem 3.5rem;align-items:start;padding:3.5rem 0 5.5rem}}
    @media(max-width:900px){{.story-layout{{grid-template-columns:1fr;gap:2rem;padding:2.5rem 0 4.5rem}}}}

    .story-toc{{position:sticky;top:84px}}
    @media(max-width:900px){{.story-toc{{position:static;background:var(--white);border:1px solid var(--border);border-radius:var(--radius);padding:1.375rem 1.25rem;box-shadow:var(--shadow-md)}}}}
    .story-toc-title{{font-size:.6875rem;font-weight:700;letter-spacing:.11em;text-transform:uppercase;color:var(--text-muted);margin-bottom:.875rem}}
    .story-toc a{{display:block;font-size:.8125rem;font-weight:500;color:var(--text-secondary);padding:.4rem .5rem;border-radius:var(--radius-sm);border-left:2px solid transparent;transition:color var(--transition),border-color var(--transition),background var(--transition);line-height:1.45}}
    .story-toc a:hover{{color:var(--navy);border-left-color:var(--gold);background:rgba(201,168,76,.08)}}

    .story-promo{{background:linear-gradient(180deg,var(--cream) 0%,var(--warm-white) 100%);padding:3.5rem 0 4rem;border-bottom:1px solid var(--border);scroll-margin-top:88px}}
    .story-section{{padding:4rem 0;scroll-margin-top:88px}}
    .story-section--paper{{background:var(--white)}}
    .story-section--warm{{background:var(--warm-white)}}

    .story-section-label{{font-size:.6875rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--gold);margin-bottom:.625rem}}
    .story-h2{{font-size:clamp(1.5rem,2.8vw,2rem);font-weight:800;letter-spacing:-.03em;color:var(--navy);line-height:1.2;margin-bottom:1rem}}
    .story-divider{{width:48px;height:3px;background:linear-gradient(90deg,var(--gold),var(--gold-light));border-radius:2px;margin-bottom:1.75rem}}

    .story-lede{{margin:0;padding:1.75rem 1.5rem 1.75rem 1.75rem;border-left:4px solid var(--gold);background:var(--white);border-radius:0 var(--radius-lg) var(--radius-lg) 0;box-shadow:var(--shadow-md)}}
    .story-lede p{{font-family:Georgia,'Times New Roman',serif;font-size:clamp(1.125rem,2.2vw,1.35rem);font-style:italic;color:var(--text-primary);line-height:1.65;margin:0}}

    .story-p{{font-size:1.015rem;color:var(--text-secondary);line-height:1.82;margin-bottom:1.125rem}}
    .story-p:last-child{{margin-bottom:0}}

    .story-cta{{padding:4rem 0 5rem;background:linear-gradient(135deg,var(--navy-deep),var(--navy));text-align:center}}
    .story-cta-inner{{max-width:32rem;margin:0 auto;padding:0 1.5rem}}
    .story-cta h2{{font-size:clamp(1.35rem,2.5vw,1.75rem);font-weight:700;color:var(--white);margin-bottom:.75rem;letter-spacing:-.02em}}
    .story-cta p{{font-size:.9375rem;color:rgba(255,255,255,.65);line-height:1.7;margin-bottom:1.5rem}}
    .story-cta-btns{{display:flex;flex-wrap:wrap;gap:.75rem;justify-content:center}}
    .story-cta a{{display:inline-flex;align-items:center;gap:.5rem;background:var(--gold);color:var(--navy-deep);padding:.75rem 1.5rem;border-radius:100px;font-size:.9375rem;font-weight:600;transition:transform var(--transition),box-shadow var(--transition),background var(--transition)}}
    .story-cta a:hover{{background:var(--gold-light);transform:translateY(-2px);box-shadow:0 8px 24px rgba(201,168,76,.3)}}
    .story-cta a.secondary{{background:rgba(255,255,255,.12);color:var(--white);border:1px solid rgba(255,255,255,.35)}}
    .story-cta a.secondary:hover{{background:rgba(255,255,255,.2);box-shadow:none}}

    .site-footer{{background:#0b1220;color:rgba(255,255,255,.5);padding:4.5rem 1.5rem 2.5rem}}
    .footer-inner{{max-width:var(--max-width);margin:0 auto}}
    .footer-top{{display:flex;align-items:flex-start;justify-content:space-between;padding-bottom:2.5rem;border-bottom:1px solid rgba(255,255,255,.07);gap:2rem;flex-wrap:wrap}}
    .footer-brand{{display:flex;align-items:center;gap:.625rem}}
    .footer-brand img{{width:36px;height:36px;object-fit:cover;border-radius:50%;border:1px solid rgba(255,255,255,.95);box-shadow:0 0 0 1px rgba(0,0,0,.18)}}
    .footer-brand-name{{font-size:1rem;font-weight:700;color:var(--white)}}
    .footer-nav{{display:flex;gap:.5rem 2.25rem;flex-wrap:wrap;align-items:center}}
    .footer-nav a{{font-size:.875rem;color:rgba(255,255,255,.45);transition:color var(--transition)}}
    .footer-nav a:hover{{color:var(--white)}}
    .footer-bottom{{padding-top:2rem;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.75rem}}
    .footer-copyright{{font-size:.8125rem;color:rgba(255,255,255,.3)}}
    .footer-tagline{{font-size:.8125rem;color:rgba(255,255,255,.2);font-style:italic}}

    @media(prefers-reduced-motion:reduce){{*,*::before,*::after{{animation:none!important;transition:none!important}}}}
  </style>
</head>
<body>

<a href="#main" class="skip-link">Skip to main content</a>

<header class="site-header" role="banner">
  <nav class="nav-inner" aria-label="Primary navigation">
    <a href="/" class="nav-brand" aria-label="ChristBay — home">
      <img src="/assets/brand.png" alt="" aria-hidden="true" />
      <span class="nav-brand-name">ChristBay</span>
    </a>
    <div class="nav-links">
      <a href="/#features" class="nav-text">Features</a>
      <a href="/#premium" class="nav-text">Premium</a>
      <a href="/history/" class="nav-text" aria-current="page">Our Story</a>
      <a href="/support/" class="nav-text">Support</a>
      <div class="nav-dropdown">
        <button type="button" class="nav-cta" id="download-toggle" aria-expanded="false" aria-haspopup="true" aria-label="Download options">Download</button>
        <div class="nav-dropdown-menu" id="download-menu">
          <a href="https://apps.apple.com/se/app/christbay-daglig-reflektion/id6759575925" class="nav-dropdown-item" aria-label="Download on Apple App Store">
            <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false" xmlns="http://www.w3.org/2000/svg"><path fill="currentColor" d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/></svg>
            App Store
          </a>
          <a href="https://play.google.com/store/apps/details?id=com.oakdev.christbay" class="nav-dropdown-item" aria-label="Download on Google Play Store">
            <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false" xmlns="http://www.w3.org/2000/svg"><path fill="currentColor" d="M3.609 1.814L13.792 12 3.609 22.186c-.386.387-.593.916-.593 1.465V1.349c0 .549.207 1.078.593 1.465zm10.908 10.911L21.268 24 3.609 1.814 14.517 12.722z"/></svg>
            Google Play
          </a>
        </div>
      </div>
    </div>
  </nav>
</header>

<main id="main">
  <header class="page-hero" aria-labelledby="page-title">
    <div class="page-hero-inner">
      <p class="page-hero-label">ChristBay</p>
      <h1 id="page-title">Our <em>story</em> &amp; history</h1>
      <p class="page-hero-lead">From the first fifteen reflection doors to the fuller companion in version 2.0 — the same calm, Scripture-rooted heart, told in the words we share with the store and our community.</p>
    </div>
  </header>
  <svg class="hero-wave" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 48" preserveAspectRatio="none" aria-hidden="true" focusable="false">
    <path fill="currentColor" d="M0 24 C 240 6 480 42 720 24 C 960 6 1200 42 1440 24 L 1440 48 L 0 48 Z" />
  </svg>

  <div class="container story-layout">
    <nav class="story-toc" aria-label="On this page">
      <p class="story-toc-title">On this page</p>
      <a href="#promotional-text">Promotional</a>
      <a href="#store-description">Store description</a>
      <a href="#what-s-new-in-version-2-0">What&rsquo;s new in 2.0</a>
    </nav>
    <div class="story-article">
{FRAGMENT}
    </div>
  </div>

  <section class="story-cta" aria-label="Download ChristBay">
    <div class="story-cta-inner">
      <h2>Walk with ChristBay today</h2>
      <p>Download the app for iOS or Android and begin — or return to — a steadier rhythm of prayer, Scripture, and reflection.</p>
      <div class="story-cta-btns">
        <a href="https://apps.apple.com/se/app/christbay-daglig-reflektion/id6759575925">App Store</a>
        <a href="https://play.google.com/store/apps/details?id=com.oakdev.christbay" class="secondary">Google Play</a>
      </div>
    </div>
  </section>
</main>

<footer class="site-footer" role="contentinfo">
  <div class="footer-inner">
    <div class="footer-top">
      <div class="footer-brand">
        <img src="/assets/brand.png" alt="ChristBay" />
        <span class="footer-brand-name">ChristBay</span>
      </div>
      <nav class="footer-nav" aria-label="Footer links">
        <a href="/privacy/">Privacy Policy</a>
        <a href="/terms/">Terms of Use</a>
        <a href="/support/">Support</a>
        <a href="/history/" aria-current="page">Our Story</a>
        <a href="/join/">Join with code</a>
        <a href="/delete-account/">Delete Account</a>
      </nav>
    </div>
    <div class="footer-bottom">
      <p class="footer-copyright">&copy; 2026 OakDev &amp; AI AB. All rights reserved.</p>
      <p class="footer-tagline">Walk in the Word. Grow in grace.</p>
    </div>
  </div>
</footer>

<script>
(function () {{
  var downloadToggle = document.getElementById('download-toggle');
  var downloadMenu = document.getElementById('download-menu');
  if (downloadToggle && downloadMenu) {{
    downloadToggle.addEventListener('click', function (e) {{
      e.preventDefault();
      var isOpen = downloadMenu.classList.contains('open');
      downloadMenu.classList.toggle('open');
      downloadToggle.setAttribute('aria-expanded', !isOpen);
    }});
    document.addEventListener('click', function (e) {{
      if (!downloadToggle.contains(e.target) && !downloadMenu.contains(e.target)) {{
        downloadMenu.classList.remove('open');
        downloadToggle.setAttribute('aria-expanded', 'false');
      }}
    }});
    document.addEventListener('keydown', function (e) {{
      if (e.key === 'Escape') {{
        downloadMenu.classList.remove('open');
        downloadToggle.setAttribute('aria-expanded', 'false');
      }}
    }});
    downloadMenu.querySelectorAll('a').forEach(function (link) {{
      link.addEventListener('click', function () {{
        downloadMenu.classList.remove('open');
        downloadToggle.setAttribute('aria-expanded', 'false');
      }});
    }});
  }}
}})();
</script>
</body>
</html>
"""

frag = build_body_fragment()
out = TEMPLATE.replace(
    "{FRAGMENT}", "\n".join("      " + line if line else "" for line in frag.splitlines())
)
(ROOT / "history" / "index.html").write_text(out, encoding="utf-8")
print("Wrote history/index.html from", MD_PATH.name)
