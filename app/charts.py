from app.gsheet import get_sheet_data
from app.utils import parse_money
    
def build_net_worth_chart():
    data = get_sheet_data()
    net_worth = {}
    for row in data[1:]:
        net_worth[row[0]] = parse_money(row[1])
    option = {
        'xAxis': {
            'type': 'category',
            'data': list(net_worth.keys())
        },
        'yAxis': {
            'axisLabel': {
                ':formatter': 'value => "€ " + value'
            }
        },
        'series': [
            {
                'type': 'line',
                'data': list(net_worth.values()),
                'smooth': 'true'
            }
        ]
    }
    return option

def get_dashboard_data():
    raw_data = get_sheet_data()
    return raw_data