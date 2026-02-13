// iTaK Browser Init Override
// Injected into Playwright browser contexts via browser-use.
// Handles common cookie consent dialogs and anti-bot checks.

(function () {
    'use strict';

    // Auto-dismiss cookie consent banners
    const consentSelectors = [
        '[id*="cookie-consent"] button[class*="accept"]',
        '[id*="cookie-banner"] button[class*="accept"]',
        '[class*="cookie-consent"] button[class*="accept"]',
        '#onetrust-accept-btn-handler',
        '.cc-btn.cc-allow',
        'button[data-testid="cookie-policy-dialog-accept-button"]',
        '[aria-label*="Accept cookies"]',
        '[aria-label*="Accept all"]',
    ];

    function dismissConsent() {
        for (const selector of consentSelectors) {
            const btn = document.querySelector(selector);
            if (btn && btn.offsetParent !== null) {
                btn.click();
                return true;
            }
        }
        return false;
    }

    // Try immediately and with a delay
    dismissConsent();
    setTimeout(dismissConsent, 1000);
    setTimeout(dismissConsent, 3000);

    // Override navigator properties to avoid bot detection
    Object.defineProperty(navigator, 'webdriver', {
        get: () => false,
    });
})();
