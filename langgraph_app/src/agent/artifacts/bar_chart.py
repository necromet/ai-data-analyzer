# Starry Night theme colors from index.css
THEME_COLORS = ['#5b51d8', '#f2c14e', '#a0b4d4', '#c0bfcc', '#4a3a45']
from .utils import print_and_save_config

def echarts_bar(x_column: str, y_column: str, query_result: dict = None, title: str = None, x_axis_name: str = None, y_axis_name: str = None, x_axis_type: str = None, y_axis_type: str = None) -> dict:
    """Generate vertical bar charts for echarts.js using the provided query result data.
    
    Args:
        x_column: Column name for x-axis (categories)
        y_column: Column name for y-axis (values)
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
      "tooltip": {
        "trigger": "axis",
        "axisPointer": {
          "type": "shadow"
        }
      },
      "grid": {
        "top": 100,
        "bottom": 100,
        "containLabel": True
      },
      "dataZoom": [
        {"type": "inside"},
        {"type": "slider", "bottom": 20, "height": 40}
      ],
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
          "type": "bar",
          "showBackground": True,
          "backgroundStyle": {
            "color": "rgba(180, 180, 180, 0.2)"
          },
          "sampling": "lttb"
        }
      ]
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

    print_and_save_config(config, name="echarts_bar")
    return config


def echarts_bar_horizontal(y_column: str, x_column: str, query_result: dict = None, title: str = None, x_axis_name: str = None, y_axis_name: str = None, x_axis_type: str = None, y_axis_type: str = None) -> dict:
    """Generate horizontal bar charts for echarts.js using the provided query result data.
    
    Args:
        y_column: Column name for y-axis (categories)
        x_column: Column name for x-axis (values)
        query_result: Query result dict with 'data' key containing list of row dicts
        title: Optional chart title
        x_axis_name: Optional display name for x-axis (value axis)
        y_axis_name: Optional display name for y-axis (category axis)
        x_axis_type: Optional axis scale type ("category", "value", "time", "log")
        y_axis_type: Optional axis scale type ("category", "value", "time", "log")
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
      "grid": {
        "top": "10%",
        "right": "10%",
        "bottom": "5%",
        "left": "10%",
        "containLabel": True
        },
      "dataZoom": [
        {"type": "inside", "yAxisIndex": 0},
        {"type": "slider", "yAxisIndex": 0, "right": 15, "width": 20}
      ],
      "toolbox": {
            "show": True,
            "orient": "vertical",
            "left": 5,
            "top": "center",
            "feature": {
                "dataView": {"show": True, "readOnly": False},
                "restore": {"show": True},
                "saveAsImage": {"show": True}
            }
        },
      "xAxis": {
        "type": x_axis_type or "value"
      },
      "yAxis": {
        "type": y_axis_type or "category",
        "data": y_data,
        "inverse": True
      },
      "series": [
        {
            "data": x_data,
            "type": "bar",
            "showBackground": True,
            "backgroundStyle": {
                "color": "rgba(180, 180, 180, 0.2)"
            },
            "itemStyle": {
                "borderRadius": [0, 8, 8, 0]
            },
            "sampling": "lttb"
        },
    ]
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

    print_and_save_config(config, name="echarts_bar_horizontal")
    return config


def echarts_bar_stacked(category_column: str, value_columns: list, query_result: dict = None, title: str = "Stacked Bar Chart", x_axis_name: str = None, y_axis_name: str = None, series_labels: dict = None, x_axis_type: str = None, y_axis_type: str = None) -> dict:
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
        x_axis_type: Optional axis scale type ("category", "value", "time", "log")
        y_axis_type: Optional axis scale type ("category", "value", "time", "log")
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
            "left": "center",
            "top": 5
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross"
            }
        },
        "legend": {
            "data": legend_labels,
            "top": 40
        },
        "grid": {
            "top": 100,
            "bottom": 110,
            "containLabel": True
        },
        "dataZoom": [
            {"type": "inside"},
            {"type": "slider", "bottom": 20, "height": 40},
        ],
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
        "xAxis": {
            "type": x_axis_type or "category",
            "data": categories
        },
        "yAxis": {
            "type": y_axis_type or "value"
        },
        "series": series
    }
    
    if x_axis_name:
        config["xAxis"]["name"] = x_axis_name
    if y_axis_name:
        config["yAxis"]["name"] = y_axis_name
    if len(data) > 500:
        for s in config["series"]:
            s["large"] = True
            s["largeThreshold"] = 500

    print_and_save_config(config, name="echarts_bar_stacked")
    return config


def echarts_bar_grouped(category_column: str, value_columns: list, query_result: dict = None, title: str = "Grouped Bar Chart", x_axis_name: str = None, y_axis_name: str = None, series_labels: dict = None, x_axis_type: str = None, y_axis_type: str = None) -> dict:
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
        x_axis_type: Optional axis scale type ("category", "value", "time", "log")
        y_axis_type: Optional axis scale type ("category", "value", "time", "log")
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
            "left": "center",
            "top": 5
        },
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "shadow"
            }
        },
        "legend": {
            "data": legend_labels,
            "top": 40
        },
        "grid": {
            "top": 100,
            "bottom": 110,
            "containLabel": True
        },
        "dataZoom": [
            {"type": "inside"},
            {"type": "slider", "bottom": 50}
        ],
        "toolbox": {
            "show": True,
            "orient": "vertical",
            "right": 5,
            "top": "center",
            "feature": {
                "dataView": {"show": True, "readOnly": False},
                "restore": {"show": True},
                "saveAsImage": {"show": True}
            }
        },
        "xAxis": {
            "type": x_axis_type or "category",
            "data": categories
        },
        "yAxis": {
            "type": y_axis_type or "value"
        },
        "series": series
    }
    
    if x_axis_name:
        config["xAxis"]["name"] = x_axis_name
    if y_axis_name:
        config["yAxis"]["name"] = y_axis_name
    if len(data) > 500:
        for s in config["series"]:
            s["large"] = True
            s["largeThreshold"] = 500

    print_and_save_config(config, name="echarts_bar_grouped")
    return config