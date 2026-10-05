create schema if not exists staging;

create table if not exists staging.poi (
	id bigint not null,
	lat double precision,
	lon double precision,
	amenity varchar(50),
	name varchar(1000)
);

copy staging.poi (
	id,
	lat,
	lon,
	amenity,
	name
)
from 'D:\FPT\SEMESTER\FALL26\ADY201m\Group Assignment\ADY201_FA26\Flatten\Systhesis.csv'
with (
	format csv,
	header true,
	encoding 'utf8'
);

select count(*) from staging.poi where staging.poi.name is not null;

create table if not exists staging.grid_cell (
	cell_id int not null,
	row_id int,
	col_id int,
	min_lat double precision,
	max_lat double precision,
	min_lon double precision,
	max_lon double precision
)

insert into staging.grid_cell (
	cell_id,
	row_id,
	col_id,
	min_lat,
	max_lat,
	min_lon,
	max_lon
)
with b as (
	select
		20.5645154 as min_lat,
		21.3854176 as max_lat,
		105.2889615 as min_lon,_
		106.0200407 as max_lon
)
select
	r + c * 200 + 1 as cell_id,
	r as row_id,
	c as col_id,
	b.min_lat + r * (b.max_lat - b.min_lat) / 200 as min_lat,
	b.min_lat + (r + 1) * (b.max_lat - b.min_lat) / 200 as max_lat,
	b.min_lon + c * (b.max_lon - b.min_lon) / 200 as min_lon,
	b.min_lon + (c + 1) * (b.max_lon - b.min_lon) / 200 as max_lon
from generate_series(0, 199) as r
cross join generate_series(0, 199) as c
cross join b;

truncate table staging.grid_cell;

select * from staging.grid_cell;

alter table staging.poi add column cell_id int;

update staging.poi as p
set cell_id = g.cell_id
from staging.grid_cell as g
where 
	p.lat >= g.min_lat and
	p.lat < g.max_lat and
	p.lon >= g.min_lon and
	p.lon < g.max_lon;


select
	p.cell_id,
	g.min_lat,
	g.max_lat,
	g.min_lon,
	g.max_lon,
	count(p.id) as num
from (select * from staging.poi where amenity = 'fast_food') as p
right join staging.grid_cell g on p.cell_id = g.cell_id
group by
	p.cell_id,
	g.min_lat,
	g.max_lat,
	g.min_lon,
	g.max_lon
order by num desc;


select * from staging.poi p where p.cell_id is null;


