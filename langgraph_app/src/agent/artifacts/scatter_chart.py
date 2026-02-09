def echarts_scatter(x_column: str, y_column: str, title: str = "Scatter Plot", query_result: dict = None) -> dict:
    """Generate scatter plots for echarts.js using the provided query result data.
    
    Args:
        x_column: Column name for x-axis
        y_column: Column name for y-axis
        title: Chart title
        query_result: Query result dict with 'data' key containing list of row dicts
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    data = query_result["data"]
    scatter_data = [[row.get(x_column), row.get(y_column)] for row in data]
    
    return {
        "title": {
            "text": title,
            "left": "center"
        },
        "tooltip": {
            "trigger": "item"
        },
        "xAxis": {
            "type": "value"
        },
        "yAxis": {
            "type": "value"
        },
        "series": [
            {
                "symbolSize": 10,
                "data": scatter_data,
                "type": "scatter"
            }
        ]
    }
