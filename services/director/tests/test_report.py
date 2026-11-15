import datetime

from app.report import build_report


def test_report_sums_per_category_and_sorts(assets):
    day = datetime.datetime(2026, 1, 1)
    assets.insert_many([
        {"name": "A", "categories": ["Tech", "Finance"], "buying_price": 100, "buying_date": day,
         "selling_price": 300, "selling_date": day, "info": {}},
        {"name": "B", "categories": ["Tech"], "buying_price": 50, "buying_date": day, "info": {}},
        {"name": "C", "categories": ["Energy"], "buying_price": 10, "buying_date": day, "info": {}},
        {"name": "D", "categories": ["Art"], "buying_price": 10, "buying_date": day, "info": {}},
    ])

    assert build_report() == [
        {"category": "Finance", "spent": 100, "earned": 300},
        {"category": "Tech", "spent": 150, "earned": 300},
        {"category": "Art", "spent": 10, "earned": 0},
        {"category": "Energy", "spent": 10, "earned": 0},
    ]
