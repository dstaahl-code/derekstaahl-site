# Derek Staahl Website - Development Notes

## Overview
Personal portfolio website for Derek Staahl, Emmy-winning TV news anchor and reporter at Arizona's Family (3TV/CBS5) in Phoenix.

**Live Site:** https://derekstaahl.com
**Repository:** github.com/dstaahl-code/derekstaahl-site
**Hosting:** Netlify (CLI deploys via `npm run deploy`; GitHub auto-deploys disabled to save build minutes)

---

## Work Completed: January 23, 2026

### Animated Logo Background (Hero & Page Headers)

Added a twinkling mosaic of TV station logos as a subtle background effect behind the hero section and page headers.

#### Logo Files
Located in `/images/logos/`:
- `arizonas-family.png` - Arizona's Family (current employer, primary logo)
- `27News.png` - ABC 27 Madison
- `3tv-azfamily.jpg` - 3TV
- `abc10news.jpg` - ABC 10 San Diego
- `CW-Logo-2015-update.webp` - CW Network
- `KPHO_CBS_5.webp` - CBS 5 Phoenix

#### Implementation Details

**CSS (`css/style.css`):**
- `.hero__background-logos` - Container for logo elements
- `.hero-logo` - Individual logo styling with dark silhouette filter
- `.hero-logo.azfamily-logo` - Special styling for Arizona's Family logo (needs higher brightness due to orange background)
- `.hero-logo.twinkle` - Brightened state for twinkle animation
- Responsive breakpoints at 1200px, 768px, and 480px

**JavaScript (`js/main.js`):**
- `generateLogos()` function creates logo elements dynamically
- Logos positioned using percentage-based layout (spreads across full width)
- 15 rows for hero section, 5 rows for page headers
- Twinkle animation cycles through all 6 logo types
- Only logos in center area (25%-75% horizontal, 10%-70% vertical) eligible for twinkle on hero
- Respects `prefers-reduced-motion` accessibility setting

**HTML Changes:**
- `index.html` - Added `<div class="hero__background-logos" id="hero-logos">` inside hero
- `about.html` - Added `page-header__background` with logo container
- `contact.html` - Added `page-header__background` with logo container

#### Mobile Responsiveness
- Logos scale down on smaller screens (35px → 28px → 28px)
- 25% of logos hidden on mobile (`nth-child(4n)`) to prevent overlap
- Opacity reduced on mobile for subtler effect

### Footer Social Links Fix
- Tightened spacing between social media links on mobile
- Added flex-wrap for graceful wrapping
- Reduced font size slightly to prevent text cutoff

---

## Work Completed: February 12, 2026

### Auto-Updating Episode System for Generation AI

Built an automated pipeline that fetches new Generation AI episodes weekly and updates the site without manual intervention.

#### How It Works
1. **cron-job.org** triggers the GitHub Actions workflow every Wednesday at 10:06 PM MST
2. **Python script** fetches the Generation AI YouTube playlist RSS feed
3. **Scrapes azfamily.com** (best-effort) to find the matching article link
4. **Writes new episodes** to `data/episodes.json`
5. **Commits and pushes** to `main`, then **deploys to Netlify** via CLI (`npx netlify-cli deploy --prod`)
6. **Client-side JS** fetches `episodes.json` and renders episode cards dynamically
7. **Episode 1 stays hardcoded** in HTML as an SEO/no-JS fallback

#### Files Created
- `.github/workflows/update-genai-episodes.yml` - `workflow_dispatch` only (triggered by cron-job.org)
- `scripts/update_episodes.py` - Python script (stdlib only, no pip) that fetches YouTube RSS + scrapes AZFamily
- `data/episodes.json` - Episode data file, seeded with Episode 1

#### Files Modified
- `generation-ai.html` - Added `<div id="genai-dynamic-episodes">` container; added `data-episode-id` attribute to existing episode for deduplication
- `js/main.js` - Added episode rendering from JSON (fetches `/data/episodes.json`, renders cards newest-first, hides hardcoded duplicates, XSS-safe escaping, silent failure)
- `css/style.css` - Added `.genai-episode + .genai-episode` spacing rule

#### Key Technical Details
- **YouTube playlist ID:** `PLJQ20huef_NwQoBRT-QSNP3vl9hoV4OWy` (dedicated Generation AI playlist)
- **RSS URL:** `https://www.youtube.com/feeds/videos.xml?playlist_id=PLJQ20huef_NwQoBRT-QSNP3vl9hoV4OWy`
- **Episode filtering:** Regex `generation\s+ai` (case-insensitive) on video titles (safety check; playlist is already curated)
- **Deduplication:** By `youtubeId` in JSON and `data-episode-id` attribute in DOM
- **Retry logic:** `fetch_url` retries 3 times with exponential backoff (2s, 4s); exits gracefully if feed unreachable
- **No API keys needed for episode fetch** - YouTube RSS is free/public, GitHub Actions uses built-in `GITHUB_TOKEN`
- **Netlify deploy from workflow** uses `NETLIFY_AUTH_TOKEN` and `NETLIFY_SITE_ID` (stored as GitHub Actions secrets)
- **Scheduling:** cron-job.org POSTs to GitHub workflow dispatch API (requires GitHub PAT with `workflow` scope)

#### Derek's Weekly Workflow
1. **Automatic:** New episode appears on site Wednesday night with video, title, date, description
2. **Optional manual polish:** Edit `data/episodes.json` on GitHub to add `guest` name and tweak `description` (then pull locally and `npm run deploy`)
3. **Manual trigger:** Can run workflow anytime from GitHub Actions tab if episode drops at non-standard time

