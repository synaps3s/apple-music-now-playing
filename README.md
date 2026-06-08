# apple-music-now-playing

A GitHub profile badge that shows the track you are listening to on Apple Music, with animated background colors extracted from the album artwork.

The badge updates automatically as you switch tracks. Colors change per album. Bars animate while playing, go static when paused.

---

## How it works

A [Tampermonkey](https://www.tampermonkey.net/) userscript running on `music.apple.com` reads the current track from the player bar DOM and sends it to a small Python server running locally. The server generates an SVG badge with three slow-moving blurred blobs colored from the album art, plus an animated equalizer. A [Cloudflare quick tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) exposes the server at a public URL that GitHub can fetch.

---

## Prerequisites

- Python 3.10 or newer
- [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) installed and on your PATH
- [Tampermonkey](https://www.tampermonkey.net/) browser extension

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/yourusername/apple-music-now-playing
cd apple-music-now-playing
pip install -r requirements.txt
```

### 2. Create a GitHub fine-grained token

Go to **GitHub -> Settings -> Developer settings -> Personal access tokens -> Fine-grained tokens** and create a token with:

- Repository access: only your profile repo (`yourusername/yourusername`)
- Permissions: **Contents** -> Read and Write

### 3. Configure

```bash
cp .env.example .env
```

Open `.env` and fill in the values:

```
GITHUB_TOKEN=github_pat_...
GITHUB_REPO=yourusername/yourusername
API_SECRET=<output of: openssl rand -hex 24>
```

### 4. Add the badge placeholder to your profile README

Open your profile README on GitHub and add this line wherever you want the badge to appear:

```markdown
![Now Playing](https://placeholder.trycloudflare.com/now-playing.svg)
```

The URL is replaced automatically on every startup, so the placeholder URL does not matter.

### 5. Start the server

```bash
python start.py
```

On first run, the README is updated with the live tunnel URL.

#### Optional: run as a systemd user service (Linux)

The service starts automatically at login and restarts on failure -- no terminal needed.

```bash
cp music-widget.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now music-widget.service
```

Useful commands:

```bash
systemctl --user status music-widget.service
systemctl --user restart music-widget.service
journalctl --user -u music-widget.service -f
```

### 6. Install the Tampermonkey script

1. Open Tampermonkey -> Dashboard -> click the **+** icon to create a new script
2. Delete the default template content
3. Paste the contents of `tampermonkey.js`
4. Set `SECRET` to the same value you put in `.env` for `API_SECRET`
5. Save with Ctrl+S

Open `music.apple.com`, play a track, and the badge updates within 10 seconds. The Tampermonkey icon on `music.apple.com` should show a number badge -- if it shows "No access needed" instead, the script is not active on that page. Open the Dashboard and verify the script is enabled.

---

## Customization

All visual options are at the top of the `get_svg()` function in `server.py`:

| Constant | Default | What it does |
|---|---|---|
| `SVG_WIDTH` | `500` | Total badge width in pixels |
| `SVG_HEIGHT` | `100` | Total badge height in pixels |
| `ARTWORK_SIZE` | `76` | Album art square size; keep below `SVG_HEIGHT - 24` |
| `BLOB_OPACITY` | `0.55` | Background blob opacity from 0.0 to 1.0 |
| `BLOB_BLUR` | `30` | Gaussian blur radius; higher values make blobs softer |
| `BG_COLOR` | `"#0a0a0a"` | Base background color |

The equalizer bar color and background blob colors are derived automatically from the album artwork. If you want to override them, set `accent` and `c1/c2/c3` to fixed hex values instead of using the extracted palette.

To adjust the blob movement speed, change the `dur` values on the `<animate>` elements inside `bg_blobs`. Longer durations mean slower movement.

---

## Troubleshooting

**Badge shows "Not playing"**

The server has not received any data yet. Make sure `music.apple.com` is open in your browser with a track playing. Check that the Tampermonkey icon on that tab shows a number badge rather than "No access needed".

**Selectors stopped working**

Apple occasionally changes the player bar markup. If the widget stops updating, open DevTools on `music.apple.com` and run:

```js
document.querySelector('[data-testid="lcd-metadata"] .marquee--primary [data-testid="marquee-text-item"]')?.textContent
```

If it returns `null`, inspect the bottom player bar and update the selectors in `tampermonkey.js`. The comments in that file explain what each selector targets.

**Tunnel URL changes after restart**

Cloudflare quick tunnels assign a new hostname on every run. `start.py` updates the README automatically each time, so the badge always points to the right URL. If you want a stable URL, set up a named Cloudflare tunnel with a custom domain.

---

## License

MIT
