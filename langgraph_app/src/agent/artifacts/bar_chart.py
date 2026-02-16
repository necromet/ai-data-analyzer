# Starry Night theme colors from index.css
THEME_COLORS = ['#5b51d8', '#f2c14e', '#a0b4d4', '#c0bfcc', '#4a3a45']

def echarts_bar(x_column: str, y_column: str, query_result: dict = None, title: str = None, x_axis_name: str = None, y_axis_name: str = None) -> dict:
    """Generate vertical bar charts for echarts.js using the provided query result data.
    
    Args:
        x_column: Column name for x-axis (categories)
        y_column: Column name for y-axis (values)
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
      "color": THEME_COLORS,
      "tooltip": {
        "trigger": "axis",
        "axisPointer": {
          "type": "shadow"
        }
      },
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
          "type": "bar",
          "showBackground": True,
          "backgroundStyle": {
            "color": "rgba(180, 180, 180, 0.2)"
          }
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


def echarts_bar_horizontal(y_column: str, x_column: str, query_result: dict = None, title: str = None, x_axis_name: str = None, y_axis_name: str = None) -> dict:
    """Generate horizontal bar charts for echarts.js using the provided query result data.
    
    Args:
        y_column: Column name for y-axis (categories)
        x_column: Column name for x-axis (values)
        query_result: Query result dict with 'data' key containing list of row dicts
        title: Optional chart title
        x_axis_name: Optional display name for x-axis (value axis)
        y_axis_name: Optional display name for y-axis (category axis)
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    data = query_result["data"]
    y_data = [row.get(y_column) for row in data]
    x_data = [row.get(x_column) for row in data]
    
    config = {
      "color": THEME_COLORS,
      "tooltip": {
        "trigger": "axis",
        "axisPointer": {
          "type": "shadow"
        }
      },
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
          "type": "bar",
          "showBackground": True,
          "backgroundStyle": {
            "color": "rgba(180, 180, 180, 0.2)"
          }
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


def echarts_bar_stacked(category_column: str, value_columns: list, query_result: dict = None, title: str = "Stacked Bar Chart", x_axis_name: str = None, y_axis_name: str = None, series_labels: dict = None) -> dict:
    """Generate stacked bar charts for echarts.js using the provided query result data.
    Multiple series are stacked on top of each other.
    
    Args:
        category_column: Column name for categories (x-axis)
        value_columns: List of column names for stacked values
        query_result: Query result dict with 'data' key containing list of row dicts
        title: Chart title
        x_axis_name: Optional display name for x-axis
        y_axis_name: Optional display name for y-axis
        series_labels: Optional dict mapping column names to display labels
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    if not series_labels:
        series_labels = {}
    
    data = query_result["data"]
    categories = [row.get(category_column) for row in data]
    
    legend_labels = [series_labels.get(col, col) for col in value_columns]
    
    series = []
    for col in value_columns:
        series.append({
            "name": series_labels.get(col, col),
            "type": "bar",
            "stack": "total",
            "data": [row.get(col, 0) for row in data]
        })
    
    config = {
        "color": THEME_COLORS,
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
            "data": legend_labels,
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
    
    if x_axis_name:
        config["xAxis"]["name"] = x_axis_name
    if y_axis_name:
        config["yAxis"]["name"] = y_axis_name
    
    return config


def echarts_bar_grouped(category_column: str, value_columns: list, query_result: dict = None, title: str = "Grouped Bar Chart", x_axis_name: str = None, y_axis_name: str = None, series_labels: dict = None) -> dict:
    """Generate grouped/clustered bar charts for echarts.js using the provided query result data.
    Multiple series are displayed side by side.
    
    Args:
        category_column: Column name for categories (x-axis)
        value_columns: List of column names for grouped values
        query_result: Query result dict with 'data' key containing list of row dicts
        title: Chart title
        x_axis_name: Optional display name for x-axis
        y_axis_name: Optional display name for y-axis
        series_labels: Optional dict mapping column names to display labels
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    if not series_labels:
        series_labels = {}
    
    data = query_result["data"]
    categories = [row.get(category_column) for row in data]
    
    legend_labels = [series_labels.get(col, col) for col in value_columns]
    
    series = []
    for col in value_columns:
        series.append({
            "name": series_labels.get(col, col),
            "type": "bar",
            "data": [row.get(col, 0) for row in data]
        })
    
    config = {
        "color": THEME_COLORS,
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
            "data": legend_labels,
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
    
    if x_axis_name:
        config["xAxis"]["name"] = x_axis_name
    if y_axis_name:
        config["yAxis"]["name"] = y_axis_name
    
    return config


def echarts_bar_stacked_dual_axis(category_column: str, primary_value_columns: list, secondary_value_columns: list, query_result: dict = None, title: str = "Stacked Bar Chart (Dual Axis)", primary_axis_name: str = None, secondary_axis_name: str = None, x_axis_name: str = None, series_labels: dict = None) -> dict:
    """Generate stacked bar charts with dual y-axes for echarts.js using the provided query result data.
    Primary columns are stacked on the left y-axis, secondary columns are stacked on the right y-axis.
    
    Args:
        category_column: Column name for categories (x-axis)
        primary_value_columns: List of column names for stacked values on primary (left) y-axis
        secondary_value_columns: List of column names for stacked values on secondary (right) y-axis
        query_result: Query result dict with 'data' key containing list of row dicts
        title: Chart title
        primary_axis_name: Optional name for primary y-axis
        secondary_axis_name: Optional name for secondary y-axis
        x_axis_name: Optional display name for x-axis
        series_labels: Optional dict mapping column names to display labels
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    if not series_labels:
        series_labels = {}
    
    data = query_result["data"]
    categories = [row.get(category_column) for row in data]
    
    series = []
    all_columns = primary_value_columns + secondary_value_columns
    
    # Add primary axis series (stacked)
    for col in primary_value_columns:
        series.append({
            "name": series_labels.get(col, col),
            "type": "bar",
            "stack": "primary",
            "yAxisIndex": 0,
            "data": [row.get(col, 0) for row in data]
        })
    
    # Add secondary axis series (stacked)
    for col in secondary_value_columns:
        series.append({
            "name": series_labels.get(col, col),
            "type": "bar",
            "stack": "secondary",
            "yAxisIndex": 1,
            "data": [row.get(col, 0) for row in data]
        })
    
    config = {
        "color": THEME_COLORS,
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
            "data": [series_labels.get(col, col) for col in all_columns],
            "top": "bottom"
        },
        "xAxis": {
            "type": "category",
            "data": categories
        },
        "yAxis": [
            {
                "type": "value",
                "name": primary_axis_name,
                "position": "left"
            },
            {
                "type": "value",
                "name": secondary_axis_name,
                "position": "right"
            }
        ],
        "series": series
    }
    
    if x_axis_name:
        config["xAxis"]["name"] = x_axis_name
    
    return config


def echarts_bar_grouped_dual_axis(category_column: str, primary_value_columns: list, secondary_value_columns: list, query_result: dict = None, title: str = "Grouped Bar Chart (Dual Axis)", primary_axis_name: str = None, secondary_axis_name: str = None, x_axis_name: str = None, series_labels: dict = None) -> dict:
    """Generate grouped/clustered bar charts with dual y-axes for echarts.js using the provided query result data.
    Primary columns are displayed on the left y-axis, secondary columns are displayed on the right y-axis.
    All bars are grouped side by side.
    
    Args:
        category_column: Column name for categories (x-axis)
        primary_value_columns: List of column names for grouped values on primary (left) y-axis
        secondary_value_columns: List of column names for grouped values on secondary (right) y-axis
        query_result: Query result dict with 'data' key containing list of row dicts
        title: Chart title
        primary_axis_name: Optional name for primary y-axis
        secondary_axis_name: Optional name for secondary y-axis
        x_axis_name: Optional display name for x-axis
        series_labels: Optional dict mapping column names to display labels
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    if not series_labels:
        series_labels = {}
    
    data = query_result["data"]
    categories = [row.get(category_column) for row in data]
    
    series = []
    all_columns = primary_value_columns + secondary_value_columns
    
    # Add primary axis series
    for col in primary_value_columns:
        series.append({
            "name": series_labels.get(col, col),
            "type": "bar",
            "yAxisIndex": 0,
            "data": [row.get(col, 0) for row in data]
        })
    
    # Add secondary axis series
    for col in secondary_value_columns:
        series.append({
            "name": series_labels.get(col, col),
            "type": "bar",
            "yAxisIndex": 1,
            "data": [row.get(col, 0) for row in data]
        })
    
    config = {
        "color": THEME_COLORS,
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
            "data": [series_labels.get(col, col) for col in all_columns],
            "top": "bottom"
        },
        "xAxis": {
            "type": "category",
            "data": categories
        },
        "yAxis": [
            {
                "type": "value",
                "name": primary_axis_name,
                "position": "left"
            },
            {
                "type": "value",
                "name": secondary_axis_name,
                "position": "right"
            }
        ],
        "series": series
    }
    
    if x_axis_name:
        config["xAxis"]["name"] = x_axis_name
    
    return config
