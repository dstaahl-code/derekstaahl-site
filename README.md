# Derek Staahl - Personal Portfolio Website

A fast, SEO-optimized static portfolio site built with pure HTML5 and CSS3. Ready for deployment to Netlify with zero build steps.

## Quick Start

1. Clone or download this repository
2. Replace placeholder content with your information (see [Customization](#customization) below)
3. Add your images (see `images/README.md` for specifications)
4. Deploy to Netlify

## Project Structure

```
/
├── index.html          # Homepage
├── clips.html          # Published work/clips
├── about.html          # Bio and background
├── contact.html        # Contact form (Netlify Forms)
├── 404.html            # Custom error page
├── sitemap.xml         # For search engines
├── robots.txt          # Crawler instructions
├── css/
│   └── style.css       # All styles
├── js/
│   └── main.js         # Mobile nav + scroll animations
├── images/
│   ├── README.md       # Image optimization guide
│   └── originals/      # Store original images here
├── favicon.svg         # Modern favicon (DS initials)
└── README.md           # This file
```

## Customization

### Step 1: Update Personal Information

Search for and replace these placeholders across all HTML files:

| Placeholder | Replace With |
|-------------|--------------|
| `[YOUR TITLE]` | Your job title (e.g., "Investigative Journalist") |
| `[YOUR BEAT]` | Your coverage area (e.g., "politics and government") |
| `[CITY]` | Your location |
| `[YOUR_TWITTER_HANDLE]` | Your Twitter/X handle (without @) |
| `[YOUR_LINKEDIN]` | Your LinkedIn username |
| `[YOUR_EMAIL]` | Your email address |
| `[PUBLICATION NAME]` | Names of publications you've written for |
| `[LINK TO ARTICLE]` | URLs to your published work |
| `[HEADLINE...]` | Headlines of your articles |
| `[Write 2-3 sentences...]` | Your actual bio content |

### Step 2: Update Meta Information

In each HTML file's `<head>` section, update:

- `<title>` tag
- `<meta name="description">` content
- Open Graph and Twitter Card descriptions
- JSON-LD schema data (in `index.html`)

### Step 3: Add Your Images

See `images/README.md` for detailed instructions. Required images:

- `headshot.webp` and `headshot.jpg` (400x500px)
- `hero-bg.webp` and `hero-bg.jpg` (1920x1080px)
- `og-image.png` (1200x630px)
- `favicon.ico` (32x32px)
- `apple-touch-icon.png` (180x180px)

### Step 4: Add Your Clips

In `clips.html` and the featured clips section of `index.html`:

1. Replace placeholder headlines with your actual article titles
2. Add links to your published work
3. Update publication names and dates
4. Write brief descriptions of each piece

## Deployment to Netlify

### Method 1: GitHub + Netlify (Recommended)

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/dstaahl-code/derekstaahl-site.git
   git push -u origin main
   ```

2. **Connect to Netlify:**
   - Go to [netlify.com](https://netlify.com) and sign in
   - Click "Add new site" > "Import an existing project"
   - Choose "GitHub" and select your repository
   - Build settings: Leave blank (no build command needed)
   - Click "Deploy site"

### Method 2: Drag and Drop

1. Go to [app.netlify.com/drop](https://app.netlify.com/drop)
2. Drag your project folder onto the page
3. Wait for deployment to complete

### Set Up Custom Domain

1. In Netlify, go to Site settings > Domain management
2. Click "Add custom domain"
3. Enter `derekstaahl.com`
4. Follow Netlify's instructions to update your DNS settings
5. Enable HTTPS (automatic with Let's Encrypt)

### Enable Netlify Forms

Forms work automatically on Netlify. After deployment:

1. Go to Site settings > Forms
2. Verify the "contact" form appears
3. Submissions will appear in the Netlify dashboard
4. Optionally set up email notifications in Form settings

## SEO: Submit to Google

After deployment:

1. Go to [Google Search Console](https://search.google.com/search-console)
2. Add your property (domain or URL prefix)
3. Verify ownership using Netlify DNS or HTML file method
4. Submit your sitemap: `https://derekstaahl.com/sitemap.xml`

## Adding Analytics

The site includes a placeholder for Plausible Analytics. To enable:

1. Sign up at [plausible.io](https://plausible.io)
2. Add your domain
3. Uncomment the analytics script in each HTML file's `<head>`:

```html
<script defer data-domain="derekstaahl.com" src="https://plausible.io/js/script.js"></script>
```

Alternative: Use Netlify Analytics (paid feature) - no code changes needed.

## Testing Locally

Using Python:
```bash
cd /path/to/derekstaahl-site
python -m http.server 8000
# Open http://localhost:8000
```

Using Node.js:
```bash
npx serve
# Open the URL shown in terminal
```

## Pre-Launch Checklist

### Content
- [ ] All `[PLACEHOLDER]` text replaced with real content
- [ ] All clips have real headlines, links, and descriptions
- [ ] Bio paragraphs written
- [ ] Contact info updated (email, social links)
- [ ] Timeline/career highlights filled in

### Images
- [ ] Headshot added (webp + jpg, 400x500px)
- [ ] Hero background added (webp + jpg, 1920x1080px)
- [ ] Open Graph image created (og-image.png, 1200x630px)
- [ ] Favicons created (ico, svg, apple-touch-icon)
- [ ] All images optimized (see images/README.md)

### SEO
- [ ] Meta descriptions unique and compelling for each page
- [ ] JSON-LD schema updated in index.html
- [ ] Canonical URLs use production domain
- [ ] og:image and twitter:image URLs are absolute

### Technical
- [ ] Contact form tested on Netlify (receives submissions)
- [ ] 404 page displays correctly for invalid URLs
- [ ] Mobile navigation works
- [ ] All links work (no broken links)

### Performance
- [ ] Lighthouse score 90+ on Performance
- [ ] Lighthouse score 90+ on Accessibility
- [ ] Lighthouse score 90+ on Best Practices
- [ ] Lighthouse score 90+ on SEO

### Post-Launch
- [ ] Sitemap submitted to Google Search Console
- [ ] Analytics script uncommented
- [ ] Custom domain configured with HTTPS

## Updating Content

To add new clips:

1. Edit `clips.html` and add a new `<article class="clip-item">` element
2. Optionally add to featured clips in `index.html`
3. Update `sitemap.xml` with new `<lastmod>` date
4. Commit and push to GitHub (auto-deploys on Netlify)

## Browser Support

This site supports all modern browsers:
- Chrome, Firefox, Safari, Edge (latest 2 versions)
- Mobile browsers on iOS and Android
- Graceful degradation for older browsers (WebP fallback to JPEG)

## Credits

Built with:
- [Inter](https://fonts.google.com/specimen/Inter) and [Source Serif Pro](https://fonts.google.com/specimen/Source+Serif+Pro) fonts
- CSS custom properties for theming
- Intersection Observer API for scroll animations
- Netlify Forms for contact functionality

## License

This template is free to use for personal portfolio sites.
