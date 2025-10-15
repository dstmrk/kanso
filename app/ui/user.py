from nicegui import app, ui

from app.core.state_manager import state_manager
from app.services import pages
from app.services.utils import get_user_currency
from app.ui import dock, header, styles

# Currency options with symbol and code only
CURRENCY_OPTIONS = {"EUR": "€ EUR", "USD": "$ USD", "GBP": "£ GBP", "CHF": "Fr CHF", "JPY": "¥ JPY"}


def render_theme_toggle() -> None:
    """Render theme toggle switch (light/dark mode)."""

    def save_theme_preference() -> None:
        current_theme: str = app.storage.user.get("theme", "light")
        new_theme: str = "dark" if current_theme == "light" else "light"
        app.storage.user["theme"] = new_theme

        # Update localStorage and DOM immediately
        script: str = f"""
            localStorage.setItem('kanso-theme', '{new_theme}');
            document.documentElement.setAttribute('data-theme', '{new_theme}');
            document.documentElement.style.colorScheme = '{new_theme}';
        """
        ui.run_javascript(script)

    with ui.element("label").classes("flex cursor-pointer gap-2 items-center"):
        ui.html(styles.SUN_SVG, sanitize=False)
        toggle = (
            ui.element("input")
            .props('type="checkbox" value="dark"')
            .classes("toggle")
            .on("click", save_theme_preference)
        )
        current_theme: str = app.storage.user.get("theme", "light")
        if current_theme == "dark":
            toggle.props("checked")
        ui.html(styles.MOON_SVG, sanitize=False)


def render_currency_selector() -> None:
    """Render currency dropdown selector."""

    def save_currency_preference(event) -> None:
        """Save the selected currency preference."""
        selected_code = event.value
        app.storage.user["currency"] = selected_code
        ui.notify(f"Currency changed to {CURRENCY_OPTIONS[selected_code]}", type="positive")

    # Get current currency: use stored preference or detect from locale
    current_currency: str = app.storage.user.get("currency", get_user_currency())
    # Save it if it wasn't stored yet
    if "currency" not in app.storage.user:
        app.storage.user["currency"] = current_currency

    # DaisyUI dropdown component
    with ui.element("div").classes("dropdown"):
        # Dropdown button showing current selection
        current_label = CURRENCY_OPTIONS[current_currency]
        dropdown_btn = (
            ui.element("div").props('tabindex="0" role="button"').classes("btn btn-outline w-48")
        )
        with dropdown_btn:
            label_display = ui.label(current_label).classes("mx-auto")

        # Dropdown menu
        with (
            ui.element("ul")
            .props('tabindex="0"')
            .classes("dropdown-content menu bg-base-100 rounded-box z-[1] w-48 p-2 shadow mt-2")
        ):
            for code, label in CURRENCY_OPTIONS.items():
                with ui.element("li"):

                    def make_click_handler(currency_code, label_text):
                        def handler():
                            save_currency_preference(type("Event", (), {"value": currency_code})())
                            label_display.set_text(label_text)
                            # Close dropdown by removing focus
                            ui.run_javascript("document.activeElement.blur()")

                        return handler

                    link = ui.element("a")
                    with link:
                        ui.label(label)
                    link.on("click", make_click_handler(code, label))


def render_refresh_button() -> None:
    """Render data refresh button."""

    def refresh_data() -> None:
        """Force refresh of all cached data by clearing the cache."""
        state_manager.invalidate_cache()
        ui.notify("Data cache cleared! Data will be refreshed on next page visit.", type="positive")

    with (
        ui.element("button")
        .on("click", refresh_data)
        .classes("btn bg-secondary hover:bg-secondary/80 text-secondary-content w-48")
    ):
        ui.label("Refresh Data")


def render_logout_button() -> None:
    """Render logout button."""
    with (
        ui.element("button")
        .on("click", lambda: ui.navigate.to(pages.LOGOUT_PAGE))
        .classes("btn btn-outline btn-error w-48")
    ):
        ui.label("Logout")


def render() -> None:
    """Render the user settings page with theme toggle and data refresh."""
    header.render()

    with ui.column().classes("mx-auto items-center gap-6 p-4"):
        render_theme_toggle()
        render_currency_selector()
        render_refresh_button()
        render_logout_button()

    dock.render()
