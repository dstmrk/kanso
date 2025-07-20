from typing import Dict, Any

def create_net_worth_chart_options(net_worth_data: Dict[str, Any], user_agent: str) -> Dict[str, Any]:
    return {
        "tooltip": {
            "trigger": "axis",
            ":valueFormatter": 'function(value) { return "€ " + value.toFixed(2).toLocaleString("it-IT") }'
            },
        "grid": {"left": '15%', "right": '5%', "top": '10%', "bottom": '20%'},
        "xAxis": {
            "type": "category",
            "data": net_worth_data.get('dates', []),
            "axisLabel": {
                "fontSize": 8 if user_agent == "mobile" else 12
                }
        },
        "yAxis": {
            "type": "value",
            "axisLabel": {
                "formatter": '€ {value}',
                "fontSize": 8 if user_agent == "mobile" else 12
                }
        },
        "series": [{
            "name": "Net Worth",
            "type": "line",
            "smooth": True,
            "data": net_worth_data.get('values', []),
            "areaStyle": {}
        }]
    }
    
def create_asset_vs_liabilities_chart(chart_data: Dict[str, Any], user_agent: str) -> Dict[str, Any]:
    data = []
    for category_name, items in chart_data.items():
        category = {
            'name': category_name,
            'children': []
        }
        for item_name, value in items.items():
            category['children'].append({
                'name': item_name,
                'value': abs(value)
            })
        data.append(category)
    return {
        "tooltip": {
            "trigger": 'item',
            ":valueFormatter": 'function(value) { return "€ " + value.toFixed(2).toLocaleString("it-IT") }'
        },
        "grid": {"left": '15%', "right": '5%', "top": '10%', "bottom": '20%'},
        "color": ["#FFFFFF","#2b821d", "#c12e34"],
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
                "color": "#ffffff",
                "fontSize": 8 if user_agent == "mobile" else 12
            }
        }
    }

def create_cash_flow_options(cash_flow_data: Dict[str, float], user_agent: str) -> Dict[str, Any]:
    income = cash_flow_data.get('Income', 0)
    savings = cash_flow_data.get('Savings', 0)
    expenses_total = cash_flow_data.get('Expenses', 0)

    expense_categories = {k: v for k, v in cash_flow_data.items() if k not in ['Income', 'Savings', 'Expenses']}
    nodes = [{'name': 'Income'}, {'name': 'Savings'}, {'name': 'Expenses'}] + [
        {'name': category} for category in expense_categories
    ]

    links = [
        {'source': 'Income', 'target': 'Savings', 'value': round(savings, 2)},
        {'source': 'Income', 'target': 'Expenses', 'value': round(expenses_total, 2)},
    ] + [
        {'source': 'Expenses', 'target': category, 'value': round(amount, 2)}
        for category, amount in expense_categories.items()
    ]

    options = {
        'tooltip': {
            'trigger': 'item',
            'triggerOn': 'mousemove',
            ":valueFormatter": 'function(value) { return "€ " + value.toFixed(2).toLocaleString("it-IT")}'
            },
        'series': [{
            'type': 'sankey',
            'layout': 'none',
            'data': nodes,
            'links': links,
            'emphasis': {'focus': 'adjacency'},
            'lineStyle': {'color': 'source', 'curveness': 0.5},
            'label': {'fontSize': 8 if user_agent == "mobile" else 12}
        }]
    }
    return options
