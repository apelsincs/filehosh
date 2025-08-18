// Переключатель тем для 0123.ru

class MaterialThemeManager {
    constructor() {
        this.currentTheme = 'light';
        this.themes = ['light', 'dark'];
        this.init();
    }

    init() {
        this.loadTheme();
        this.setupEventListeners();
        this.applyTheme();
        this.setupKeyboardShortcuts();
    }

    loadTheme() {
        // Загружаем сохраненную тему из localStorage
        const savedTheme = localStorage.getItem('md-theme');
        if (savedTheme && this.themes.includes(savedTheme)) {
            this.currentTheme = savedTheme;
        } else {
            // Определяем тему по системным настройкам
            this.currentTheme = this.getSystemTheme();
        }
    }

    getSystemTheme() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    setupEventListeners() {
        // Обработчики для кнопок переключения темы
        const themeButtons = document.querySelectorAll('.theme-btn');
        themeButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const theme = e.currentTarget.dataset.theme;
                if (theme && this.themes.includes(theme)) {
                    this.switchTheme(theme);
                }
            });
        });

        // Слушаем изменения системной темы
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addEventListener('change', (e) => {
                if (!localStorage.getItem('md-theme')) {
                    this.switchTheme(e.matches ? 'dark' : 'light');
                }
            });
        }
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + T для переключения темы
            if ((e.ctrlKey || e.metaKey) && e.key === 't') {
                e.preventDefault();
                this.toggleTheme();
            }
        });
    }

    switchTheme(theme) {
        if (!this.themes.includes(theme)) return;

        // Добавляем класс для плавного перехода
        document.body.classList.add('theme-transitioning');

        this.currentTheme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        
        // Сохраняем в localStorage
        localStorage.setItem('md-theme', theme);

        // Обновляем активную кнопку
        this.updateActiveButton();

        // Обновляем мета-теги
        this.updateMetaTags();

        // Показываем уведомление
        this.showThemeNotification(theme);

        // Убираем класс перехода через небольшую задержку
        setTimeout(() => {
            document.body.classList.remove('theme-transitioning');
        }, 300);
    }

    toggleTheme() {
        const currentIndex = this.themes.indexOf(this.currentTheme);
        const nextIndex = (currentIndex + 1) % this.themes.length;
        this.switchTheme(this.themes[nextIndex]);
    }

    updateActiveButton() {
        const themeButtons = document.querySelectorAll('.theme-btn');
        themeButtons.forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.theme === this.currentTheme) {
                btn.classList.add('active');
            }
        });
    }

    updateMetaTags() {
        // Обновляем theme-color для мобильных устройств
        let metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (!metaThemeColor) {
            metaThemeColor = document.createElement('meta');
            metaThemeColor.name = 'theme-color';
            document.head.appendChild(metaThemeColor);
        }

        if (this.currentTheme === 'dark') {
            metaThemeColor.content = '#000000';
        } else {
            metaThemeColor.content = '#1976d2';
        }
    }

    showThemeNotification(theme) {
        const themeNames = {
            'light': 'Светлая тема',
            'dark': 'Темная тема'
        };

        const notification = document.createElement('div');
        notification.className = 'notification notification-info';
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-palette"></i>
                <span>Переключено на ${themeNames[theme]}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        // Добавляем в контейнер уведомлений
        let container = document.querySelector('.notification-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'notification-container';
            document.body.appendChild(container);
        }

        container.appendChild(notification);

        // Показываем уведомление
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);

        // Автоматически скрываем через 3 секунды
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 300);
        }, 3000);
    }

    applyTheme() {
        document.documentElement.setAttribute('data-theme', this.currentTheme);
        this.updateActiveButton();
        this.updateMetaTags();
    }

    // Получить текущую тему
    getCurrentTheme() {
        return this.currentTheme;
    }

    // Проверить, является ли тема темной
    isDarkTheme() {
        return this.currentTheme === 'dark';
    }

    // Получить CSS переменную для текущей темы
    getCSSVariable(variable) {
        return getComputedStyle(document.documentElement).getPropertyValue(variable);
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.mdThemeManager = new MaterialThemeManager();
});

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MaterialThemeManager;
} 