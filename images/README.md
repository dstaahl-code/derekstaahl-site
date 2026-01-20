# Image Optimization Instructions

Before deploying your site, you'll need to add and optimize your images. Follow these guidelines to ensure fast loading times and good visual quality.

## Required Images

| File | Dimensions | Format | Use |
|------|------------|--------|-----|
| `headshot.webp` | 400x500 px | WebP | Your headshot in bio sections |
| `headshot.jpg` | 400x500 px | JPEG | Fallback for older browsers |
| `hero-bg.webp` | 1920x1080 px | WebP | Hero section background |
| `hero-bg.jpg` | 1920x1080 px | JPEG | Fallback for older browsers |
| `og-image.png` | 1200x630 px | PNG | Social media sharing preview |
| `favicon.ico` | 32x32 px | ICO | Browser tab icon (legacy) |
| `favicon.svg` | Scalable | SVG | Modern browser favicon |
| `apple-touch-icon.png` | 180x180 px | PNG | iOS home screen icon |

## Optional Images (for video clips)

| File | Dimensions | Format | Use |
|------|------------|--------|-----|
| `video-thumbnail-placeholder.jpg` | 400x225 px (16:9) | JPEG | Placeholder for video thumbnails |

## Optimization Guidelines

### For Photos (headshot, hero background)

1. **Resize appropriately:**
   - Content images: max 800px width
   - Hero/background images: max 1920px width
   - Headshot: 400x500px (or similar portrait ratio)

2. **Convert to WebP:**
   - Use 80-85% quality setting
   - Keep file size under 200KB for photos
   - Keep file size under 500KB for hero images

3. **Always create JPEG fallbacks:**
   - Same dimensions as WebP version
   - 85% quality setting

### For Social Sharing Image (og-image.png)

- Must be exactly 1200x630 pixels
- Keep as PNG (not WebP) for better social platform compatibility
- Include your name and a brief tagline
- Use readable fonts and good contrast
- File size can be up to 1MB

### For Favicons

- `favicon.ico`: 32x32px, can include multiple sizes (16x16, 32x32)
- `favicon.svg`: Use the provided SVG with your initials
- `apple-touch-icon.png`: 180x180px, no transparency, solid background

## Free Optimization Tools

1. **Squoosh.app** (recommended)
   - Browser-based, no installation needed
   - Supports WebP conversion
   - Real-time quality preview
   - URL: https://squoosh.app

2. **TinyPNG / TinyJPG**
   - Browser-based compression
   - Also handles WebP
   - URL: https://tinypng.com

3. **ImageOptim** (Mac only)
   - Desktop app for batch optimization
   - URL: https://imageoptim.com

4. **SVGOMG** (for SVG optimization)
   - URL: https://jakearchibald.github.io/svgomg/

## How to Add Images

1. Place your original, unoptimized images in the `/images/originals/` folder (for backup)

2. Optimize the images using the tools above

3. Place optimized images in the `/images/` folder with the correct filenames

4. Test locally to ensure images load correctly:
   ```bash
   # If you have Python installed:
   python -m http.server 8000

   # Or with Node.js:
   npx serve
   ```

5. Open `http://localhost:8000` and verify images display properly

## HTML Usage Examples

The site uses `<picture>` elements for WebP with JPEG fallback:

```html
<picture>
  <source srcset="/images/headshot.webp" type="image/webp">
  <img src="/images/headshot.jpg" alt="Derek Staahl headshot" loading="lazy" width="400" height="500">
</picture>
```

Always include:
- `loading="lazy"` for images below the fold
- `width` and `height` attributes to prevent layout shift
- Descriptive `alt` text for accessibility

## Checklist

- [ ] Headshot (webp + jpg fallback)
- [ ] Hero background (webp + jpg fallback)
- [ ] Open Graph image (og-image.png)
- [ ] Favicon files (ico, svg, apple-touch-icon)
- [ ] Video thumbnails (if applicable)
- [ ] All images under recommended file sizes
- [ ] All images have appropriate alt text in HTML
