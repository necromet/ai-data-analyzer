# Starry Night theme colors from index.css
THEME_COLORS = ['#5b51d8', '#f2c14e', '#a0b4d4', '#c0bfcc', '#4a3a45']

def echarts_pie(name_column: str, value_column: str, title: str = "Distribution", query_result: dict = None, series_name: str = None) -> dict:
    """Generate pie charts for echarts.js using the provided query result data.
    
    Args:
        name_column: Column name for pie slice names
        value_column: Column name for pie slice values
        title: Chart title
        query_result: Query result dict with 'data' key containing list of row dicts
        series_name: Optional display name for the series (defaults to name_column)
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    data = query_result["data"]
    pie_data = [{"value": row.get(value_column), "name": row.get(name_column)} for row in data]
    
    display_name = series_name or name_column
    
    return {
        "color": THEME_COLORS,
        "title": {
            "text": title,
            "left": "center",
            "top": 5
        },
        "tooltip": {
            "trigger": "item"
        },
        "toolbox": {
            "show": True,
            "orient": "vertical",
            "top": "center",
            "right": 5,
            "feature": {
                "dataView": {"show": True, "readOnly": False},
                "restore": {"show": True},
                "saveAsImage": {"show": True}
            }
        },
        "legend": {
            "orient": "vertical",
            "left": "left"
        },
        "series": [
            {
                "name": display_name,
                "type": "pie",
                "sampling": "lttb",
                "radius": "50%",
                "data": pie_data,
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowOffsetX": 0,
                        "shadowColor": "rgba(0, 0, 0, 0.5)"
                    }
                }
            }
        ]
    }
