/* Multilingual Support - English / Malayalam */
(function () {
    const LANG_KEY = 'agrivision_lang';

    function getLang() {
        return localStorage.getItem(LANG_KEY) || 'en';
    }

    function setLang(lang) {
        localStorage.setItem(LANG_KEY, lang);
        applyLang(lang);
    }

    function applyLang(lang) {
        // Toggle visibility of content spans (but NOT the toggle buttons themselves)
        document.querySelectorAll('[data-lang]:not(.lang-btn)').forEach(el => {
            el.style.display = (el.dataset.lang === lang) ? '' : 'none';
        });

        // Highlight the active button
        document.querySelectorAll('.lang-btn').forEach(btn => {
            const isActive = btn.dataset.lang === lang;
            btn.style.background = isActive ? '#1b5e20' : 'transparent';
            btn.style.color = isActive ? '#fff' : '#1b5e20';
        });

        document.documentElement.lang = (lang === 'ml') ? 'ml' : 'en';
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('.lang-btn').forEach(btn => {
            btn.addEventListener('click', () => setLang(btn.dataset.lang));
        });
        applyLang(getLang());
    });

    window.AgriLang = { get: getLang, set: setLang, apply: applyLang };
})();