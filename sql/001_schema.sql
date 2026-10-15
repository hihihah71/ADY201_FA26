create table  if not exists regions(
    region_id varchar primary key,
    name varchar not null,
    boundary_path varchar not null,
    enabled boolean not null default true 
);