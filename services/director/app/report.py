"""GET /report, built entirely on the MongoDB Aggregation Framework: unwind
each asset's categories, sum spent/earned per category, then sort by earned
desc, spent asc, category asc. No aggregation logic runs in Python."""
from .extensions import assets_collection

REPORT_PIPELINE = [
    # An asset with N categories becomes N rows, so it counts once toward
    # every category it belongs to.
    {"$unwind": "$categories"},
    {
        "$group": {
            "_id": "$categories",
            "spent": {"$sum": "$buying_price"},
            # Only sold assets contribute to `earned` (selling_price is
            # always > 0 when present).
            "earned": {
                "$sum": {
                    "$cond": [
                        {"$gt": [{"$ifNull": ["$selling_price", 0]}, 0]},
                        "$selling_price",
                        0,
                    ]
                }
            },
        }
    },
    {"$project": {"_id": 0, "category": "$_id", "spent": 1, "earned": 1}},
    {"$sort": {"earned": -1, "spent": 1, "category": 1}},
]


def build_report():
    return list(assets_collection.aggregate(REPORT_PIPELINE))
