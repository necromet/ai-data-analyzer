# Starry Night theme colors from index.css
THEME_COLORS = ['#5b51d8', '#f2c14e', '#a0b4d4', '#c0bfcc', '#4a3a45']

def echarts_line(x_column: str, y_column: str, query_result: dict, title: str = None, x_axis_name: str = None, y_axis_name: str = None, x_axis_type: str = None, y_axis_type: str = None) -> dict:
    """Generate line charts for echarts.js using the provided query result data.
    
    Args:
        x_column: Column name for x-axis
        y_column: Column name for y-axis
        query_result: Query result dict with 'data' key containing list of row dicts
        title: Optional chart title
        x_axis_name: Optional display name for x-axis
        y_axis_name: Optional display name for y-axis
        x_axis_type: Optional axis scale type ("category", "value", "time", "log")
        y_axis_type: Optional axis scale type ("category", "value", "time", "log")
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    data = query_result["data"]
    x_data = [row.get(x_column) for row in data]
    y_data = [row.get(y_column) for row in data]
    
    config = {
      "color": THEME_COLORS,
      "grid": {
        "top": 70,
        "bottom": 80,
        "containLabel": True
      },
      "dataZoom": [
        {"type": "inside"},
        {"type": "slider", "bottom": 10}
      ],
      "xAxis": {
        "type": x_axis_type or "category",
        "data": x_data
      },
      "yAxis": {
        "type": y_axis_type or "value"
      },
      "series": [
        {
          "data": y_data,
          "type": "line"
        }
      ],
      "tooltip": {
        "trigger": "axis"
      }
    }
    
    if title:
        config["title"] = {"text": title, "left": "center", "top": 5}
    if x_axis_name:
        config["xAxis"]["name"] = x_axis_name
    if y_axis_name:
        config["yAxis"]["name"] = y_axis_name
    if len(data) > 500:
        for s in config["series"]:
            s["large"] = True
            s["largeThreshold"] = 500
    
    return config


def echarts_area(x_column: str, y_column: str, query_result: dict, title: str = None, x_axis_name: str = None, y_axis_name: str = None, x_axis_type: str = None, y_axis_type: str = None) -> dict:
    """Generate area charts for echarts.js using the provided query result data.
    
    Args:
        x_column: Column name for x-axis
        y_column: Column name for y-axis
        query_result: Query result dict with 'data' key containing list of row dicts
        title: Optional chart title
        x_axis_name: Optional display name for x-axis
        y_axis_name: Optional display name for y-axis
        x_axis_type: Optional axis scale type ("category", "value", "time", "log")
        y_axis_type: Optional axis scale type ("category", "value", "time", "log")
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    data = query_result["data"]
    x_data = [row.get(x_column) for row in data]
    y_data = [row.get(y_column) for row in data]
    
    config = {
      "color": THEME_COLORS,
      "grid": {
        "top": 70,
        "bottom": 80,
        "containLabel": True
      },
      "dataZoom": [
        {"type": "inside"},
        {"type": "slider", "bottom": 10}
      ],
      "xAxis": {
        "type": x_axis_type or "category",
        "data": x_data
      },
      "yAxis": {
        "type": y_axis_type or "value"
      },
      "series": [
        {
          "data": y_data,
          "type": "line",
          "areaStyle": {}
        }
      ],
      "tooltip": {
        "trigger": "axis"
      }
    }
    
    if title:
        config["title"] = {"text": title, "left": "center", "top": 5}
    if x_axis_name:
        config["xAxis"]["name"] = x_axis_name
    if y_axis_name:
        config["yAxis"]["name"] = y_axis_name
    if len(data) > 500:
        for s in config["series"]:
            s["large"] = True
            s["largeThreshold"] = 500
    
    return config


def echarts_area_stacked(x_column: str, value_columns: list, query_result: dict, title: str = None, x_axis_name: str = None, y_axis_name: str = None, series_labels: dict = None, x_axis_type: str = None, y_axis_type: str = None) -> dict:
    """Generate stacked area charts for echarts.js using the provided query result data.
    
    Args:
        x_column: Column name for x-axis (category)
        value_columns: List of column names for stacked values
        query_result: Query result dict with 'data' key containing list of row dicts
        title: Optional chart title
        x_axis_name: Optional display name for x-axis
        y_axis_name: Optional display name for y-axis
        series_labels: Optional dict mapping column names to display labels
        x_axis_type: Optional axis scale type ("category", "value", "time", "log")
        y_axis_type: Optional axis scale type ("category", "value", "time", "log")
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
      "color": THEME_COLORS,
      "grid": {
        "top": 70,
        "bottom": 110,
        "containLabel": True
      },
      "dataZoom": [
        {"type": "inside"},
        {"type": "slider", "bottom": 10}
      ],
      "xAxis": {
        "type": x_axis_type or "category",
        "data": x_data
      },
      "yAxis": {
        "type": y_axis_type or "value"
      },
      "series": series,
      "legend": {
        "data": legend_labels,
        "bottom": 60
      },
      "tooltip": {
        "trigger": "axis"
      }
    }
    
    if title:
        config["title"] = {"text": title, "left": "center", "top": 5}
    if x_axis_name:
        config["xAxis"]["name"] = x_axis_name
    if y_axis_name:
        config["yAxis"]["name"] = y_axis_name
    if len(data) > 500:
        for s in config["series"]:
            s["large"] = True
            s["largeThreshold"] = 500
    
    return config
