def echarts_line(df, x_column: str, y_column: str) -> dict:
    return {
      "xAxis": {
        "type": "category",
        "data": df[x_column].tolist()
      },
      "yAxis": {
        "type": "value"
      },
      "series": [
        {
          "data": df[y_column].tolist(),
          "type": "line"
        }
      ]
    }

def echarts_bar(df, x_column: str, y_column: str) -> dict:
    return {
      "xAxis": {
        "type": "category",
        "data": df[x_column].tolist()
      },
      "yAxis": {
        "type": "value"
      },
      "series": [
        {
          "data": df[y_column].tolist(),
          "type": "bar"
        }
      ]
    }

def echarts_pie(name_column: str, value_column: str, title: str = "Distribution") -> dict:
    """Generate pie charts for echarts.js using the latest query result data."""
    return {
        "title": {
            "text": title,
            "left": "center"
        },
        "tooltip": {
            "trigger": "item"
        },
        "legend": {
            "orient": "vertical",
            "left": "left"
        },
        "series": [
            {
                "name": name_column,
                "type": "pie",
                "radius": "50%",
                "data": [
                    {"value": "{{value_column}}", "name": "{{name_column}}"}
                ],
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowOffsetX": 0,
                        "shadowColor": "rgba(0, 0, 0, 0.5)"
                    }
                }
            }
        ]
    }

def echarts_scatter(x_column: str, y_column: str, title: str = "Scatter Plot") -> dict:
    """Generate scatter plots for echarts.js using the latest query result data."""
    return {
        "title": {
            "text": title,
            "left": "center"
        },
        "tooltip": {
            "trigger": "item"
        },
        "xAxis": {
            "type": "value"
        },
        "yAxis": {
            "type": "value"
        },
        "series": [
            {
                "symbolSize": 10,
                "data": [[f"{{x_column}}", f"{{y_column}}"]],
                "type": "scatter"
            }
        ]
    }

def data_vis_system_prompt(user_input: str = "", query_result: str = "", column_names: list[str] = None, row_example: dict = None) -> str:
    """This is the system prompt for the data visualization agent."""
    prompt = f"""
User Input: {user_input}

Query Result: {query_result}

Column Names: {column_names}

Row Example: {row_example}

dataframe or data is a variable named "records"

system prompt:
You are a data visualization expert for an e-commerce database, provided with 
1. User input
2. To do list
3. Column names
4. Row example

Your role:
<role>
Synthesize information from the query result, column names, and row example to determine what type of chart, title, x_columns and y_columns would best represent the data in response to the user input. Your output will be a JSON Object in the format below:
{{
    "chart_type": "line/bar/pie/scatter",
    "title": "chart title",
    "data": "records",
    "x_columns": "name of important column",
    "y_columns": "name of important column"
}}
No explanation, pleasantries, or additional text. Your chart option is limited to line, bar, pie, and scatter charts.
</role>
"""
    return prompt
