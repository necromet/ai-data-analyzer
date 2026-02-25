# Starry Night theme colors from index.css
THEME_COLORS = ['#5b51d8', '#f2c14e', '#a0b4d4', '#c0bfcc', '#4a3a45']

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
    
    # Build data array: [x, y] or [x, y, size] or [x, y, size, label]
    scatter_data = []
    for row in data:
        point = [row.get(x_column), row.get(y_column)]
        if size_column:
            point.append(row.get(size_column))
        if label_column:
            point.append(row.get(label_column))
        scatter_data.append(point)
    
    # Build title config
    title_config = {
        "text": title,
        "left": "center",
        "top": 5
    }
    if subtitle:
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
    
    # Build series config
    series_config = {
        "type": "scatter",
        "data": scatter_data,
        "emphasis": {
            "focus": "series"
        },
        "symbolSize": 10,
        "itemStyle": {
            "opacity": 0.5  # Set opacity to 50%
        },
        "sampling": "lttb"
    }
    
    # Build config
    config = {
        "color": THEME_COLORS,
        "title": title_config,
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
    
    # If we have extra dimensions, customize tooltip formatter
    if size_column or label_column:
        # Build custom formatter as a structured object
        formatter_parts = []
        if label_column:
            formatter_parts.append({"label": label_column, "index": 3 if size_column else 2})
        formatter_parts.append({"label": x_column, "index": 0, "format": "toFixed", "precision": 2})
        formatter_parts.append({"label": y_column, "index": 1, "format": "toFixed", "precision": 2})
        if size_column:
            formatter_parts.append({"label": size_column, "index": 2})

        config["tooltip"]["formatter"] = {
            "type": "structured",
            "parts": formatter_parts
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
    if len(data) > 500:
        series_config["large"] = True
        series_config["largeThreshold"] = 500
        series_config.pop("emphasis", None)
    
    if len(data) > 10000:
        series_config["symbolSize"] = 5  # Reduce symbol size for very large datasets
        series_config["progressive"] = 5000
        series_config["progressiveThreshold"] = 10000
        series_config["itemStyle"] = {
            "opacity": 0.3  # Set opacity to 30%
        }
    
    return config
