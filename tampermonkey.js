// ==UserScript==
// @name         Apple Music Now Playing
// @namespace    https://github.com/yourusername/apple-music-now-playing
// @version      1.0
// @description  Reads the current track from Apple Music web and sends it to your local widget server
// @match        https://music.apple.com/*
// @grant        GM_xmlhttpRequest
// @connect      localhost
// ==/UserScript==

// fetch() is not used here because Apple Music's Content Security Policy
// blocks requests to localhost from the page context.
// GM_xmlhttpRequest runs outside the page sandbox and bypasses the CSP.

(function () {
    'use strict';

    const SERVER_URL  = 'http://localhost:8000/now-playing';
    const SECRET      = 'your_api_secret_here'; // must match API_SECRET in your .env file
    const INTERVAL_MS = 10000;                  // polling interval in milliseconds

    // -------------------------------------------------------------------------
    // DOM selectors for the Apple Music web player bar (bottom of the page).
    //
    // Apple occasionally updates their markup. If the badge stops updating,
    // open DevTools on music.apple.com while a track is playing and run:
    //
    //   document.querySelector('[data-testid="lcd-metadata"] .marquee--primary [data-testid="marquee-text-item"]')?.textContent
    //
    // If it returns null, inspect the player bar and update the selectors below.
    // -------------------------------------------------------------------------

    function getTrackInfo() {
        // Song title -- first text node inside the primary scrolling marquee
        const titleEl = document.querySelector(
            '[data-testid="lcd-metadata"] .marquee--primary [data-testid="marquee-text-item"]'
        );
        if (!titleEl) return null;

        // Artist name -- the first button in the secondary marquee
        // (it is a button because clicking it opens the artist page)
        const artistEl = document.querySelector(
            '[data-testid="lcd-metadata"] .marquee--secondary [data-testid="marquee-text-item-button"]'
        );

        // Artwork URL -- the <img> src is a 1x1 lazy-load placeholder, so we
        // read the actual URL from the <source> element's srcset instead.
        // We then replace the thumbnail size with 300x300 for better quality.
        let artworkUrl = null;
        const sourceEl = document.querySelector('[data-testid="player-lcd-artwork"] source');
        if (sourceEl && sourceEl.srcset) {
            const first = sourceEl.srcset.split(',')[0].trim().split(' ')[0];
            if (first) {
                artworkUrl = first.replace(/\/\d+x\d+[^/]*\.jpg$/, '/300x300bb.jpg');
            }
        }

        // Play state -- when playing, the play button is hidden via aria-hidden="true"
        // and the pause button is visible. We detect playing by checking the play button.
        const playBtn   = document.querySelector(
            '[data-testid="playback-controls"] .playback-play__play'
        );
        const isPlaying = playBtn ? playBtn.getAttribute('aria-hidden') === 'true' : false;

        return {
            title:       titleEl.textContent.trim(),
            artist:      artistEl ? artistEl.textContent.trim() : '',
            artwork_url: artworkUrl,
            is_playing:  isPlaying,
        };
    }

    let lastSent = null;

    function sendUpdate() {
        const info = getTrackInfo();
        if (!info) return;

        // Only send when the track or play state actually changes
        const key = `${info.title}|${info.is_playing}`;
        if (key === lastSent) return;
        lastSent = key;

        GM_xmlhttpRequest({
            method:  'POST',
            url:     SERVER_URL,
            headers: {
                'Content-Type': 'application/json',
                'X-Secret':     SECRET,
            },
            data:    JSON.stringify(info),
            onerror: () => {},
        });
    }

    setInterval(sendUpdate, INTERVAL_MS);
    sendUpdate();
})();
