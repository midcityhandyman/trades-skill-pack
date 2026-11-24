# Waste factors (SAMPLE values)

These are illustrative defaults baked into `scripts/takeoff.py`. They are not a trade
standard. Replace them with the numbers your own jobs have shown.

| Material | Sample waste | Raise it when |
|---|---|---|
| Drywall | 10% | many corners, soffits, vaulted ceilings |
| Tile, straight lay | 10% | small rooms with many cuts |
| Tile, diagonal lay | 15% | large format tile |
| Tile, herringbone | 20% | narrow rooms |
| Paint | 5% | rough or unprimed surfaces, deep colors |
| Baseboard trim | 10% | many short walls, stain grade matching |

Sample paint coverage: 350 sqft per gallon per coat.

Override per material in the room JSON, as a fraction:

```json
"tile": {"tile_in": [12, 24], "pattern": "diagonal", "waste": 0.18}
```

A waste value of 1 or more is rejected, because it almost always means a percent was
typed where a fraction was expected.
