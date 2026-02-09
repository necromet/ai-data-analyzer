def echarts_bar(x_column: str, y_column: str, query_result: dict = None) -> dict:
    """Generate vertical bar charts for echarts.js using the provided query result data.
    
    Args:
        x_column: Column name for x-axis (categories)
        y_column: Column name for y-axis (values)
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
          "type": "bar"
        }
      ]
    }


def echarts_bar_horizontal(y_column: str, x_column: str, query_result: dict = None) -> dict:
    """Generate horizontal bar charts for echarts.js using the provided query result data.
    
    Args:
        y_column: Column name for y-axis (categories)
        x_column: Column name for x-axis (values)
        query_result: Query result dict with 'data' key containing list of row dicts
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    data = query_result["data"]
    y_data = [row.get(y_column) for row in data]
    x_data = [row.get(x_column) for row in data]
    
    return {
      "xAxis": {
        "type": "value"
      },
      "yAxis": {
        "type": "category",
        "data": y_data
      },
      "series": [
        {
          "data": x_data,
          "type": "bar"
        }
      ]
    }


def echarts_bar_stacked(category_column: str, value_columns: list, query_result: dict = None, title: str = "Stacked Bar Chart") -> dict:
    """Generate stacked bar charts for echarts.js using the provided query result data.
    Multiple series are stacked on top of each other.
    
    Args:
        category_column: Column name for categories (x-axis)
        value_columns: List of column names for stacked values
        query_result: Query result dict with 'data' key containing list of row dicts
        title: Chart title
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    data = query_result["data"]
    categories = [row.get(category_column) for row in data]
    
    series = []
    for col in value_columns:
        series.append({
            "name": col,
            "type": "bar",
            "stack": "total",
            "data": [row.get(col, 0) for row in data]
        })
    
    return {
        "title": {
            "text": title,
            "left": "center"
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "shadow"
            }
        },
        "legend": {
            "data": value_columns,
            "top": "bottom"
        },
        "xAxis": {
            "type": "category",
            "data": categories
        },
        "yAxis": {
            "type": "value"
        },
        "series": series
    }


def echarts_bar_grouped(category_column: str, value_columns: list, query_result: dict = None, title: str = "Grouped Bar Chart") -> dict:
    """Generate grouped/clustered bar charts for echarts.js using the provided query result data.
    Multiple series are displayed side by side.
    
    Args:
        category_column: Column name for categories (x-axis)
        value_columns: List of column names for grouped values
        query_result: Query result dict with 'data' key containing list of row dicts
        title: Chart title
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    data = query_result["data"]
    categories = [row.get(category_column) for row in data]
    
    series = []
    for col in value_columns:
        series.append({
            "name": col,
            "type": "bar",
            "data": [row.get(col, 0) for row in data]
        })
    
    return {
        "title": {
            "text": title,
            "left": "center"
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "shadow"
            }
        },
        "legend": {
            "data": value_columns,
            "top": "bottom"
        },
        "xAxis": {
            "type": "category",
            "data": categories
        },
        "yAxis": {
            "type": "value"
        },
        "series": series
    }
