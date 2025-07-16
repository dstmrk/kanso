# app/ui/charts.py
from typing import Dict, Any

def create_net_worth_chart_options(net_worth_data: Dict[str, Any], user_agent: str) -> Dict[str, Any]:
    """
    Generates ECharts options for a net worth line chart.
    
    Args:
        net_worth_data: A dictionary with 'dates' and 'values' keys.
    """
    return {
        "tooltip": {"trigger": "axis"},
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