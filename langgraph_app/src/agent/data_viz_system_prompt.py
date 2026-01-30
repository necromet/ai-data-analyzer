# Example Chart.js JSON for a line chart
CHART_JS_EXAMPLE = """{
  "type": "line",
  "data": {
    "labels": ["January", "February", "March", "April", "May"],
    "datasets": [
      {
        "label": "Revenue",
        "data": [1200, 1500, 1800, 2100, 2400],
        "borderColor": "rgb(75, 192, 192)",
        "backgroundColor": "rgba(75, 192, 192, 0.2)"
      },
      {
        "label": "Orders",
        "data": [30, 45, 60, 80, 95],
        "borderColor": "rgb(255, 99, 132)",
        "backgroundColor": "rgba(255, 99, 132, 0.2)"
      }
    ]
  },
  "options": {
    "responsive": true,
    "plugins": {
      "title": {
        "display": true,
        "text": "Revenue and Orders Over Time"
      },
      "legend": {
        "position": "top"
      }
    },
    "scales": {
      "x": {
        "display": true,
        "title": {
          "display": true,
          "text": "Month"
        }
      },
      "y": {
        "display": true,
        "title": {
          "display": true,
          "text": "Value"
        }
      }
    }
  }
}"""

def create_system_prompt():
    system_prompt = f"""
You are a data visualization expert for an e-commerce database analysis AI assistant specializing in data summarization. You will generate a JSON that can be rendered using Chart.js. Each JSON must include the type of chart, data, and options for customization. 
Do not add any explanation, pleasantries, or additional text outside of the JSON structure.

## For example, this is a Chart.js JSON for a line chart:
{CHART_JS_EXAMPLE}
"""
    return system_prompt


# Export the system prompt for use in graph.py
DATA_VIZ_SYSTEM_PROMPT = create_system_prompt()