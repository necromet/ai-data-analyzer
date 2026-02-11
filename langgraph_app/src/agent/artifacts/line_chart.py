def echarts_line(x_column: str, y_column: str, query_result: dict, title: str = None, x_axis_name: str = None, y_axis_name: str = None) -> dict:
    """Generate line charts for echarts.js using the provided query result data.
    
    Args:
        x_column: Column name for x-axis
        y_column: Column name for y-axis
        query_result: Query result dict with 'data' key containing list of row dicts
        title: Optional chart title
        x_axis_name: Optional display name for x-axis
        y_axis_name: Optional display name for y-axis
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    data = query_result["data"]
    x_data = [row.get(x_column) for row in data]
    y_data = [row.get(y_column) for row in data]
    
    config = {
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
    
    if title:
        config["title"] = {"text": title, "left": "center"}
    if x_axis_name:
        config["xAxis"]["name"] = x_axis_name
    if y_axis_name:
        config["yAxis"]["name"] = y_axis_name
    
    return config


def echarts_line_smooth(x_column: str, y_column: str, query_result: dict, title: str = None, x_axis_name: str = None, y_axis_name: str = None) -> dict:
    """Generate smoothed line charts for echarts.js using the provided query result data.
    
    Args:
        x_column: Column name for x-axis
        y_column: Column name for y-axis
        query_result: Query result dict with 'data' key containing list of row dicts
        title: Optional chart title
        x_axis_name: Optional display name for x-axis
        y_axis_name: Optional display name for y-axis
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    data = query_result["data"]
    x_data = [row.get(x_column) for row in data]
    y_data = [row.get(y_column) for row in data]
    
    config = {
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
    
    if title:
        config["title"] = {"text": title, "left": "center"}
    if x_axis_name:
        config["xAxis"]["name"] = x_axis_name
    if y_axis_name:
        config["yAxis"]["name"] = y_axis_name
    
    return config


def echarts_line_stacked(x_column: str, value_columns: list, query_result: dict, title: str = None, x_axis_name: str = None, y_axis_name: str = None, series_labels: dict = None) -> dict:
    """Generate stacked line charts for echarts.js using the provided query result data.
    
    Args:
        x_column: Column name for x-axis (category)
        value_columns: List of column names for stacked values
        query_result: Query result dict with 'data' key containing list of row dicts
        title: Optional chart title
        x_axis_name: Optional display name for x-axis
        y_axis_name: Optional display name for y-axis
        series_labels: Optional dict mapping column names to display labels
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    if not series_labels:
        series_labels = {}
    
    data = query_result["data"]
    x_data = [row.get(x_column) for row in data]
    
    legend_labels = [series_labels.get(col, col) for col in value_columns]
    
    series = []
    for col in value_columns:
        y_data = [row.get(col) for row in data]
        series.append({
            "name": series_labels.get(col, col),
            "data": y_data,
            "type": "line",
            "stack": "Total"
        })
    
    config = {
      "xAxis": {
        "type": "category",
        "data": x_data
      },
      "yAxis": {
        "type": "value"
      },
      "series": series,
      "legend": {
        "data": legend_labels
      }
    }
    
    if title:
        config["title"] = {"text": title, "left": "center"}
    if x_axis_name:
        config["xAxis"]["name"] = x_axis_name
    if y_axis_name:
        config["yAxis"]["name"] = y_axis_name
    
    return config


def echarts_area(x_column: str, y_column: str, query_result: dict, title: str = None, x_axis_name: str = None, y_axis_name: str = None) -> dict:
    """Generate area charts for echarts.js using the provided query result data.
    
    Args:
        x_column: Column name for x-axis
        y_column: Column name for y-axis
        query_result: Query result dict with 'data' key containing list of row dicts
        title: Optional chart title
        x_axis_name: Optional display name for x-axis
        y_axis_name: Optional display name for y-axis
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    data = query_result["data"]
    x_data = [row.get(x_column) for row in data]
    y_data = [row.get(y_column) for row in data]
    
    config = {
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
    
    if title:
        config["title"] = {"text": title, "left": "center"}
    if x_axis_name:
        config["xAxis"]["name"] = x_axis_name
    if y_axis_name:
        config["yAxis"]["name"] = y_axis_name
    
    return config


def echarts_area_stacked(x_column: str, value_columns: list, query_result: dict, title: str = None, x_axis_name: str = None, y_axis_name: str = None, series_labels: dict = None) -> dict:
    """Generate stacked area charts for echarts.js using the provided query result data.
    
    Args:
        x_column: Column name for x-axis (category)
        value_columns: List of column names for stacked values
        query_result: Query result dict with 'data' key containing list of row dicts
        title: Optional chart title
        x_axis_name: Optional display name for x-axis
        y_axis_name: Optional display name for y-axis
        series_labels: Optional dict mapping column names to display labels
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    if not series_labels:
        series_labels = {}
    
    data = query_result["data"]
    x_data = [row.get(x_column) for row in data]
    
    legend_labels = [series_labels.get(col, col) for col in value_columns]
    
    series = []
    for col in value_columns:
        y_data = [row.get(col) for row in data]
        series.append({
            "name": series_labels.get(col, col),
            "data": y_data,
            "type": "line",
            "stack": "Total",
            "areaStyle": {}
        })
    
    config = {
      "xAxis": {
        "type": "category",
        "data": x_data
      },
      "yAxis": {
        "type": "value"
      },
      "series": series,
      "legend": {
        "data": legend_labels
      }
    }
    
    if title:
        config["title"] = {"text": title, "left": "center"}
    if x_axis_name:
        config["xAxis"]["name"] = x_axis_name
    if y_axis_name:
        config["yAxis"]["name"] = y_axis_name
    
    return config
