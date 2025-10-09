from typing import Dict, Any, Literal, List

class ChartOptionsBuilder:
    """Centralized chart options builder with common formatting."""

    @staticmethod
    def get_font_size(user_agent: Literal["mobile", "desktop"]) -> int:
        """Get font size based on user agent."""
        return 8 if user_agent == "mobile" else 12

    @staticmethod
    def get_common_tooltip(currency: str = 'USD') -> Dict[str, str]:
        """Get common tooltip configuration with currency formatting."""
        return {
            ':valueFormatter': f'function(value) {{ return value.toLocaleString(undefined, {{style: "currency", currency: "{currency}", minimumFractionDigits: 2, maximumFractionDigits: 2}}) }}'
        }

    @staticmethod
    def get_common_grid() -> Dict[str, str]:
        """Get common grid configuration."""
        return {"left": '15%', "right": '5%', "top": '10%', "bottom": '20%'}

    @staticmethod
    def get_currency_axis_label(user_agent: Literal["mobile", "desktop"], currency: str = 'USD') -> Dict[str, Any]:
        """Get currency formatted axis label."""
        return {
            "fontSize": ChartOptionsBuilder.get_font_size(user_agent),
            ':formatter': f'function(value) {{ return value.toLocaleString(undefined, {{style: "currency", currency: "{currency}", maximumFractionDigits: 0}}) }}'
        }


def create_net_worth_chart_options(net_worth_data: Dict[str, Any], user_agent: Literal["mobile", "desktop"], currency: str = 'USD') -> Dict[str, Any]:
    return {
        "tooltip": {
            "trigger": "axis",
            **ChartOptionsBuilder.get_common_tooltip(currency)
        },
        "grid": ChartOptionsBuilder.get_common_grid(),
        "xAxis": {
            "type": "category",
            "data": net_worth_data.get('dates', []),
            "axisLabel": {
                "fontSize": ChartOptionsBuilder.get_font_size(user_agent)
            }
        },
        "yAxis": {
            "type": "value",
            "axisLabel": ChartOptionsBuilder.get_currency_axis_label(user_agent, currency)
        },
        "series": [{
            "name": "Net Worth",
            "type": "line",
            "smooth": True,
            "data": net_worth_data.get('values', []),
            "areaStyle": {}
        }]
    }

def create_asset_vs_liabilities_chart(chart_data: Dict[str, Any], user_agent: Literal["mobile", "desktop"], currency: str = 'USD') -> Dict[str, Any]:
    # Convert ObservableDict to regular dict (NiceGUI compatibility)
    chart_data = dict(chart_data)
    for key in chart_data:
        if hasattr(chart_data[key], 'items'):
            chart_data[key] = dict(chart_data[key])
            # Handle nested dicts
            for subkey in list(chart_data[key].keys()):
                if hasattr(chart_data[key][subkey], 'items'):
                    chart_data[key][subkey] = dict(chart_data[key][subkey])

    data: List[Dict[str, Any]] = []
    for category_name, items in chart_data.items():
        category: Dict[str, Any] = {
            'name': category_name,
            'children': []
        }
        for item_name, value in items.items():
            # Check if value is a dict (nested structure from MultiIndex)
            if isinstance(value, dict):
                # MultiIndex case: create subcategory with children
                subcategory: Dict[str, Any] = {
                    'name': item_name,
                    'children': []
                }
                for sub_item_name, sub_value in value.items():
                    subcategory['children'].append({
                        'name': sub_item_name,
                        'value': abs(sub_value)
                    })
                category['children'].append(subcategory)
            else:
                # Single header case: direct value
                category['children'].append({
                    'name': item_name,
                    'value': abs(value)
                })
        data.append(category)

    return {
        "tooltip": {
            "trigger": 'item',
            **ChartOptionsBuilder.get_common_tooltip(currency)
        },
        "grid": ChartOptionsBuilder.get_common_grid(),
        "color": ["#777777","#2b821d", "#c12e34"],
        "series": {
            "type": "sunburst",
            "data": data,
            "radius": [50, '80%'],
            "itemStyle": {
                "borderRadius": 5,
                "borderWidth": 1
            },
            "label": {
                "show": "true",
                "rotate": '0',
                "minAngle": 5,
                "color": "#dddddd",
                "fontSize": ChartOptionsBuilder.get_font_size(user_agent)
            }
        }
    }

