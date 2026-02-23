import numpy as np

# Starry Night theme colors from index.css
THEME_COLORS = ['#5b51d8', '#f2c14e', '#a0b4d4', '#c0bfcc', '#4a3a45']

def calculate_boxplot_stats(values):
    """Calculate boxplot statistics (min, Q1, median, Q3, max) for a list of values.
    
    Args:
        values: List of numeric values
        
    Returns:
        List containing [min, Q1, median, Q3, max]
    """
    if not values:
        return [0, 0, 0, 0, 0]
    
    # Ensure values is a 1D array and remove any NaN values
    values_array = np.array(values).flatten()
    values_array = values_array[~np.isnan(values_array)]
    
    if len(values_array) == 0:
        return [0, 0, 0, 0, 0]
    
    values_sorted = np.sort(values_array)
    
    # Use .item() to safely extract scalar values from numpy arrays
    min_val = np.min(values_sorted).item()
    q1 = np.percentile(values_sorted, 25).item()
    median = np.percentile(values_sorted, 50).item()
    q3 = np.percentile(values_sorted, 75).item()
    max_val = np.max(values_sorted).item()
    
    return [min_val, q1, median, q3, max_val]


def _extract_boxplot_data(query_result: dict, category_column: str,
                          min_col: str = "min", q1_col: str = "q1", median_col: str = "median",
                          q3_col: str = "q3", max_col: str = "max"):
    """Extract categories and box data from pre-computed query results.
    
    Returns:
        Tuple of (categories list, box_data list) or (None, error_dict) on failure
    """
    if not query_result or not query_result.get("data"):
        return None, {"error": "No query results available"}
    
    data = query_result["data"]
    categories = []
    box_data = []
    
    for row in data:
        category = row.get(category_column)
        min_val = row.get(min_col)
        q1_val = row.get(q1_col)
        median_val = row.get(median_col)
        q3_val = row.get(q3_col)
        max_val = row.get(max_col)
        
        if category is not None and all(v is not None for v in [min_val, q1_val, median_val, q3_val, max_val]):
            try:
                categories.append(str(category))
                box_data.append([float(min_val), float(q1_val), float(median_val), float(q3_val), float(max_val)])
            except (ValueError, TypeError):
                pass
    
    if not categories:
        return None, {"error": "No valid boxplot data available"}
    
    return (categories, box_data), None


def echarts_boxplot(category_column: str, query_result: dict, title: str = "",
                    min_col: str = "min", q1_col: str = "q1", median_col: str = "median",
                    q3_col: str = "q3", max_col: str = "max") -> dict:
    """Generate vertical boxplot charts from pre-computed statistics (min, Q1, median, Q3, max).
    
    Expects query results where each row contains a category and its pre-aggregated
    boxplot statistics (min, q1, median, q3, max).
    
    Args:
        category_column: Column name for categories (x-axis)
        query_result: Query result dict with 'data' key containing list of row dicts
        title: Optional chart title
        min_col: Column name for minimum values (default: "min")
        q1_col: Column name for Q1 values (default: "q1")
        median_col: Column name for median values (default: "median")
        q3_col: Column name for Q3 values (default: "q3")
        max_col: Column name for maximum values (default: "max")
        
    Returns:
        ECharts configuration dictionary
    """
    result, error = _extract_boxplot_data(query_result, category_column, min_col, q1_col, median_col, q3_col, max_col)
    if error:
        return error
    
    categories, box_data = result
    
    config = {
        "color": THEME_COLORS,
        "title": {
            "text": title or f"Boxplot by {category_column}",
            "top": 5
        },
        "tooltip": {
            "trigger": "item",
            "confine": True
        },
        "grid": {
            "left": "10%",
            "right": "10%",
            "bottom": 100,
            "top": 100,
            "containLabel": True
        },
        "dataZoom": [
            {"type": "inside"},
            {"type": "slider", "bottom": 40}
        ],
        "toolbox": {
            "feature": {
                "dataView": {"show": True, "readOnly": False},
                "restore": {"show": True},
                "saveAsImage": {"show": True}
            }
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
            "scale": True,
            "splitArea": {
                "show": True
            }
        },
        "series": [
            {
                "name": "boxplot",
                "type": "boxplot",
                "data": box_data
            }
        ]
    }
    
    return config