import numpy as np


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
        "title": {
            "text": title or f"Boxplot by {category_column}"
        },
        "tooltip": {
            "trigger": "item",
            "confine": True
        },
        "grid": {
            "left": "10%",
            "right": "10%",
            "bottom": "15%",
            "top": "15%",
            "containLabel": True
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


def echarts_boxplot_horizontal(category_column: str, query_result: dict, title: str = "",
                               min_col: str = "min", q1_col: str = "q1", median_col: str = "median",
                               q3_col: str = "q3", max_col: str = "max") -> dict:
    """Generate horizontal boxplot charts from pre-computed statistics (min, Q1, median, Q3, max).
    
    Expects query results where each row contains a category and its pre-aggregated
    boxplot statistics (min, q1, median, q3, max).
    
    Args:
        category_column: Column name for categories (y-axis)
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
        "title": {
            "text": title or f"Boxplot by {category_column}"
        },
        "tooltip": {
            "trigger": "item",
            "confine": True
        },
        "grid": {
            "left": "15%",
            "right": "10%",
            "bottom": "80",
            "top": "15%",
            "containLabel": True
        },
        "xAxis": {
            "type": "value",
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
                "right": 10,
                "bottom": 20
            }
        ],
        "series": [
            {
                "name": "boxplot",
                "type": "boxplot",
                "data": box_data,
                "itemStyle": {
                    "color": "#b8c5f2"
                }
            }
        ]
    }
    
    return config


def echarts_boxplot_dual_axis(category_column: str, primary_categories: list, secondary_categories: list,
                              query_result: dict, title: str = "",
                              min_col: str = "min", q1_col: str = "q1", median_col: str = "median",
                              q3_col: str = "q3", max_col: str = "max",
                              primary_axis_name: str = None, secondary_axis_name: str = None) -> dict:
    """Generate vertical boxplot with dual y-axes from pre-computed statistics.
    
    Splits categories into two groups, each rendered on a separate y-axis with its own scale.
    Useful when comparing metrics with very different value ranges (e.g., cm vs grams).
    
    Args:
        category_column: Column name for categories (x-axis)
        primary_categories: List of category values for the left y-axis
        secondary_categories: List of category values for the right y-axis
        query_result: Query result dict with 'data' key containing list of row dicts
        title: Optional chart title
        min_col: Column name for minimum values (default: "min")
        q1_col: Column name for Q1 values (default: "q1")
        median_col: Column name for median values (default: "median")
        q3_col: Column name for Q3 values (default: "q3")
        max_col: Column name for maximum values (default: "max")
        primary_axis_name: Label for the left y-axis (optional)
        secondary_axis_name: Label for the right y-axis (optional)
        
    Returns:
        ECharts configuration dictionary
    """
    result, error = _extract_boxplot_data(query_result, category_column, min_col, q1_col, median_col, q3_col, max_col)
    if error:
        return error
    
    categories, box_data = result
    
    # Build lookup: category -> box_data
    cat_to_box = dict(zip(categories, box_data))
    
    # Merge all categories in order: primary first, then secondary
    all_categories = []
    for c in primary_categories:
        if c in cat_to_box and c not in all_categories:
            all_categories.append(c)
    for c in secondary_categories:
        if c in cat_to_box and c not in all_categories:
            all_categories.append(c)
    # Add any remaining categories not explicitly assigned (put on primary by default)
    for c in categories:
        if c not in all_categories:
            all_categories.append(c)
            if c not in primary_categories:
                primary_categories.append(c)
    
    if not all_categories:
        return {"error": "No valid categories found for dual-axis boxplot"}
    
    primary_set = set(primary_categories)
    secondary_set = set(secondary_categories)
    
    # Build series data: use '-' placeholder for categories not in this series
    primary_data = []
    secondary_data = []
    for cat in all_categories:
        if cat in primary_set and cat in cat_to_box:
            primary_data.append(cat_to_box[cat])
        else:
            primary_data.append("-")
        
        if cat in secondary_set and cat in cat_to_box:
            secondary_data.append(cat_to_box[cat])
        else:
            secondary_data.append("-")
    
    config = {
        "title": {
            "text": title or f"Boxplot by {category_column} (dual axis)"
        },
        "tooltip": {
            "trigger": "item",
            "confine": True
        },
        "legend": {
            "data": [
                primary_axis_name or "Primary",
                secondary_axis_name or "Secondary"
            ],
            "top": "5%"
        },
        "grid": {
            "left": "10%",
            "right": "10%",
            "bottom": "15%",
            "top": "15%",
            "containLabel": True
        },
        "xAxis": {
            "type": "category",
            "data": all_categories,
            "boundaryGap": True,
            "nameGap": 30,
            "splitArea": {
                "show": False
            },
            "splitLine": {
                "show": False
            }
        },
        "yAxis": [
            {
                "type": "value",
                "name": primary_axis_name or "Primary",
                "scale": True,
                "splitArea": {
                    "show": True
                }
            },
            {
                "type": "value",
                "name": secondary_axis_name or "Secondary",
                "scale": True,
                "splitArea": {
                    "show": False
                }
            }
        ],
        "series": [
            {
                "name": primary_axis_name or "Primary",
                "type": "boxplot",
                "yAxisIndex": 0,
                "data": primary_data
            },
            {
                "name": secondary_axis_name or "Secondary",
                "type": "boxplot",
                "yAxisIndex": 1,
                "data": secondary_data,
                "itemStyle": {
                    "color": "#b8c5f2"
                }
            }
        ]
    }
    
    return config


def echarts_boxplot_multi_column(value_columns: list, query_result: dict, title: str = "", orientation: str = "vertical") -> dict:
    """Generate side-by-side boxplots for multiple columns using ECharts dataset API.
    Each column becomes a category on the axis with its own boxplot.
    Data is restructured so each row represents one value with its column name.
    
    Args:
        value_columns: List of column names to create boxplots for
        query_result: Query result dict with 'data' key containing list of row dicts
        title: Optional chart title
        orientation: "vertical" or "horizontal" for chart orientation
        
    Returns:
        ECharts configuration dictionary
    """
    if not query_result or not query_result.get("data"):
        return {"error": "No query results available"}
    
    if not value_columns or not isinstance(value_columns, list):
        return {"error": "value_columns must be a non-empty list"}
    
    data = query_result["data"]
    
    # Restructure data: each row becomes [column_name, value]
    # This allows ECharts to group by column name
    source_data = []
    for row in data:
        for col in value_columns:
            value = row.get(col)
            if value is not None:
                try:
                    source_data.append([col, float(value)])
                except (ValueError, TypeError):
                    pass  # Skip non-numeric values
    
    if not source_data:
        return {"error": "No valid data available"}
    
    if orientation == "horizontal":
        # Horizontal orientation
        config = {
            "dataset": [
                {
                    "id": "raw",
                    "source": source_data,
                    "dimensions": ["column", "value"]
                },
                {
                    "id": "aggregate",
                    "fromDatasetId": "raw",
                    "transform": [
                        {
                            "type": "ecSimpleTransform:aggregate",
                            "config": {
                                "resultDimensions": [
                                    {"name": "min", "from": "value", "method": "min"},
                                    {"name": "Q1", "from": "value", "method": "Q1"},
                                    {"name": "median", "from": "value", "method": "median"},
                                    {"name": "Q3", "from": "value", "method": "Q3"},
                                    {"name": "max", "from": "value", "method": "max"},
                                    {"name": "column", "from": "column"}
                                ],
                                "groupBy": "column"
                            }
                        }
                    ]
                }
            ],
            "title": {
                "text": title or f"Boxplot comparison of {', '.join(value_columns)}"
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
                "name": "value",
                "nameLocation": "middle",
                "nameGap": 30,
                "scale": True,
                "splitArea": {
                    "show": True
                }
            },
            "yAxis": {
                "type": "category",
                "boundaryGap": True,
                "nameGap": 30,
                "splitArea": {
                    "show": False
                },
                "splitLine": {
                    "show": False
                }
            },
            "series": [
                {
                    "name": "boxplot",
                    "type": "boxplot",
                    "datasetId": "aggregate",
                    "itemStyle": {
                        "color": "#b8c5f2"
                    },
                    "encode": {
                        "x": ["min", "Q1", "median", "Q3", "max"],
                        "y": "column",
                        "itemName": ["column"],
                        "tooltip": ["min", "Q1", "median", "Q3", "max"]
                    }
                }
            ]
        }
    else:
        # Vertical orientation (default)
        config = {
            "dataset": [
                {
                    "id": "raw",
                    "source": source_data,
                    "dimensions": ["column", "value"]
                },
                {
                    "id": "aggregate",
                    "fromDatasetId": "raw",
                    "transform": [
                        {
                            "type": "ecSimpleTransform:aggregate",
                            "config": {
                                "resultDimensions": [
                                    {"name": "min", "from": "value", "method": "min"},
                                    {"name": "Q1", "from": "value", "method": "Q1"},
                                    {"name": "median", "from": "value", "method": "median"},
                                    {"name": "Q3", "from": "value", "method": "Q3"},
                                    {"name": "max", "from": "value", "method": "max"},
                                    {"name": "column", "from": "column"}
                                ],
                                "groupBy": "column"
                            }
                        }
                    ]
                }
            ],
            "title": {
                "text": title or f"Boxplot comparison of {', '.join(value_columns)}"
            },
            "tooltip": {
                "trigger": "item",
                "confine": True
            },
            "grid": {
                "left": "10%",
                "right": "10%",
                "bottom": "15%",
                "top": "15%",
                "containLabel": True
            },
            "xAxis": {
                "type": "category",
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
                "name": "value",
                "scale": True,
                "splitArea": {
                    "show": True
                }
            },
            "series": [
                {
                    "name": "boxplot",
                    "type": "boxplot",
                    "datasetId": "aggregate",
                    "encode": {
                        "x": "column",
                        "y": ["min", "Q1", "median", "Q3", "max"],
                        "itemName": ["column"],
                        "tooltip": ["min", "Q1", "median", "Q3", "max"]
                    }
                }
            ]
        }
    
    return config