def create_cash_flow_options(cash_flow_data: Dict[str, float], user_agent: Literal["mobile", "desktop"], currency: str = 'USD') -> Dict[str, Any]:
    savings = cash_flow_data.get('Savings', 0)
    expenses_total = cash_flow_data.get('Expenses', 0)
    expense_categories = {k: v for k, v in cash_flow_data.items() if k not in ['Savings', 'Expenses']}

    colors = [
        "#e6b600", "#95706d", "#9bbc99", "#8c6ac4", "#ea7e53",
        "#0098d9", "#e098c7", "#73c0de", "#3fb27f"
    ]

    nodes = [
        {'name': 'Income', 'itemStyle': {'color': '#2b821d'}},
        {'name': 'Savings', 'itemStyle': {'color': '#005eaa'}},
        {'name': 'Expenses', 'itemStyle': {'color': '#c12e34'}}
    ] + [
        {'name': category, 'itemStyle': {'color': colors[i % len(colors)]}}
        for i, category in enumerate(expense_categories)
    ]

    links = [
        {'source': 'Income', 'target': 'Savings', 'value': round(savings, 2)},
        {'source': 'Income', 'target': 'Expenses', 'value': round(expenses_total, 2)},
    ] + [
        {'source': 'Expenses', 'target': category, 'value': round(amount, 2)}
        for category, amount in expense_categories.items()
    ]

    return {
        'tooltip': {
            'trigger': 'item',
            'triggerOn': 'mousemove',
            **ChartOptionsBuilder.get_common_tooltip(currency)
        },
        'series': [{
            'type': 'sankey',
            'layout': 'none',
            'data': nodes,
            'links': links,
            'emphasis': {'focus': 'adjacency'},
            'lineStyle': {'color': 'source', 'curveness': 0.3},
            'label': {'fontSize': ChartOptionsBuilder.get_font_size(user_agent)}
        }]
    }

def create_avg_expenses_options(expenses_data: Dict[str, float], user_agent: Literal["mobile", "desktop"], currency: str = 'USD') -> Dict[str, Any]:
    data = [
        {'name': category, 'value': value}
        for category, value in expenses_data.items()
    ]

    return {
        'tooltip': {
            'trigger': 'item',
            **ChartOptionsBuilder.get_common_tooltip(currency)
        },
        'series': {
            'type': 'pie',
            'radius': [50, '80%'],
            'avoidLabelOverlap': 'false',
            'itemStyle': {
                'borderRadius': 5,
                'borderColor': '#fff',
                'borderWidth': 1
            },
            'label': {
                'minAngle': 5,
                'fontSize': ChartOptionsBuilder.get_font_size(user_agent)
            },
            'labelLine': {'show': 'false'},
            'data': data,
            'emphasis': {'focus': 'self'}
        }
    }

def create_income_vs_expenses_options(income_vs_expenses_data: Dict[str, Any], user_agent: Literal["mobile", "desktop"], currency: str = 'USD') -> Dict[str, Any]:
    return {
        'legend': {'data': ['Income', 'Expenses']},
        'tooltip': {
            'trigger': 'axis',
            **ChartOptionsBuilder.get_common_tooltip(currency)
        },
        'grid': ChartOptionsBuilder.get_common_grid(),
        'color': ["#2b821d", "#c12e34"],
        'xAxis': {
            'type': 'category',
            'axisLabel': {
                'fontSize': ChartOptionsBuilder.get_font_size(user_agent)
            },
            'data': income_vs_expenses_data['dates'],
            'axisTick': {'alignWithLabel': True}
        },
        'yAxis': {
            'type': 'value',
            'axisLabel': ChartOptionsBuilder.get_currency_axis_label(user_agent, currency),
            'axisLine': {'onZero': True},
            'splitLine': {'show': False}
        },
        'series': [
            {
                'name': 'Income',
                'type': 'bar',
                'stack': 'total',
                'data': income_vs_expenses_data['incomes'],
                'emphasis': {'focus': 'self'}
            },
            {
                'name': 'Expenses',
                'type': 'bar',
                'stack': 'total',
                'data': income_vs_expenses_data['expenses'],
                'emphasis': {'focus': 'self'}
            }
        ]
    }