# Starry Night theme colors from index.css
THEME_COLORS = ['#5b51d8', '#f2c14e', '#a0b4d4', '#c0bfcc', '#4a3a45']

def echarts_bar_line(x_column: str, bar_columns: list, line_columns: list, query_result: dict = None, 
                     primary_axis_name: str = "", secondary_axis_name: str = "", title: str = None, x_axis_name: str = None, series_labels: dict = None, x_axis_type: str = None) -> dict:
    """Generate combination bar and line chart with dual y-axes for echarts.js.
    
    Args:
        x_column: Column name for x-axis (categories)
        bar_columns: List of column names for bar series (uses left y-axis)
        line_columns: List of column names for line series (uses right y-axis)
        query_result: Query result dict with 'data' key containing list of row dicts
        primary_axis_name: Optional label for left y-axis (bar axis)
        secondary_axis_name: Optional label for right y-axis (line axis)
        title: Optional chart title
        x_axis_name: Optional display name for x-axis
        series_labels: Optional dict mapping column names to display labels
        x_axis_type: Optional axis scale type for x-axis ("category", "value", "time", "log")
    
    Returns:
        ECharts configuration dictionary with combined bar and line series
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    if not series_labels:
        series_labels = {}
    
    data = query_result["data"]
    x_data = [row.get(x_column) for row in data]
    
    # Collect all column names for legend
    all_columns = bar_columns + line_columns
    legend_data = [series_labels.get(col, col) for col in all_columns]
    
    # Build bar series (using primary/left y-axis)
    bar_series = []
    for col in bar_columns:
        y_data = [row.get(col) for row in data]
        bar_series.append({
            "name": series_labels.get(col, col),
            "type": "bar",
            "data": y_data
        })
    
    # Build line series (using secondary/right y-axis)
    line_series = []
    for col in line_columns:
        y_data = [row.get(col) for row in data]
        line_series.append({
            "name": series_labels.get(col, col),
            "type": "line",
            "yAxisIndex": 1,
            "data": y_data
        })
    
    # Combine all series
    all_series = bar_series + line_series
    
    # Build x-axis config
    x_axis_config = {
        "type": x_axis_type or "category",
        "data": x_data,
        "axisPointer": {
            "type": "shadow"
        }
    }
    if x_axis_name:
        x_axis_config["name"] = x_axis_name
    
    # Build y-axis configurations
    y_axis_config = [
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
    ]
    
    config = {
        "color": THEME_COLORS,
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross",
                "crossStyle": {
                    "color": "#999"
                }
            }
        },
        "toolbox": {
            "feature": {
                "dataView": {"show": True, "readOnly": False},
                "magicType": {"show": True, "type": ["line", "bar"]},
                "restore": {"show": True},
                "saveAsImage": {"show": True}
            }
        },
        "legend": {
            "data": legend_data,
            "top": 40
        },
        "xAxis": x_axis_config,
        "yAxis": y_axis_config,
        "grid": {
            "top": 100,
            "bottom": 100,
            "containLabel": True
        },
        "dataZoom": [
            {"type": "inside"},
            {"type": "slider", "bottom": 10}
        ],
        "series": all_series
    }
    
    if title:
        config["title"] = {"text": title, "left": "center", "top": 0}
    if len(data) > 500:
        for s in config["series"]:
            s["large"] = True
            s["largeThreshold"] = 500
    
    return config