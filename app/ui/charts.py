from typing import Any, Literal

from app.core.currency_formats import get_currency_format


class ChartOptionsBuilder:
    """Centralized chart options builder with common formatting."""

    @staticmethod
    def get_font_size(user_agent: Literal["mobile", "desktop"]) -> int:
        """Get font size based on user agent."""
        return 8 if user_agent == "mobile" else 12

    @staticmethod
    def create_currency_formatter(currency: str, decimals: int = 2) -> str:
        """Create JavaScript currency formatter function with hardcoded symbols.

        Args:
            currency: Currency code (EUR, USD, GBP, CHF, JPY)
            decimals: Number of decimal places (default: 2)

        Returns:
            JavaScript function string for ECharts formatter

        Note:
            Uses hardcoded currency symbols to avoid browser locale issues.
            All currencies use space between symbol and number for consistency.
        """
        # Get currency format from centralized config
        fmt = get_currency_format(currency)
        symbol = fmt.symbol
        thousands_sep = fmt.thousands_sep
        decimal_sep = fmt.decimal_sep

        # Build formatter based on currency configuration
        if decimals > 0 and fmt.has_decimals:
            # Format with decimals: split integer and decimal parts
            if fmt.position == "before":
                return f'function(value) {{ const parts = Math.abs(value).toFixed({decimals}).split("."); const int = parts[0].replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, "{thousands_sep}"); const dec = parts[1]; return (value < 0 ? "-" : "") + "{symbol} " + int + "{decimal_sep}" + dec; }}'
            else:
                return f'function(value) {{ const parts = Math.abs(value).toFixed({decimals}).split("."); const int = parts[0].replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, "{thousands_sep}"); const dec = parts[1]; return (value < 0 ? "-" : "") + int + "{decimal_sep}" + dec + " {symbol}"; }}'
        else:
            # Format without decimals: just integer part
            if fmt.position == "before":
                return f'function(value) {{ const formatted = Math.abs(value).toFixed(0).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, "{thousands_sep}"); return (value < 0 ? "-" : "") + "{symbol} " + formatted; }}'
            else:
                return f'function(value) {{ const formatted = Math.abs(value).toFixed(0).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, "{thousands_sep}"); return (value < 0 ? "-" : "") + formatted + " {symbol}"; }}'

    @staticmethod
    def get_common_tooltip(currency: str = "USD") -> dict[str, str]:
        """Get common tooltip configuration with currency formatting."""
        return {
            ":valueFormatter": ChartOptionsBuilder.create_currency_formatter(currency, decimals=2)
        }

    @staticmethod
    def get_common_grid() -> dict[str, str]:
        """Get common grid configuration."""
        return {"left": "15%", "right": "5%", "top": "10%", "bottom": "20%"}

    @staticmethod
    def get_currency_axis_label(
        user_agent: Literal["mobile", "desktop"], currency: str = "USD"
    ) -> dict[str, Any]:
        """Get currency formatted axis label."""
        return {
            "fontSize": ChartOptionsBuilder.get_font_size(user_agent),
            ":formatter": ChartOptionsBuilder.create_currency_formatter(currency, decimals=0),
        }


def create_net_worth_chart_options(
    net_worth_data: dict[str, Any], user_agent: Literal["mobile", "desktop"], currency: str = "USD"
) -> dict[str, Any]:
    return {
        "tooltip": {"trigger": "axis", **ChartOptionsBuilder.get_common_tooltip(currency)},
        "grid": ChartOptionsBuilder.get_common_grid(),
        "xAxis": {
            "type": "category",
            "data": net_worth_data.get("dates", []),
            "axisLabel": {"fontSize": ChartOptionsBuilder.get_font_size(user_agent)},
        },
        "yAxis": {
            "type": "value",
            "axisLabel": ChartOptionsBuilder.get_currency_axis_label(user_agent, currency),
        },
        "series": [
            {
                "name": "Net Worth",
                "type": "line",
                "smooth": True,
                "data": net_worth_data.get("values", []),
                "areaStyle": {},
            }
        ],
    }


