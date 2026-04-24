# Starry Night theme colors from index.css
THEME_COLORS = ['#5b51d8', '#f2c14e', '#a0b4d4', '#c0bfcc', '#4a3a45']
from .utils import print_and_save_config
import random

MAX_SCATTER_POINTS = 5000

def echarts_scatter(
    x_column: str, 
    y_column: str, 
    title: str = "Scatter Plot",
    subtitle: str = None,
    size_column: str = None,
    label_column: str = None,
    x_axis_name: str = None,
    y_axis_name: str = None,
    x_axis_type: str = None,
    y_axis_type: str = None,
    query_result: dict = None
) -> dict:
    """Generate scatter/bubble plots for echarts.js using the provided query result data.
    
    Args:
        x_column: Column name for x-axis
        y_column: Column name for y-axis
        title: Chart title
        subtitle: Optional chart subtitle
        size_column: Optional column name for bubble size (creates bubble chart)
        label_column: Optional column name for data point labels
        x_axis_name: Optional name for x-axis
        y_axis_name: Optional name for y-axis
        x_axis_type: Optional axis scale type ("category", "value", "time", "log")
        y_axis_type: Optional axis scale type ("category", "value", "time", "log")
        query_result: Query result dict with 'data' key containing list of row dicts
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    data = query_result["data"]
    original_count = len(data)
    
    # Build data array: [x, y] or [x, y, size] or [x, y, size, label]
    # Filter out rows where x or y is None
    scatter_data = []
    for row in data:
        x_val = row.get(x_column)
        y_val = row.get(y_column)
        if x_val is None or y_val is None:
            continue
        point = [x_val, y_val]
        if size_column:
            point.append(row.get(size_column, 1))
        if label_column:
            point.append(row.get(label_column, ""))
        scatter_data.append(point)
    
    # Server-side downsampling for large datasets
    # ECharts' sampling/large modes do NOT work with scatter series,
    # so we must reduce point count before sending to the browser.
    sampled = False
    if len(scatter_data) > MAX_SCATTER_POINTS:
        scatter_data = random.sample(scatter_data, MAX_SCATTER_POINTS)
        sampled = True
    
    # Build title config
    title_config = {
        "text": title,
        "left": "center",
        "top": 5
    }
    if sampled:
        title_config["subtext"] = f"Showing {MAX_SCATTER_POINTS:,} of {original_count:,} points (sampled)"
    elif subtitle:
        title_config["subtext"] = subtitle
    
    # Build axis configs
    x_axis_config = {
        "type": x_axis_type or "value",
        "splitLine": {"show": True}
    }
    if x_axis_name:
        x_axis_config["name"] = x_axis_name
        x_axis_config["nameLocation"] = "middle"
        x_axis_config["nameGap"] = 30
    
    y_axis_config = {
        "type": y_axis_type or "value",
        "splitLine": {"show": True}
    }
    if y_axis_name:
        y_axis_config["name"] = y_axis_name
        y_axis_config["nameLocation"] = "middle"
        y_axis_config["nameGap"] = 40
    
    # Determine symbol size and opacity based on final point count
    point_count = len(scatter_data)
    if point_count > 2000:
        symbol_size = 3
        opacity = 0.3
    elif point_count > 500:
        symbol_size = 5
        opacity = 0.4
    else:
        symbol_size = 10
        opacity = 0.5
    
    # Build series config
    series_config = {
        "type": "scatter",
        "data": scatter_data,
        "symbolSize": symbol_size,
        "itemStyle": {
            "opacity": opacity
        },
        "progressive": 2000,
        "progressiveThreshold": 500,
    }
    
    # Only add emphasis for small datasets (expensive for large ones)
    if point_count <= 500:
        series_config["emphasis"] = {"focus": "series"}
    
    # Build config
    config = {
        "color": THEME_COLORS,
        "title": title_config,
        "tooltip": {
            "trigger": "item",
        },
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
    }
    
    config["xAxis"] = x_axis_config
    config["yAxis"] = y_axis_config
    config["grid"] = {
        "top": 80,
        "left": 60,
        "right": 40,
        "bottom": 80
    }
    config["dataZoom"] = [
        {"type": "inside"},
        {"type": "slider", "bottom": 10}
    ]
    config["series"] = [series_config]

    print_and_save_config(config, name="echarts_scatter")
    return config
