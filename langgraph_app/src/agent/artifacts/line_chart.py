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


def echarts_line_smooth(x_column: str, y_column: str, query_result: dict) -> dict:
    """Generate smoothed line charts for echarts.js using the provided query result data.
    
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
          "type": "line",
          "smooth": True
        }
      ]
    }


def echarts_line_stacked(x_column: str, value_columns: list, query_result: dict) -> dict:
    """Generate stacked line charts for echarts.js using the provided query result data.
    
    Args:
        x_column: Column name for x-axis (category)
        value_columns: List of column names for stacked values
        query_result: Query result dict with 'data' key containing list of row dicts
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    data = query_result["data"]
    x_data = [row.get(x_column) for row in data]
    
    series = []
    for col in value_columns:
        y_data = [row.get(col) for row in data]
        series.append({
            "name": col,
            "data": y_data,
            "type": "line",
            "stack": "Total"
        })
    
    return {
      "xAxis": {
        "type": "category",
        "data": x_data
      },
      "yAxis": {
        "type": "value"
      },
      "series": series,
      "legend": {
        "data": value_columns
      }
    }


def echarts_area(x_column: str, y_column: str, query_result: dict) -> dict:
    """Generate area charts for echarts.js using the provided query result data.
    
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
          "type": "line",
          "areaStyle": {}
        }
      ]
    }


def echarts_area_stacked(x_column: str, value_columns: list, query_result: dict) -> dict:
    """Generate stacked area charts for echarts.js using the provided query result data.
    
    Args:
        x_column: Column name for x-axis (category)
        value_columns: List of column names for stacked values
        query_result: Query result dict with 'data' key containing list of row dicts
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    data = query_result["data"]
    x_data = [row.get(x_column) for row in data]
    
    series = []
    for col in value_columns:
        y_data = [row.get(col) for row in data]
        series.append({
            "name": col,
            "data": y_data,
            "type": "line",
            "stack": "Total",
            "areaStyle": {}
        })
    
    return {
      "xAxis": {
        "type": "category",
        "data": x_data
      },
      "yAxis": {
        "type": "value"
      },
      "series": series,
      "legend": {
        "data": value_columns
      }
    }