#### AZFamily Article Scraping
- Scrapes `https://www.azfamily.com/news/technology/` for links matching Generation AI keywords
- Best-effort: if scraping fails, `azfamilyUrl` is left empty and the "Watch on AZFamily" link won't render
- Derek can add the URL manually in the JSON edit

### Site-Wide Navigation Update
- Added "Generation AI" nav link to all pages: `index.html`, `about.html`, `clips.html`, `contact.html`

### Repository Cleanup
- Hardened `.gitignore` with patterns for `.env`, credentials, and secrets
- Removed planning spec files from repo (kept local only for Claude Code access):
  - `generation-ai-booking-system-spec.md`
  - `generation-ai-free-plan-spec.md`

---

## Technical Notes

### CSS Custom Properties Used
- `--color-primary: #0f172a` (navy blue background)
- `--color-accent` (orange accent color)
- `--space-sm`, `--space-lg`, etc. (spacing scale)

### Logo Styling Approach
```css
.hero-logo {
  filter: brightness(0.22) saturate(0) contrast(0.9);
  opacity: 0.45;
  border-radius: 22%; /* Apple app-style rounded corners */
}
```

The Arizona's Family logo requires special handling because its orange background becomes nearly invisible when desaturated against the navy background:
```css
.hero-logo.azfamily-logo {
  filter: brightness(0.25) saturate(0) contrast(1.2);
}
```

### Twinkle Animation
- Duration: 1600ms
- Interval: 2500ms between twinkles
- Cycles through each logo type in order
- CSS transition handles smooth fade in/out

---

## Git Commits (January 23, 2026)
1. `8b065e4` - Add animated TV station logo background to hero section
2. `b633a8c` - Add animated logo background to About and Contact page headers
3. `5f3e7ee` - Add responsive scaling for logo background on mobile
4. `670d085` - Fix mobile logo overlap with !important overrides
5. `8f9b1d0` - Adjust mobile logo density - show 60% instead of 25%
6. `65be551` - Increase mobile logo size to 28px and show 75% density
7. `6ead0b0` - Tighten footer social links spacing on mobile

## Git Commits (February 12, 2026)
1. `8b6ad51` - Add auto-updating episode system for Generation AI page
2. `801b997` - Add Generation AI nav link site-wide and project docs
3. `a41e9d3` - Remove planning specs from repo, keep local only

## Session Log: February 19, 2026

### 1. Switched YouTube feed from channel to playlist RSS
The channel RSS feed (`channel_id=UCIrgpHvUm1FMtv-C1xwkJtw`) was returning 404 errors from GitHub Actions (worked locally but YouTube blocks data center IPs). Switched to a dedicated Generation AI playlist feed (`playlist_id=PLJQ20huef_NwQoBRT-QSNP3vl9hoV4OWy`) which is more targeted and reliable.

**Modified:** `scripts/update_episodes.py`

### 2. Added retry logic to fetch_url
`fetch_url()` now retries 3 times with exponential backoff (2s, 4s delays). If the YouTube feed is still unreachable after retries, the script exits gracefully (exit 0) instead of crashing the workflow.

**Modified:** `scripts/update_episodes.py`

### 3. Migrated scheduling from GitHub cron to cron-job.org
Removed `schedule:` trigger from the workflow (GitHub's cron runner had unreliable timing). Workflow is now `workflow_dispatch` only. Set up cron-job.org to POST to the GitHub workflow dispatch API every Wednesday at 10:06 PM MST.

**cron-job.org config:**
- URL: `https://api.github.com/repos/dstaahl-code/derekstaahl-site/actions/workflows/update-genai-episodes.yml/dispatches`
- Method: POST, Body: `{"ref":"main"}`
- Headers: `Authorization: Bearer {github_pat}`, `Content-Type: application/json`
- Schedule: Wednesdays at 22:06 America/Phoenix

**Modified:** `.github/workflows/update-genai-episodes.yml`

**Commit:** `187b149`

## Session Log: February 19, 2026 (Part 2)

### 4. Switched from Netlify auto-deploys to CLI deploys
Disabled Netlify's GitHub auto-deploy integration to save build minutes. Site is now deployed from the command line.

- **Local deploy:** `npm run deploy` (runs `npx netlify deploy --prod --dir=.`)
- **Workflow deploy:** Added `Deploy to Netlify` step to `update-genai-episodes.yml` using `npx netlify-cli deploy --prod --dir=.`
- **Netlify linked:** `.netlify/state.json` created via `netlify link` (gitignored)
- **Site ID:** `f69d1d53-11d4-4cba-8d2b-7c982d2a52c9`

**GitHub Actions secrets required:**
- `NETLIFY_AUTH_TOKEN` - Personal access token from Netlify (app.netlify.com/user/applications)
- `NETLIFY_SITE_ID` - `f69d1d53-11d4-4cba-8d2b-7c982d2a52c9`

**Files created:** `package.json`
**Files modified:** `.github/workflows/update-genai-episodes.yml`, `.gitignore`

### 5. Updated copyright to 2026
Footer copyright changed from 2025 to 2026 across all six pages: `index.html`, `generation-ai.html`, `about.html`, `contact.html`, `clips.html`, `404.html`.

**Commit:** `057559a`

---

## Related Files (Not in Repo)
- `/Users/derekstaahl/Documents/Gemini Photos/background-composition.html` - Original HTML composition tool used to design the logo mosaic layout
- `generation-ai-booking-system-spec.md` - Guest booking system spec (Airtable, Cal.com, Make.com pipeline)
- `generation-ai-free-plan-spec.md` - Booking automation consolidated for Make.com free tier
