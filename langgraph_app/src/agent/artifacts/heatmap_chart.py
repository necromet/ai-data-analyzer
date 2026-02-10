def echarts_heatmap(x_column: str, y_column: str, value_column: str, title: str = "Heatmap", query_result: dict = None) -> dict:
    """Generate a basic heatmap for echarts.js using the provided query result data.
    
    Args:
        x_column: Column name for x-axis categories
        y_column: Column name for y-axis categories
        value_column: Column name for heatmap values
        title: Chart title
        query_result: Query result dict with 'data' key containing list of row dicts
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
    
    return {
        "title": {
            "text": title,
            "left": "center"
        },
        "tooltip": {
            "position": "top"
        },
        "grid": {
            "height": "50%",
            "top": "15%"
        },
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
                    "show": True
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


def echarts_heatmap_time_series(date_column: str, time_category_column: str, value_column: str, title: str = "Time Series Heatmap", query_result: dict = None) -> dict:
    """Generate a time-based heatmap for echarts.js (e.g., hours vs days, months vs years).
    
    Args:
        date_column: Column name for date categories (e.g., days, dates)
        time_category_column: Column name for time categories (e.g., hours, months)
        value_column: Column name for heatmap values
        title: Chart title
        query_result: Query result dict with 'data' key containing list of row dicts
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    data = query_result["data"]
    
    # Extract unique categories
    dates = sorted(list(set(row.get(date_column) for row in data if row.get(date_column) is not None)))
    time_categories = sorted(list(set(row.get(time_category_column) for row in data if row.get(time_category_column) is not None)))
    
    # Create mapping
    date_map = {cat: idx for idx, cat in enumerate(dates)}
    time_map = {cat: idx for idx, cat in enumerate(time_categories)}
    
    # Prepare heatmap data
    heatmap_data = []
    values = []
    for row in data:
        date_val = row.get(date_column)
        time_val = row.get(time_category_column)
        val = row.get(value_column)
        if date_val is not None and time_val is not None and val is not None:
            heatmap_data.append([date_map[date_val], time_map[time_val], val])
            values.append(val)
    
    min_val = min(values) if values else 0
    max_val = max(values) if values else 10
    
    return {
        "title": {
            "text": title,
            "left": "center"
        },
        "tooltip": {
            "position": "top"
        },
        "grid": {
            "height": "50%",
            "top": "15%"
        },
        "xAxis": {
            "type": "category",
            "data": dates,
            "splitArea": {
                "show": True
            }
        },
        "yAxis": {
            "type": "category",
            "data": time_categories,
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
                    "show": True
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
            # Extract values for both columns
            values1 = [row.get(col1) for row in data if row.get(col1) is not None and row.get(col2) is not None]
            values2 = [row.get(col2) for row in data if row.get(col1) is not None and row.get(col2) is not None]
            
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
    
    return {
        "title": {
            "text": title,
            "left": "center"
        },
        "tooltip": {
            "position": "top"
        },
        "grid": {
            "height": "60%",
            "top": "15%"
        },
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
                    "show": True
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


def echarts_heatmap_calendar(date_column: str, value_column: str, year: int, title: str = "Calendar Heatmap", query_result: dict = None) -> dict:
    """Generate a calendar heatmap for echarts.js showing values across dates in a year.
    
    Args:
        date_column: Column name containing dates (should be in format YYYY-MM-DD)
        value_column: Column name for heatmap values
        year: Year to display in calendar format
        title: Chart title
        query_result: Query result dict with 'data' key containing list of row dicts
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    data = query_result["data"]
    
    # Prepare calendar data: [date, value]
    calendar_data = []
    values = []
    for row in data:
        date_val = row.get(date_column)
        val = row.get(value_column)
        if date_val is not None and val is not None:
            # Ensure date is in string format
            date_str = str(date_val)
            calendar_data.append([date_str, val])
            values.append(val)
    
    min_val = min(values) if values else 0
    max_val = max(values) if values else 10
    
    return {
        "title": {
            "text": title,
            "left": "center",
            "top": 20
        },
        "tooltip": {
            "position": "top"
        },
        "visualMap": {
            "min": min_val,
            "max": max_val,
            "calculable": True,
            "orient": "horizontal",
            "left": "center",
            "bottom": 20
        },
        "calendar": {
            "top": 80,
            "left": 30,
            "right": 30,
            "cellSize": ["auto", 13],
            "range": str(year),
            "itemStyle": {
                "borderWidth": 0.5
            },
            "yearLabel": {
                "show": False
            }
        },
        "series": [
            {
                "type": "heatmap",
                "coordinateSystem": "calendar",
                "data": calendar_data
            }
        ]
    }