def create_asset_vs_liabilities_chart(
    chart_data: dict[str, Any], user_agent: Literal["mobile", "desktop"], currency: str = "USD"
) -> dict[str, Any]:
    # Convert ObservableDict to regular dict (NiceGUI compatibility)
    chart_data = dict(chart_data)
    for key in chart_data:
        if hasattr(chart_data[key], "items"):
            chart_data[key] = dict(chart_data[key])
            # Handle nested dicts
            for subkey in list(chart_data[key].keys()):
                if hasattr(chart_data[key][subkey], "items"):
                    chart_data[key][subkey] = dict(chart_data[key][subkey])

    # Build data structure without explicit colors (let ECharts handle gradients)
    data: list[dict[str, Any]] = []
    for category_name, items in chart_data.items():
        category: dict[str, Any] = {"name": category_name, "children": []}
        for item_name, value in items.items():
            # Check if value is a dict (nested structure from MultiIndex)
            if isinstance(value, dict):
                # MultiIndex case: create subcategory with children
                subcategory: dict[str, Any] = {"name": item_name, "children": []}
                for sub_item_name, sub_value in value.items():
                    subcategory["children"].append({"name": sub_item_name, "value": abs(sub_value)})
                category["children"].append(subcategory)
            else:
                # Single header case: direct value
                category["children"].append({"name": item_name, "value": abs(value)})
        data.append(category)

    # Sort data to ensure consistent color assignment: Assets (green), Liabilities (red)
    category_order = {"Assets": 0, "Liabilities": 1, "Net Worth": 2}
    data.sort(key=lambda x: category_order.get(x["name"], 999))

    return {
        "tooltip": {"trigger": "item", **ChartOptionsBuilder.get_common_tooltip(currency)},
        "grid": ChartOptionsBuilder.get_common_grid(),
        "color": [
            "#2b821d",
            "#c12e34",
            "#777777",
        ],  # Green for Assets, Red for Liabilities, Gray for Net Worth
        "series": {
            "type": "sunburst",
            "data": data,
            "radius": [50, "80%"],
            "itemStyle": {"borderRadius": 5, "borderWidth": 1},
            "label": {
                "show": "true",
                "rotate": "0",
                "minAngle": 5,
                "color": "#dddddd",
                "fontSize": ChartOptionsBuilder.get_font_size(user_agent),
            },
        },
    }


def create_cash_flow_options(
    cash_flow_data: dict[str, float],
    user_agent: Literal["mobile", "desktop"],
    currency: str = "USD",
) -> dict[str, Any]:
    """Create Sankey diagram for cash flow visualization.

    Supports both single and multiple income sources:
    - Single source: Income → Savings/Expenses
    - Multiple sources: Source1, Source2, ... → Total Income → Savings/Expenses

    Args:
        cash_flow_data: Dict with income sources, Savings, Expenses, and expense categories
        user_agent: mobile or desktop for sizing
        currency: Currency code for formatting

    Returns:
        ECharts Sankey diagram options
    """
    savings = cash_flow_data.get("Savings", 0)
    expenses_total = cash_flow_data.get("Expenses", 0)

    # Income sources: keys that are not Savings or Expenses
    # We need to differentiate between income sources and expense categories
    # Income sources come first in the dict (from finance_calculator)
    # Expense categories come after Expenses key

    income_sources: dict[str, float] = {}
    expense_categories: dict[str, float] = {}

    # Parse keys in order to identify structure
    found_expenses_key = False
    for key, value in cash_flow_data.items():
        if key == "Expenses":
            found_expenses_key = True
            continue
        elif key == "Savings":
            continue
        elif not found_expenses_key:
            # Before "Expenses" key = income sources
            income_sources[key] = value
        else:
            # After "Expenses" key = expense categories
            expense_categories[key] = value

    has_multiple_sources = len(income_sources) > 1

    colors = [
        "#e6b600",
        "#95706d",
        "#9bbc99",
        "#8c6ac4",
        "#ea7e53",
        "#0098d9",
        "#e098c7",
        "#73c0de",
        "#3fb27f",
    ]

    # Build nodes and links based on income source count
    if has_multiple_sources:
        # Multiple income sources: Source1, Source2 → Total Income → Savings/Expenses
        nodes = [
            # Income source nodes (green shades)
            *[
                {"name": source, "itemStyle": {"color": "#2b821d" if i == 0 else "#4a9d3a"}}
                for i, source in enumerate(income_sources)
            ],
            # Aggregation node
            {"name": "Total Income", "itemStyle": {"color": "#2b821d"}},
            # Output nodes
            {"name": "Savings", "itemStyle": {"color": "#005eaa"}},
            {"name": "Expenses", "itemStyle": {"color": "#c12e34"}},
            # Expense category nodes
            *[
                {"name": category, "itemStyle": {"color": colors[i % len(colors)]}}
                for i, category in enumerate(expense_categories)
            ],
        ]

        links = [
            # Income sources → Total Income
            *[
                {"source": source, "target": "Total Income", "value": round(amount, 2)}
                for source, amount in income_sources.items()
            ],
            # Total Income → Savings/Expenses
            {"source": "Total Income", "target": "Savings", "value": round(savings, 2)},
            {"source": "Total Income", "target": "Expenses", "value": round(expenses_total, 2)},
            # Expenses → Categories
            *[
                {"source": "Expenses", "target": category, "value": round(amount, 2)}
                for category, amount in expense_categories.items()
            ],
        ]
    else:
        # Single income source: keep original behavior
        income_name = list(income_sources.keys())[0] if income_sources else "Income"

        nodes = [
            {"name": income_name, "itemStyle": {"color": "#2b821d"}},
            {"name": "Savings", "itemStyle": {"color": "#005eaa"}},
            {"name": "Expenses", "itemStyle": {"color": "#c12e34"}},
            *[
                {"name": category, "itemStyle": {"color": colors[i % len(colors)]}}
                for i, category in enumerate(expense_categories)
            ],
        ]

        links = [
            {"source": income_name, "target": "Savings", "value": round(savings, 2)},
            {"source": income_name, "target": "Expenses", "value": round(expenses_total, 2)},
            *[
                {"source": "Expenses", "target": category, "value": round(amount, 2)}
                for category, amount in expense_categories.items()
            ],
        ]

    return {
        "tooltip": {
            "trigger": "item",
            "triggerOn": "mousemove",
            **ChartOptionsBuilder.get_common_tooltip(currency),
        },
        "series": [
            {
                "type": "sankey",
                "layout": "none",
                "data": nodes,
                "links": links,
                "emphasis": {"focus": "adjacency"},
                "lineStyle": {"color": "source", "curveness": 0.3},
                "label": {"fontSize": ChartOptionsBuilder.get_font_size(user_agent)},
            }
        ],
    }


