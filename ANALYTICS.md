# Website visitor analytics

## Recommended: Vercel Web Analytics (already in index.html)

The site includes the Vercel Analytics script. To see visitor counts:

1. Open [vercel.com](https://vercel.com) ? your project `public-reports-one`
2. Go to **Analytics** tab (or **Settings ? Analytics**)
3. Enable **Web Analytics** (free tier includes basic page views)
4. Push the latest `public/index.html` to GitHub and wait for deploy
5. After 24h you will see **visitors**, **page views**, and top pages in the Vercel dashboard

No extra code needed after enabling in Vercel.

---

## Alternatives (optional)

| Service | Pros | Setup |
|---------|------|--------|
| **Cloudflare Web Analytics** | Free, privacy-friendly | Add their `<script>` tag to `index.html` |
| **Google Analytics 4** | Detailed, familiar | Create GA4 property, paste measurement ID |
| **Plausible / Umami** | Clean UI, privacy | Paid or self-hosted |

---

## What you can track

- **Page views** — how many times the homepage loaded
- **Unique visitors** — approximate distinct users (Vercel / GA)
- **PDF clicks** — need event tracking (e.g. `va('event', { name: 'pdf_click', ticker: 'NVDA' })`) or link URLs in analytics

For a portfolio site, **Vercel Web Analytics page views** is usually enough.
