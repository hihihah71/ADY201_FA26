create schema if not exists staging;

create table if not exists staging.poi(
	id bigint not null,
	lat double precision not null,
	lon double precision not null,
	amenity varchar(50) not null,
	name varchar(1000));

copy staging.poi(
	id,
	lat,
	lon,
	amenity,
	name
)
from 'G:\ADY201_FA26\Flatten\Systhesis.csv'
with(
	format csv,
	header true,
	encoding 'utf-8'
);

select * from staging.poi;

select count(*) from staging.poi
where name is not null;

create table if not exists staging.grid_cell(
	cell_id int primary key,
	row_id int not null,
	col_id int not null,
	min_lat double precision not null,
	max_lat double precision not null,
	min_lon double precision not null,
	max_lon double precision not null
);

truncate staging.grid_cell;

insert into staging.grid_cell(
	cell_id,row_id,col_id,
	min_lat,max_lat,min_lon,max_lon
)
with b as(
	select
        20.5645154::double precision as min_lat,
        21.3854176::double precision as max_lat,
        105.2889615::double precision as min_lon,
        106.0200407::double precision as max_lon
)
select		
    r + c * 200 + 1 as cell_id,
    r as row_id,
    c as col_id,
    b.min_lat + r       * (b.max_lat - b.min_lat) / 200.0 as min_lat,
    b.min_lat + (r + 1) * (b.max_lat - b.min_lat) / 200.0 as max_lat,
    b.min_lon + c       * (b.max_lon - b.min_lon) / 200.0 as min_lon,
    b.min_lon + (c + 1) * (b.max_lon - b.min_lon) / 200.0 as max_lon

from generate_series(0,199) as r
cross join generate_series(0,199) as c
cross join b;

alter table staging.poi add column if not exists cell_id int;

update staging.poi as p
set cell_id = g.cell_id
from staging.grid_cell as g
where p.lat >= g.min_lat
	and p.lat < max_lat
	and p.lon >= g.min_lon
	and p.lat < g.max_lon;

select * from staging.poi;


