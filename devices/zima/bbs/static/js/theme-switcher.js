// Theme Switcher for Neighborhood BBS
// Supports: Hacker (default), Vaporwave, Dracula

const THEME_STORAGE_KEY = 'neighborhood_bbs_theme';
const DEFAULT_THEME = 'hacker';
const AVAILABLE_THEMES = ['hacker', 'vaporwave', 'dracula'];

class ThemeSwitcher {
    constructor() {
        this.currentTheme = this.loadTheme();
        this.cssPathBase = '/static/css/theme-';
        this.init();
    }

    /**
     * Initialize theme switcher
     */
    init() {
        this.applyTheme(this.currentTheme);
        this.setupThemeSelector();
        this.setupThemeChangeListener();
    }

    /**
     * Load theme from localStorage or use default
     */
    loadTheme() {
        const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
        if (savedTheme && AVAILABLE_THEMES.includes(savedTheme)) {
            return savedTheme;
        }
        return DEFAULT_THEME;
    }

    /**
     * Save theme to localStorage
     */
    saveTheme(theme) {
        if (AVAILABLE_THEMES.includes(theme)) {
            localStorage.setItem(THEME_STORAGE_KEY, theme);
        }
    }

    /**
     * Apply theme by loading CSS file
     */
    applyTheme(theme) {
        if (!AVAILABLE_THEMES.includes(theme)) {
            console.warn(`Invalid theme: ${theme}, using default`);
            theme = DEFAULT_THEME;
        }

        // Remove existing theme CSS
        const existingLink = document.getElementById('theme-css-link');
        if (existingLink) {
            existingLink.remove();
        }

        // Create and append new theme CSS
        const link = document.createElement('link');
        link.id = 'theme-css-link';
        link.rel = 'stylesheet';
        link.href = `${this.cssPathBase}${theme}.css?v=${Date.now()}`;
        
        link.onload = () => {
            console.log(`Theme loaded: ${theme}`);
            this.currentTheme = theme;
            this.updateThemeSelector(theme);
        };

        link.onerror = () => {
            console.error(`Failed to load theme: ${theme}`);
            // Fallback to hacker theme
            if (theme !== DEFAULT_THEME) {
                this.applyTheme(DEFAULT_THEME);
            }
        };

        document.head.appendChild(link);
        this.saveTheme(theme);
    }

    /**
     * Setup theme selector dropdown
     */
    setupThemeSelector() {
        // Check if selector already exists
        let selector = document.getElementById('theme-selector-container');
        
        if (!selector) {
            selector = document.createElement('div');
            selector.id = 'theme-selector-container';
            selector.className = 'theme-selector';
            
            const label = document.createElement('label');
            label.textContent = 'Theme: ';
            label.style.marginRight = '5px';
            label.style.fontSize = '12px';
            
            const select = document.createElement('select');
            select.id = 'theme-select';
            
            // Add option for each theme
            AVAILABLE_THEMES.forEach(themeName => {
                const option = document.createElement('option');
                option.value = themeName;
                option.textContent = this.formatThemeName(themeName);
                if (themeName === this.currentTheme) {
                    option.selected = true;
                }
                select.appendChild(option);
            });
            
            selector.appendChild(label);
            selector.appendChild(select);
            document.body.appendChild(selector);
        }
    }

    /**
     * Setup event listener for theme changes
     */
    setupThemeChangeListener() {
        const selector = document.getElementById('theme-select');
        if (selector) {
            selector.addEventListener('change', (e) => {
                this.applyTheme(e.target.value);
            });
        }
    }

    /**
     * Update theme selector to reflect current theme
     */
    updateThemeSelector(theme) {
        const selector = document.getElementById('theme-select');
        if (selector) {
            selector.value = theme;
        }
    }

    /**
     * Format theme name for display
     */
    formatThemeName(themeName) {
        const names = {
            'hacker': '🖥️ Terminal Hacker',
            'vaporwave': '🌊 Vaporwave',
            'dracula': '🧛 Dracula'
        };
        return names[themeName] || themeName;
    }

    /**
     * Get list of available themes
     */
    getAvailableThemes() {
        return AVAILABLE_THEMES;
    }

    /**
     * Get current theme
     */
    getCurrentTheme() {
        return this.currentTheme;
    }

    /**
     * Reset to default theme
     */
    resetToDefault() {
        localStorage.removeItem(THEME_STORAGE_KEY);
        this.applyTheme(DEFAULT_THEME);
    }
}

// Initialize theme switcher when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeSwitcher();
});

// Fallback if DOM is already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (!window.themeManager) {
            window.themeManager = new ThemeSwitcher();
        }
    });
} else {
    if (!window.themeManager) {
        window.themeManager = new ThemeSwitcher();
    }
}
