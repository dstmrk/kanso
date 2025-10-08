class ChartOptionsBuilder:
    """Centralized chart options builder with common formatting."""
    
    @staticmethod
    def get_font_size(user_agent):
        """Get font size based on user agent."""
        return 8 if user_agent == "mobile" else 12
    
    @staticmethod
    def get_common_tooltip():
        """Get common tooltip configuration."""
        return {
            ':valueFormatter': 'function(value) { return "€ " + value.toFixed(2).toLocaleString("it-IT") }'
        }
    
    @staticmethod
    def get_common_grid():
        """Get common grid configuration."""
        return {"left": '15%', "right": '5%', "top": '10%', "bottom": '20%'}
    
    @staticmethod
    def get_currency_axis_label(user_agent):
        """Get currency formatted axis label."""
        return {
            "fontSize": ChartOptionsBuilder.get_font_size(user_agent),
            ':formatter': 'function(value) { return "€ " + value.toFixed(0).toLocaleString("it-IT") }'
        }


def create_net_worth_chart_options(net_worth_data, user_agent):
    return {
        "tooltip": {
            "trigger": "axis",
            **ChartOptionsBuilder.get_common_tooltip()
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
            "axisLabel": ChartOptionsBuilder.get_currency_axis_label(user_agent)
        },
        "series": [{
            "name": "Net Worth",
            "type": "line",
            "smooth": True,
            "data": net_worth_data.get('values', []),
            "areaStyle": {}
        }]
    }

def create_asset_vs_liabilities_chart(chart_data, user_agent):
    # Convert ObservableDict to regular dict (NiceGUI compatibility)
    chart_data = dict(chart_data)
    for key in chart_data:
        if hasattr(chart_data[key], 'items'):
            chart_data[key] = dict(chart_data[key])
            # Handle nested dicts
            for subkey in list(chart_data[key].keys()):
                if hasattr(chart_data[key][subkey], 'items'):
                    chart_data[key][subkey] = dict(chart_data[key][subkey])

    data = []
    for category_name, items in chart_data.items():
        category = {
            'name': category_name,
            'children': []
        }
        for item_name, value in items.items():
            # Check if value is a dict (nested structure from MultiIndex)
            if isinstance(value, dict):
                # MultiIndex case: create subcategory with children
                subcategory = {
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
            **ChartOptionsBuilder.get_common_tooltip()
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

def create_cash_flow_options(cash_flow_data, user_agent):
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
            **ChartOptionsBuilder.get_common_tooltip()
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

def create_avg_expenses_options(expenses_data, user_agent):
    data = [
        {'name': category, 'value': value} 
        for category, value in expenses_data.items()
    ]
    
    return {
        'tooltip': {
            'trigger': 'item',
            **ChartOptionsBuilder.get_common_tooltip()
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

def create_income_vs_expenses_options(income_vs_expenses_data, user_agent):
    return {
        'legend': {'data': ['Income', 'Expenses']},
        'tooltip': {
            'trigger': 'axis',
            **ChartOptionsBuilder.get_common_tooltip()
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
            'axisLabel': ChartOptionsBuilder.get_currency_axis_label(user_agent),
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