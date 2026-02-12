# Derek Staahl Website - Development Notes

## Overview
Personal portfolio website for Derek Staahl, Emmy-winning TV news anchor and reporter at Arizona's Family (3TV/CBS5) in Phoenix.

**Live Site:** https://derekstaahl.com
**Repository:** github.com/dstaahl-code/derekstaahl-site
**Hosting:** Netlify (auto-deploys from GitHub main branch)

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

---

## Related Files (Not in Repo)
- `/Users/derekstaahl/Documents/Gemini Photos/background-composition.html` - Original HTML composition tool used to design the logo mosaic layout