def create_avg_expenses_options(
    expenses_data: dict[str, float], user_agent: Literal["mobile", "desktop"], currency: str = "USD"
) -> dict[str, Any]:
    data = [{"name": category, "value": value} for category, value in expenses_data.items()]

    return {
        "tooltip": {"trigger": "item", **ChartOptionsBuilder.get_common_tooltip(currency)},
        "series": {
            "type": "pie",
            "radius": [50, "80%"],
            "avoidLabelOverlap": "false",
            "itemStyle": {"borderRadius": 5, "borderColor": "#fff", "borderWidth": 1},
            "label": {"minAngle": 5, "fontSize": ChartOptionsBuilder.get_font_size(user_agent)},
            "labelLine": {"show": "false"},
            "data": data,
            "emphasis": {"focus": "self"},
        },
    }


def create_income_vs_expenses_options(
    income_vs_expenses_data: dict[str, Any],
    user_agent: Literal["mobile", "desktop"],
    currency: str = "USD",
) -> dict[str, Any]:
    return {
        "legend": {"data": ["Income", "Expenses"], "top": "0%", "left": "center"},
        "tooltip": {"trigger": "axis", **ChartOptionsBuilder.get_common_tooltip(currency)},
        "grid": ChartOptionsBuilder.get_common_grid(),
        "color": ["#2b821d", "#c12e34"],
        "xAxis": {
            "type": "category",
            "axisLabel": {"fontSize": ChartOptionsBuilder.get_font_size(user_agent)},
            "data": income_vs_expenses_data["dates"],
            "axisTick": {"alignWithLabel": True},
        },
        "yAxis": {
            "type": "value",
            "axisLabel": ChartOptionsBuilder.get_currency_axis_label(user_agent, currency),
            "axisLine": {"onZero": True},
            "splitLine": {"show": False},
        },
        "series": [
            {
                "name": "Income",
                "type": "bar",
                "stack": "total",
                "data": income_vs_expenses_data["incomes"],
                "emphasis": {"focus": "self"},
            },
            {
                "name": "Expenses",
                "type": "bar",
                "stack": "total",
                "data": income_vs_expenses_data["expenses"],
                "emphasis": {"focus": "self"},
            },
        ],
    }


