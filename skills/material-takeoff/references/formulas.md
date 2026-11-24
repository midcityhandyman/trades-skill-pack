# Formulas and rounding

All order quantities round up to the next whole purchasable unit.

## Geometry (rectangular room)

- Floor area = length x width
- Gross wall area = 2 x (length + width) x height
- Net wall area = gross wall area minus door and window areas (never below zero)
- Perimeter = 2 x (length + width)

## Drywall

- Area = net wall area, plus floor area when `include_ceiling` is true
- Sheets = ceil(area x (1 + waste) / sheet area)
- Sheet areas: 4x8 = 32 sqft, 4x10 = 40 sqft, 4x12 = 48 sqft

## Tile

- Area = floor area unless `area_sqft` is given (use that for walls or a shower)
- Tiles = ceil(area x (1 + waste) / (tile width in x tile length in / 144))
- Boxes = ceil(tiles / tiles per box) when `tiles_per_box` is given

## Paint

- Area = net wall area, plus floor area when `include_ceiling` is true
- Gallons = ceil(area x coats x (1 + waste) / coverage)

## Baseboard trim

- Linear feet = perimeter minus door widths
- Sticks = ceil(linear feet x (1 + waste) / stick length)

## Not covered

Joint compound, tape, screws, thinset, grout, primer, casing and crown are not
calculated. List them for the user as items to add by hand.
