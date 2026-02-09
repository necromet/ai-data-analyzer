import numpy as np
from collections import defaultdict


def calculate_boxplot_stats(values):
    """Calculate boxplot statistics (min, Q1, median, Q3, max) for a list of values.
    
    Args:
        values: List of numeric values
        
    Returns:
        List containing [min, Q1, median, Q3, max]
    """
    if not values:
        return [0, 0, 0, 0, 0]
    
    values_array = np.array(values)
    values_sorted = np.sort(values_array)
    
    min_val = float(np.min(values_sorted))
    q1 = float(np.percentile(values_sorted, 25))
    median = float(np.percentile(values_sorted, 50))
    q3 = float(np.percentile(values_sorted, 75))
    max_val = float(np.max(values_sorted))
    
    return [min_val, q1, median, q3, max_val]


def echarts_boxplot(category_column: str, value_column: str, query_result: dict, title: str = "") -> dict:
    """Generate vertical boxplot charts for echarts.js using the provided query result data.
    
    Args:
        category_column: Column name for categories (y-axis)
        value_column: Column name for values to calculate statistics (x-axis)
        query_result: Query result dict with 'data' key containing list of row dicts
        title: Optional chart title
        
    Returns:
        ECharts configuration dictionary
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    data = query_result["data"]
    
    # Group data by category
    grouped_data = defaultdict(list)
    for row in data:
        category = row.get(category_column)
        value = row.get(value_column)
        if category is not None and value is not None:
            grouped_data[category].append(float(value))
    
    # Calculate statistics for each category
    categories = sorted(grouped_data.keys())
    boxplot_data = []
    
    for category in categories:
        stats = calculate_boxplot_stats(grouped_data[category])
        boxplot_data.append(stats)
    
    config = {
        "title": {
            "text": title or f"Boxplot of {value_column} by {category_column}"
        },
        "tooltip": {
            "trigger": "item",
            "axisPointer": {
                "type": "shadow"
            }
        },
        "grid": {
            "left": "10%",
            "right": "10%",
            "bottom": "15%"
        },
        "xAxis": {
            "type": "category",
            "data": categories,
            "boundaryGap": True,
            "nameGap": 30,
            "splitArea": {
                "show": False
            },
            "splitLine": {
                "show": False
            }
        },
        "yAxis": {
            "type": "value",
            "name": value_column,
            "splitArea": {
                "show": True
            }
        },
        "series": [
            {
                "name": "boxplot",
                "type": "boxplot",
                "data": boxplot_data,
                "tooltip": {
                    "formatter": lambda params: f"""
                        Category: {params['name']}<br/>
                        Upper: {params['data'][4]}<br/>
                        Q3: {params['data'][3]}<br/>
                        Median: {params['data'][2]}<br/>
                        Q1: {params['data'][1]}<br/>
                        Lower: {params['data'][0]}
                    """
                }
            }
        ]
    }
    
    return config


def echarts_boxplot_horizontal(category_column: str, value_column: str, query_result: dict, title: str = "") -> dict:
    """Generate horizontal boxplot charts for echarts.js using the provided query result data.
    Similar to the ECharts example with Income by Country.
    
    Args:
        category_column: Column name for categories (y-axis)
        value_column: Column name for values to calculate statistics (x-axis)
        query_result: Query result dict with 'data' key containing list of row dicts
        title: Optional chart title
        
    Returns:
        ECharts configuration dictionary
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    data = query_result["data"]
    
    # Group data by category
    grouped_data = defaultdict(list)
    for row in data:
        category = row.get(category_column)
        value = row.get(value_column)
        if category is not None and value is not None:
            grouped_data[category].append(float(value))
    
    # Calculate statistics for each category and sort by median
    categories_with_stats = []
    for category, values in grouped_data.items():
        stats = calculate_boxplot_stats(values)
        categories_with_stats.append((category, stats))
    
    # Sort by median (index 2 in stats)
    categories_with_stats.sort(key=lambda x: x[1][2])
    
    categories = [item[0] for item in categories_with_stats]
    boxplot_data = [item[1] for item in categories_with_stats]
    
    config = {
        "title": {
            "text": title or f"Boxplot of {value_column} by {category_column}"
        },
        "tooltip": {
            "trigger": "axis",
            "confine": True,
            "axisPointer": {
                "type": "shadow"
            }
        },
        "grid": {
            "left": "15%",
            "right": "10%",
            "bottom": "10%",
            "top": "15%",
            "containLabel": True
        },
        "xAxis": {
            "type": "value",
            "name": value_column,
            "nameLocation": "middle",
            "nameGap": 30,
            "scale": True,
            "splitArea": {
                "show": True
            }
        },
        "yAxis": {
            "type": "category",
            "data": categories,
            "boundaryGap": True,
            "nameGap": 30,
            "splitArea": {
                "show": False
            },
            "splitLine": {
                "show": False
            }
        },
        "dataZoom": [
            {
                "type": "inside",
                "yAxisIndex": 0
            },
            {
                "type": "slider",
                "yAxisIndex": 0,
                "width": 20,
                "right": 10
            }
        ],
        "series": [
            {
                "name": "boxplot",
                "type": "boxplot",
                "data": boxplot_data,
                "itemStyle": {
                    "color": "#b8c5f2"
                },
                "tooltip": {
                    "formatter": lambda params: f"""
                        {params['name']}<br/>
                        Max: {params['data'][4]}<br/>
                        Q3: {params['data'][3]}<br/>
                        Median: {params['data'][2]}<br/>
                        Q1: {params['data'][1]}<br/>
                        Min: {params['data'][0]}
                    """
                }
            }
        ]
    }
    
    return config
