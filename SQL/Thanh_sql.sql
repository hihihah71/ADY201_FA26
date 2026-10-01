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



