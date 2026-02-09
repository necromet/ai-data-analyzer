def echarts_pie(name_column: str, value_column: str, title: str = "Distribution", query_result: dict = None) -> dict:
    """Generate pie charts for echarts.js using the provided query result data.
    
    Args:
        name_column: Column name for pie slice names
        value_column: Column name for pie slice values
        title: Chart title
        query_result: Query result dict with 'data' key containing list of row dicts
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    data = query_result["data"]
    pie_data = [{"value": row.get(value_column), "name": row.get(name_column)} for row in data]
    
    return {
        "title": {
            "text": title,
            "left": "center"
        },
        "tooltip": {
            "trigger": "item"
        },
        "legend": {
            "orient": "vertical",
            "left": "left"
        },
        "series": [
            {
                "name": name_column,
                "type": "pie",
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
