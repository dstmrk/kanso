# app/ui/charts.py
from typing import Dict, Any

# This function is now perfectly aligned with the output of our calculator
def create_net_worth_chart_options(net_worth_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates ECharts options for a net worth line chart.
    
    Args:
        net_worth_data: A dictionary with 'dates' and 'values' keys.
    """
    return {
        "title": {"text": "Net Worth Over Time"},
        "tooltip": {"trigger": "axis"},
        # "grid": {"left": "10%", "right": "5%", "bottom": "10%"}, # Adjust grid for better label display
        "xAxis": {
            "type": "category",
            "data": net_worth_data.get('dates', []), # Use .get for safety
        },
        "yAxis": {
            "type": "value",
            "axisLabel": {"formatter": '€ {value}'} # Format the y-axis labels
        },
        "series": [{
            "name": "Net Worth",
            "type": "line",
            "smooth": True,
            "data": net_worth_data.get('values', []), # Use .get for safety
        }],
        "dataZoom": [ # Add a slider for zooming and scrolling
            {"type": "slider", "start": 0, "end": 100},
            {"type": "inside", "start": 0, "end": 100}
        ],
    }

# The expense chart function can be removed for now if you are not using it.
# def create_expense_pie_chart_options(...)