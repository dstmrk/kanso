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
LOGO_SVG: str = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 230 64" class="h-8"><circle cx="32" cy="32" r="27" fill="#fff"/><g transform="translate(10.4,10.4)scale(1.8)" fill="none" stroke="#009688" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 16l6-7 5 5 5-6"/><path d="M15 14m-1 0a1 1 0 1 0 2 0a1 1 0 1 0-2 0"/><path d="M10 9m-1 0a1 1 0 1 0 2 0a1 1 0 1 0-2 0"/><path d="M4 16m-1 0a1 1 0 1 0 2 0a1 1 0 1 0-2 0"/><path d="M20 8m-1 0a1 1 0 1 0 2 0a1 1 0 1 0-2 0"/></g><text x="70" y="50" font-family="sans-serif" font-size="50" font-weight="bold" fill="#fff" letter-spacing="1">Kanso</text></svg>'

PROFILE_SVG: str = '<svg xmlns="http://www.w3.org/2000/svg" class="size-[1.2em]" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z"/></svg>'

HOME_SVG: str = '<svg xmlns="http://www.w3.org/2000/svg" class="size-[1.2em]" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="m2.25 12 8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25"/></svg>'

EXPENSES_SVG: str = '<svg xmlns="http://www.w3.org/2000/svg" class="size-[1.2em]" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 6.75h12M8.25 12h12m-12 5.25h12M3.75 6.75h.007v.008H3.75V6.75Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0ZM3.75 12h.007v.008H3.75V12Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm-.375 5.25h.007v.008H3.75v-.008Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z"/></svg>'

SUN_SVG: str = '<svg xmlns="http://www.w3.org/2000/svg" class="size-[1.2em]" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M1 12h2M21 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"/></svg>'

MOON_SVG: str = '<svg xmlns="http://www.w3.org/2000/svg" class="size-[1.2em]" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'

CLOCK_SVG: str = '<svg xmlns="http://www.w3.org/2000/svg" class="size-[1em]" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/></svg>'

INSIGHTS_SVG: str = '<svg xmlns="http://www.w3.org/2000/svg" class="size-[1.2em]" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z"/></svg>'

NET_WORTH_SVG: str = '<svg xmlns="http://www.w3.org/2000/svg" class="size-[1.2em]" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18 9 11.25l4.306 4.306a11.95 11.95 0 0 1 5.814-5.518l2.74-1.22m0 0-5.94-2.281m5.94 2.28-2.28 5.941"/></svg>'

SETTINGS_SVG: str = '<svg xmlns="http://www.w3.org/2000/svg" class="size-[1.2em]" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z"/><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"/></svg>'

DOCUMENT_SVG: str = '<svg xmlns="http://www.w3.org/2000/svg" class="size-[1.2em]" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"/></svg>'

GITHUB_SVG: str = '<svg xmlns="http://www.w3.org/2000/svg" class="size-[1.2em]" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>'

HEART_SVG: str = '<svg xmlns="http://www.w3.org/2000/svg" class="size-[1.2em]" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12Z"/></svg>'

REFRESH_SVG: str = '<svg xmlns="http://www.w3.org/2000/svg" class="size-[1.2em]" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99"/></svg>'

ADD_SVG: str = '<svg xmlns="http://www.w3.org/2000/svg" class="size-[1.2em]" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15"/></svg>'

# AG Grid + daisyUI theme integration
AGGRID_DAISY_THEME_CSS: str = """
<style>
/* AG Grid theme that follows daisyUI dark/light mode */
.nicegui-aggrid {
    --ag-background-color: oklch(var(--b1));
    --ag-odd-row-background-color: oklch(var(--b1));
    --ag-header-background-color: oklch(var(--b2));
    --ag-chrome-background-color: oklch(var(--b2));
    --ag-foreground-color: oklch(var(--bc));
    --ag-text-color: oklch(var(--bc));
    --ag-border-color: oklch(var(--b3));
}
</style>
"""
