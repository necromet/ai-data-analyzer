def echarts_line(x_column: str, y_column: str, query_result: dict) -> dict:
    """Generate line charts for echarts.js using the provided query result data.
    
    Args:
        x_column: Column name for x-axis
        y_column: Column name for y-axis
        query_result: Query result dict with 'data' key containing list of row dicts
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    data = query_result["data"]
    x_data = [row.get(x_column) for row in data]
    y_data = [row.get(y_column) for row in data]
    
    return {
      "xAxis": {
        "type": "category",
        "data": x_data
      },
      "yAxis": {
        "type": "value"
      },
      "series": [
        {
          "data": y_data,
          "type": "line"
        }
      ]
    }
