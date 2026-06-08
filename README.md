# Discover Consent

A private, anonymous consent conversation tool for couples and groups.
Find your common ground — no accounts, no emails, no data stored.

**Live:** [discoverconsent.com](https://discoverconsent.com)

---

## How it works

1. Each person answers 46 questions privately across 6 topics
2. Answers are encoded into a short shareable URL — no server involved
3. Share links are combined on the results page
4. Only mutual yes/maybe answers are shown — no's are completely invisible

All computation happens in the browser. The server serves only a static HTML file and never sees any answer data. Hash fragments (`#/share/...`, `#/results/...`) are never transmitted to servers by browsers — this is a browser standard, not a promise.

---

## Privacy

- No accounts, emails, or cookies
- No analytics or tracking scripts
- No advertising
- Answers exist only in the URLs participants choose to share
- Open source — read the code, verify the claims

See [Privacy Policy](https://discoverconsent.com/#/privacy) for full details.

---

## Self-hosting

### Requirements
- Any static web server (Nginx, Apache, Caddy, etc.)
- The entire site is a single `index.html` file

### Nginx (recommended)

```bash
# Clone the repo
git clone https://github.com/discoverconsent/discoverconsent.git
cd discoverconsent

# Copy files to web root
sudo mkdir -p /var/www/discoverconsent
sudo cp index.html robots.txt sitemap.xml /var/www/discoverconsent/

# Copy the nginx config
sudo cp nginx.conf /etc/nginx/conf.d/discoverconsent.conf

# Edit the config with your domain
sudo nano /etc/nginx/conf.d/discoverconsent.conf

# Test and reload
sudo nginx -t && sudo systemctl reload nginx
```

### Cloudflare setup

1. Add your domain in Cloudflare
2. Point DNS to your server's IP (A record)
3. Enable Cloudflare proxy (orange cloud)
4. SSL/TLS mode: **Full** (your server handles HTTP, Cloudflare handles HTTPS)
5. Enable "Always Use HTTPS" in Cloudflare

### Any other static host

Upload `index.html`, `robots.txt`, and `sitemap.xml` to:
- GitHub Pages
- Netlify (drag and drop)
- Vercel
- Any S3-compatible storage with static hosting

No build step required.

---

## Questions

Questions are defined in the `SECTIONS` array inside `index.html`. Each section has a title, subtitle, and array of question strings. To modify, add, or remove questions:

```javascript
const SECTIONS = [
  {
    id: 'partners',
    title: "Who You're Open To",
    subtitle: 'Partner types and group configurations',
    questions: [
      'Soft swap (no penetrative sex with others)',
      // ... add or remove questions here
    ]
  },
  // ... more sections
];
```

**Note:** Changing questions changes the encoding format and breaks existing share links. Add new questions at the end of sections to preserve backwards compatibility, or increment a version number in the encoding if you make breaking changes.

---

## Contributing

Issues and pull requests welcome at [github.com/discoverconsent/discoverconsent](https://github.com/discoverconsent/discoverconsent).

Areas where contributions are especially welcome:
- Additional question suggestions (open an Issue)
- Translations / i18n
- Accessibility improvements
- Mobile UX refinements
- Question set versioning

---

## License

MIT — see [LICENSE](LICENSE)