def create_net_worth_evolution_by_class_options(
    net_worth_data: dict[str, Any],
    user_agent: Literal["mobile", "desktop"],
    currency: str = "USD",
) -> dict[str, Any]:
    """Create combo chart for net worth evolution with asset/liability class breakdown.

    Shows stacked area chart for asset classes (positive, green shades) and liability
    classes (negative, red shades), with a bold line for total net worth.

    Args:
        net_worth_data: Dict with dates, total, asset_classes, liability_classes
        user_agent: mobile or desktop for sizing
        currency: Currency code for formatting

    Returns:
        ECharts options for combo chart (stacked areas + line)
    """
    dates = net_worth_data.get("dates", [])
    total = net_worth_data.get("total", [])
    asset_classes = net_worth_data.get("asset_classes", {})
    liability_classes = net_worth_data.get("liability_classes", {})

    # Build legend data (all classes + Total Net Worth)
    legend_data = list(asset_classes.keys()) + list(liability_classes.keys()) + ["Net Worth"]

    # Build series: asset classes (stacked, green shades), liability classes (stacked, red shades)
    series: list[dict[str, Any]] = []

    # Asset classes - green shades, stacked
    asset_colors = [
        "#2b821d",  # Dark green
        "#4a9d3a",  # Medium green
        "#6fb85e",  # Light green
        "#8cc980",  # Lighter green
        "#a8daa1",  # Very light green
    ]
    for i, (class_name, values) in enumerate(asset_classes.items()):
        series.append(
            {
                "name": class_name,
                "type": "line",
                "stack": "assets",
                "areaStyle": {},
                "data": values,
                "smooth": True,
                "emphasis": {"focus": "series"},
                "itemStyle": {"color": asset_colors[i % len(asset_colors)]},
            }
        )

    # Liability classes - red shades (negative values below X axis, no stack)
    # Note: We don't stack liabilities because ECharts doesn't handle negative stacking well
    # Each liability class is shown as a separate negative area
    liability_colors = [
        "#c12e34",  # Dark red
        "#d9534f",  # Medium red
        "#e67373",  # Light red
        "#f19494",  # Lighter red
        "#f5b5b5",  # Very light red
    ]
    for i, (class_name, values) in enumerate(liability_classes.items()):
        # Ensure values are negative by taking absolute value and inverting
        negative_values = [-abs(v) for v in values]
        series.append(
            {
                "name": class_name,
                "type": "line",
                # No stack - show each liability as separate negative area
                "areaStyle": {"opacity": 0.7},  # Semi-transparent to see overlap
                "data": negative_values,  # Force negative values
                "smooth": True,
                "emphasis": {"focus": "series"},
                "itemStyle": {"color": liability_colors[i % len(liability_colors)]},
            }
        )

    # Total Net Worth - bold line on top (no stack)
    series.append(
        {
            "name": "Net Worth",
            "type": "line",
            "data": total,
            "smooth": True,
            "lineStyle": {"width": 3, "color": "#005eaa"},
            "itemStyle": {"color": "#005eaa"},
            "emphasis": {"focus": "series"},
            "z": 10,  # Ensure it's on top
        }
    )

    return {
        "legend": {
            "data": legend_data,
            "top": "3%",
            "left": "center",
            "type": "scroll",
            "textStyle": {"fontSize": ChartOptionsBuilder.get_font_size(user_agent)},
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross"},
            **ChartOptionsBuilder.get_common_tooltip(currency),
        },
        "grid": ChartOptionsBuilder.get_common_grid(),
        "xAxis": {
            "type": "category",
            "data": dates,
            "axisLabel": {"fontSize": ChartOptionsBuilder.get_font_size(user_agent)},
            "boundaryGap": False,
        },
        "yAxis": {
            "type": "value",
            "axisLabel": ChartOptionsBuilder.get_currency_axis_label(user_agent, currency),
            "axisLine": {"onZero": True},
            "splitLine": {"show": False},
        },
        "dataZoom": [
            {
                "type": "slider",
                "show": True,
                "start": 0,
                "end": 100,
                "height": 20,
                "bottom": "2%",
                "handleSize": "110%",
                "handleStyle": {"color": "#005eaa"},
                "textStyle": {"fontSize": ChartOptionsBuilder.get_font_size(user_agent)},
                "borderColor": "transparent",
                "backgroundColor": "#f0f0f0",
                "fillerColor": "rgba(0, 94, 170, 0.2)",
                "dataBackground": {"lineStyle": {"color": "#005eaa", "opacity": 0.5}},
                "selectedDataBackground": {"lineStyle": {"color": "#005eaa"}},
            },
            {
                "type": "inside",
                "start": 0,
                "end": 100,
                "zoomOnMouseWheel": True,
                "moveOnMouseMove": True,
                "moveOnMouseWheel": False,
            },
        ],
        "series": series,
    }
