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

