from numba.core.typing.builtins import bound_function
import numpy as np
import geopandas as gpd
from shapely.geometry import box
import json

def create_cells(boundary, cell_size_m):
    minx, miny, maxx, maxy = boundary.total_bounds
    polygons = []

    for x in np.arange(minx, maxx, cell_size_m):
        for y in np.arange(miny, maxy, cell_size_m):
            polygons.append(box(x, y, x + cell_size_m, y + cell_size_m))
    
    grid = gpd.GeoDataFrame(geometry=polygons, crs=boundary.crs)
    cells = gpd.clip(grid, boundary)
    cells = cells[~cells.geometry.is_empty].copy()
    cells["cell_id"] = [f"cell_{i:06d}" for i in range(len(cells))]
    cells["cell_area_km2"] = cells.area / 1000000
    return cells[["cell_id", "cell_area_km2", "geometry"]]

def get_grid_cell(boundary, grid_size):    
    boundary = boundary.to_crs(boundary.estimate_utm_crs())
    cells = create_cells(boundary, grid_size)
    cells["points"] = cells.geometry.representative_point()
    return cells

