# Starry Night theme colors from index.css
THEME_COLORS = ['#5b51d8', '#f2c14e', '#a0b4d4', '#c0bfcc', '#4a3a45']

def echarts_heatmap(x_column: str, y_column: str, value_column: str, title: str = "Heatmap", query_result: dict = None, x_axis_name: str = None, y_axis_name: str = None) -> dict:
    """Generate a basic heatmap for echarts.js using the provided query result data.
    
    Args:
        x_column: Column name for x-axis categories
        y_column: Column name for y-axis categories
        value_column: Column name for heatmap values
        title: Chart title
        query_result: Query result dict with 'data' key containing list of row dicts
        x_axis_name: Optional display name for x-axis
        y_axis_name: Optional display name for y-axis
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    data = query_result["data"]
    
    # Extract unique categories for x and y axes
    x_categories = sorted(list(set(row.get(x_column) for row in data if row.get(x_column) is not None)))
    y_categories = sorted(list(set(row.get(y_column) for row in data if row.get(y_column) is not None)))
    
    # Create mapping from category to index
    x_map = {cat: idx for idx, cat in enumerate(x_categories)}
    y_map = {cat: idx for idx, cat in enumerate(y_categories)}
    
    # Prepare heatmap data: [x_index, y_index, value]
    heatmap_data = []
    values = []
    for row in data:
        x_val = row.get(x_column)
        y_val = row.get(y_column)
        val = row.get(value_column)
        if x_val is not None and y_val is not None and val is not None:
            heatmap_data.append([x_map[x_val], y_map[y_val], val])
            values.append(val)
    
    # Calculate min and max for visualMap
    min_val = min(values) if values else 0
    max_val = max(values) if values else 10
    
    config = {
        "color": THEME_COLORS,
        "title": {
            "text": title,
            "left": "center",
            "top": 5
        },
        "tooltip": {
            "position": "top"
        },
        "grid": {
            "height": "50%",
            "top": "15%"
        },
        "dataZoom": [
            {"type": "inside"},
            {"type": "inside", "orient": "vertical"}
        ],
        "xAxis": {
            "type": "category",
            "data": x_categories,
            "splitArea": {
                "show": True
            }
        },
        "yAxis": {
            "type": "category",
            "data": y_categories,
            "splitArea": {
                "show": True
            }
        },
        "visualMap": {
            "min": min_val,
            "max": max_val,
            "calculable": True,
            "orient": "horizontal",
            "left": "center",
            "bottom": "15%"
        },
        "series": [
            {
                "name": value_column,
                "type": "heatmap",
                "data": heatmap_data,
                "label": {
                    "show": False
                },
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowColor": "rgba(0, 0, 0, 0.5)"
                    }
                }
            }
        ]
    }
    
    if x_axis_name:
        config["xAxis"]["name"] = x_axis_name
    if y_axis_name:
        config["yAxis"]["name"] = y_axis_name
    if len(data) > 500:
        for s in config["series"]:
            s["large"] = True
            s["largeThreshold"] = 500
    
    return config

def echarts_heatmap_correlation(columns: list, title: str = "Correlation Heatmap", query_result: dict = None) -> dict:
    """Generate a correlation heatmap for echarts.js showing relationships between multiple columns.
    
    Args:
        columns: List of column names to calculate correlations
        title: Chart title
        query_result: Query result dict with 'data' key containing list of row dicts
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    data = query_result["data"]
    
    # Calculate correlation matrix
    n = len(columns)
    correlation_data = []
    
    for i, col1 in enumerate(columns):
        for j, col2 in enumerate(columns):
            # Extract values for both columns, converting to float to handle string-typed numbers
            def to_float(v):
                try:
                    return float(v)
                except (TypeError, ValueError):
                    return None

            raw_pairs = [
                (to_float(row.get(col1)), to_float(row.get(col2)))
                for row in data
                if row.get(col1) is not None and row.get(col2) is not None
            ]
            valid_pairs = [(v1, v2) for v1, v2 in raw_pairs if v1 is not None and v2 is not None]
            values1 = [v1 for v1, v2 in valid_pairs]
            values2 = [v2 for v1, v2 in valid_pairs]
            
            # Calculate correlation (simplified - Pearson correlation coefficient)
            if len(values1) > 1:
                mean1 = sum(values1) / len(values1)
                mean2 = sum(values2) / len(values2)
                
                numerator = sum((v1 - mean1) * (v2 - mean2) for v1, v2 in zip(values1, values2))
                denominator1 = sum((v1 - mean1) ** 2 for v1 in values1) ** 0.5
                denominator2 = sum((v2 - mean2) ** 2 for v2 in values2) ** 0.5
                
                if denominator1 > 0 and denominator2 > 0:
                    correlation = numerator / (denominator1 * denominator2)
                else:
                    correlation = 0
            else:
                correlation = 0
            
            correlation_data.append([i, j, round(correlation, 2)])
    
    config = {
        "color": THEME_COLORS,
        "title": {
            "text": title,
            "left": "center",
            "top": 5
        },
        "tooltip": {
            "position": "top"
        },
        "grid": {
            "height": "60%",
            "top": "15%"
        },
        "dataZoom": [
            {"type": "inside"},
            {"type": "inside", "orient": "vertical"}
        ],
        "xAxis": {
            "type": "category",
            "data": columns,
            "splitArea": {
                "show": True
            }
        },
        "yAxis": {
            "type": "category",
            "data": columns,
            "splitArea": {
                "show": True
            }
        },
        "visualMap": {
            "min": -1,
            "max": 1,
            "calculable": True,
            "orient": "horizontal",
            "left": "center",
            "bottom": "5%"
        },
        "series": [
            {
                "name": "Correlation",
                "type": "heatmap",
                "data": correlation_data,
                "label": {
                    "show": False
                },
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowColor": "rgba(0, 0, 0, 0.5)"
                    }
                }
            }
        ]
    }
    if len(data) > 500:
        for s in config["series"]:
            s["large"] = True
            s["largeThreshold"] = 500
    
    return config

