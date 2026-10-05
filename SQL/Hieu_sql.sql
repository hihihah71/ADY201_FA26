create table if not exists staging.poi(
	id bigint not null,
	lat double precision,
	lon double precision,
	amenity varchar(50),
	name varchar(1000)
)

copy staging.poi(
	id,
	lat,
	lon,
	amenity,
	name
)
from 'D:\ADY201_FA26\Flatten\Systhesis.csv'
with(
	format csv,
	header true,
	encoding 'utf8'
);

create table if not exists staging.grid_cell(
	cell_id int primary key,
	row_id int not null,
	col_id int not null,
	min_lat double precision not null,
	max_lat  double precision not null,
	min_lon double precision not null,
	max_lon double precision not null
);

TRUNCATE TABLE staging.grid_cell;

INSERT INTO staging.grid_cell (
    cell_id, row_id, col_id,
    min_lat, max_lat, min_lon, max_lon
)
WITH b AS (
    SELECT
        20.5645154::DOUBLE PRECISION AS min_lat,
        21.3854176::DOUBLE PRECISION AS max_lat,
        105.2889615::DOUBLE PRECISION AS min_lon,
        106.0200407::DOUBLE PRECISION AS max_lon
)
SELECT
    r + c * 200 + 1 AS cell_id,
    r AS row_id,
    c AS col_id,
    b.min_lat + r       * (b.max_lat - b.min_lat) / 200.0 AS min_lat,
    b.min_lat + (r + 1) * (b.max_lat - b.min_lat) / 200.0 AS max_lat,
    b.min_lon + c       * (b.max_lon - b.min_lon) / 200.0 AS min_lon,
    b.min_lon + (c + 1) * (b.max_lon - b.min_lon) / 200.0 AS max_lon
FROM generate_series(0, 199) AS r
CROSS JOIN generate_series(0, 199) AS c
CROSS JOIN b;

ALTER TABLE staging.poi
ADD COLUMN IF NOT EXISTS cell_id INT;

UPDATE staging.poi AS p
SET cell_id = g.cell_id
FROM staging.grid_cell AS g
WHERE p.lat >= g.min_lat
  AND p.lat <  g.max_lat
  AND p.lon >= g.min_lon
  AND p.lon <  g.max_lon;












