# Markdown Renderer Test

This tests all the markdown features used in your data analysis output.

## Text Formatting

Bottom line: Customers have a **slightly higher** average order value than sellers ($160.99 vs. $160.61), and the data suggests order volume and geographic/product breakdowns should be examined further to understand *return rates* and product mix drivers.

## Code Blocks with JSON (ECharts)

```json
{
  "color": [
    "#5b51d8",
    "#f2c14e",
    "#a0b4d4",
    "#c0bfcc",
    "#4a3a45"
  ],
  "tooltip": {
    "trigger": "axis",
    "axisPointer": {
      "type": "shadow"
    }
  },
  "xAxis": {
    "type": "category",
    "data": [
      "customer",
      "seller"
    ],
    "name": "Role"
  },
  "yAxis": {
    "type": "value",
    "name": "Average Order Value (USD)"
  },
  "series": [
    {
      "data": [
        160.99,
        160.61
      ],
      "type": "bar",
      "showBackground": true,
      "backgroundStyle": {
        "color": "rgba(180, 180, 180, 0.2)"
      }
    }
  ],
  "title": {
    "text": "Average Order Value (USD) by Role",
    "left": "center"
  }
}
```

## Bullet Lists

- **Average order value**: The average order value for the customer role is **$160.99**, which is marginally higher than the seller role at **$160.61** (~0.24% higher).
- **Order volume context**: Customers account for **99,440** orders vs. sellers' **98,665** — both roles show very similar volumes, so small differences in AOV may meaningfully affect revenue if scaled.
- **Additional analyses needed**: Return-rate patterns, product mix contributions, and geographic distribution aren't present in the provided summary and should be joined in from the orders, order_items, products, order_reviews and customers datasets.

---

## Tables

Summary table

| Role     | Average Order Value (USD) | Order Count |
|----------|---------------------------:|------------:|
| customer | **$160.99**                | **99,440**  |
| seller   | **$160.61**                | **98,665**  |

## Next Steps List

Next recommended steps (quick list)
- Calculate return rates by role and by `product_id` using order_items and orders (flag returned/cancelled orders) to see if one role has systematically higher returns.
- Break down AOV by `product_category` and by top-N SKUs to identify which categories drive the small AOV difference.
- Map orders by `customer_state` and `seller_state` (using customers and sellers datasets) to spot geographic pockets of higher returns or higher AOV.
- Correlate review scores and return events from `order_reviews` to identify product-quality or expectation issues.

---

## Links

For more information, visit [the documentation](https://example.com).

## Inline Code

Use the `customer_id` field to join with the `orders` table.

## Blockquote

> This is an important note about the data analysis process and methodology used in this analysis.
