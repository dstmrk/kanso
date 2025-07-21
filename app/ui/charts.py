from typing import Dict, List, Any

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
                "fontSize": 8 if user_agent == "mobile" else 12,
                ':formatter': 'function(value) { return "€ " + value.toFixed(0).toLocaleString("it-IT") }'
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
    savings = cash_flow_data.get('Savings', 0)
    expenses_total = cash_flow_data.get('Expenses', 0)

    expense_categories = {k: v for k, v in cash_flow_data.items() if k not in ['Savings', 'Expenses']}
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
            ':valueFormatter': 'function(value) { return "€ " + value.toFixed(2).toLocaleString("it-IT")}'
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

def create_avg_expenses_options(expenses_data: Dict[str, float], user_agent: str) -> Dict[str, Any]:
    expense_categories = {k: v for k, v in expenses_data.items()}
    data = [
        {'name': category, 'value': value} for category, value in expense_categories.items()
    ]
    options = {
       'tooltip': {
            'trigger': 'item',
            ':valueFormatter': 'function(value) { return "€ " + value.toFixed(2).toLocaleString("it-IT")}'
        },
       'series': {
           'type': 'pie',
           'radius': [ 50, '80%'],
           'avoidLabelOverlap': 'false',
           'itemStyle': {
               'borderRadius': 5,
               'borderColor': '#fff',
               'borderWidth': 1
               },
           'label': {
               'minAngle': 5,
               'fontSize': 8 if user_agent == "mobile" else 12
               },
           'labelLine': {'show': 'false'},
           'data': data
           }
       }
    return options

def create_income_vs_expenses_options(income_vs_expenses_data: Dict[str, List], user_agent: str) -> Dict[str, Any]:
    options = {
        'tooltip': {
            'trigger': 'axis',
            ':valueFormatter': 'function(value) { return "€ " + value.toFixed(2).toLocaleString("it-IT") }'
            },
        'grid': {'left': '15%', 'right': '5%', 'top': '10%', 'bottom': '20%'},
        'color': ["#2b821d", "#c12e34"],
        'xAxis': {
            'type': 'category',
            'axisLabel': {
                'fontSize': 8 if user_agent == "mobile" else 12
            },
            'data': income_vs_expenses_data['dates'],
            'axisTick': {'alignWithLabel': True}
        },
        'yAxis': {
            'type': 'value',
            'axisLabel': {
                'fontSize': 8 if user_agent == "mobile" else 12,
                ':formatter': 'function(value) { return "€ " + value.toFixed(0).toLocaleString("it-IT") }'
            },
            'axisLine': {'onZero': True},
            'splitLine': {'show': False}
            },
        'series': [
            {
                'name': 'Income',
                'type': 'bar',
                'stack': 'total',
                'data': income_vs_expenses_data['incomes'],
                'emphasis': {'focus': 'series'}
            },
            {
                'name': 'Expenses',
                'type': 'bar',
                'stack': 'total',
                'data': income_vs_expenses_data['expenses'],
                'emphasis': {'focus': 'series'}
            }
            ]
        }
    return options