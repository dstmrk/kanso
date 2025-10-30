"""UI styles, SVG icons, and CSS class constants for the Kanso application."""

# Animation and timing constants
SKELETON_ANIMATION_SPEED: float = 1.5  # Slower, smoother animation (lower = slower)

# Stat card styles (DaisyUI)
STAT_CARDS_CLASSES: str = " stat bg-base-100 shadow-md"
STAT_CARDS_LABEL_CLASSES: str = " stat-title text-lg"
STAT_CARDS_VALUE_CLASSES: str = " stat-value"
STAT_CARDS_DESC_CLASSES: str = " stat-desc text-bold"

# Chart card styles (DaisyUI)
CHART_CARDS_CLASSES: str = " bg-base-100 shadow-md"
CHART_CARDS_LABEL_CLASSES: str = " card-title mb-2"
CHART_CARDS_CHARTS_CLASSES: str = " h-64 w-full"

# ECharts theme configuration
DEFAULT_ECHART_THEME_FOLDER: str = "themes/"
DEFAULT_ECHARTS_THEME_SUFFIX: str = "_default_echarts_theme.json"

# SVG Icons (minified for performance)
LOGO_SVG: str = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 230 64" class="h-8"><circle cx="32" cy="32" r="27" fill="#fff"/><g transform="translate(10.4,10.4)scale(1.8)" fill="none" stroke="#009688" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 16l6-7 5 5 5-6"/><path d="M15 14m-1 0a1 1 0 1 0 2 0a1 1 0 1 0-2 0"/><path d="M10 9m-1 0a1 1 0 1 0 2 0a1 1 0 1 0-2 0"/><path d="M4 16m-1 0a1 1 0 1 0 2 0a1 1 0 1 0-2 0"/><path d="M20 8m-1 0a1 1 0 1 0 2 0a1 1 0 1 0-2 0"/></g><text x="70" y="50" font-family="sans-serif" font-size="50" font-weight="bold" fill="#fff" letter-spacing="1">Kanso</text></svg>'
)

PROFILE_SVG: str = (
    '<svg xmlns="http://www.w3.org/2000/svg" class="size-[1.2em]" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z"/></svg>'
)

HOME_SVG: str = (
    '<svg xmlns="http://www.w3.org/2000/svg" class="size-[1.2em]" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="m2.25 12 8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25"/></svg>'
)

EXPENSES_SVG: str = (
    '<svg xmlns="http://www.w3.org/2000/svg" class="size-[1.2em]" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 6.75h12M8.25 12h12m-12 5.25h12M3.75 6.75h.007v.008H3.75V6.75Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0ZM3.75 12h.007v.008H3.75V12Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm-.375 5.25h.007v.008H3.75v-.008Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z"/></svg>'
)

SUN_SVG: str = (
    '<svg xmlns="http://www.w3.org/2000/svg" class="size-[1.2em]" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M1 12h2M21 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"/></svg>'
)

MOON_SVG: str = (
    '<svg xmlns="http://www.w3.org/2000/svg" class="size-[1.2em]" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
)

CLOCK_SVG: str = (
    '<svg xmlns="http://www.w3.org/2000/svg" class="size-[1em]" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/></svg>'
)

INSIGHTS_SVG: str = (
    '<svg xmlns="http://www.w3.org/2000/svg" class="size-[1.2em]" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z"/></svg>'
)

NET_WORTH_SVG: str = (
    '<svg xmlns="http://www.w3.org/2000/svg" class="size-[1.2em]" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18 9 11.25l4.306 4.306a11.95 11.95 0 0 1 5.814-5.518l2.74-1.22m0 0-5.94-2.281m5.94 2.28-2.28 5.941"/></svg>'
)
