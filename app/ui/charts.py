# app/ui/charts.py
from typing import Dict, Any

def create_net_worth_chart_options(net_worth_data: Dict[str, Any], user_agent: str) -> Dict[str, Any]:
    """
    Generates ECharts options for a net worth line chart.
    
    Args:
        net_worth_data: A dictionary with 'dates' and 'values' keys.
    """
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
    """
    Generates ECharts options for a sunburst asset vs liabilities chart.
    
    Args:
        net_worth_data: A dictionary with 'dates' and 'values' keys.
    """
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