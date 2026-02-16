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
        "left": "center"
    }
    if subtitle:
        title_config["subtext"] = subtitle
    
    # Build axis configs
    x_axis_config = {
        "type": "value",
        "splitLine": {"show": True}
    }
    if x_axis_name:
        x_axis_config["name"] = x_axis_name
        x_axis_config["nameLocation"] = "middle"
        x_axis_config["nameGap"] = 30
    
    y_axis_config = {
        "type": "value",
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
        }
    }
    
    # Set symbol size: dynamic if size_column provided, otherwise fixed
    if size_column:
        # Use function-style symbolSize for bubble effect
        # Note: ECharts expects this as a function reference, but in JSON
        # we use a special marker that the frontend will convert
        series_config["symbolSize"] = "function(val) { return Math.sqrt(val[2]) * 4; }"
    else:
        series_config["symbolSize"] = 10
    
    # Build config
    config = {
        "color": THEME_COLORS,
        "title": title_config,
        "tooltip": {
            "trigger": "item"
        }
    }
    
    # If we have extra dimensions, customize tooltip formatter
    if size_column or label_column:
        # Build custom formatter as a string (frontend will convert to function)
        formatter_parts = []
        if label_column:
            formatter_parts.append(f"'<strong>{label_column}:</strong> ' + params.data[{3 if size_column else 2}] + '<br/>'")
        formatter_parts.append(f"'<strong>{x_column}:</strong> ' + params.data[0].toFixed(2) + '<br/>'")
        formatter_parts.append(f"'<strong>{y_column}:</strong> ' + params.data[1].toFixed(2) + '<br/>'")
        if size_column:
            formatter_parts.append(f"'<strong>{size_column}:</strong> ' + params.data[2]")
        
        config["tooltip"]["formatter"] = "function(params) { return " + " + ".join(formatter_parts) + "; }"
    
    config["xAxis"] = x_axis_config
    config["yAxis"] = y_axis_config
    config["grid"] = {
        "top": 80,
        "left": 60,
        "right": 40,
        "bottom": 60
    }
    config["series"] = [series_config]
    
    return config
