create table city (
	city_id integer primary key,
	slug unique,
	name text,
	latitude real,
	longitude real
);

insert into city (slug, name, latitude, longitude) values
	('bangkok', 'Bangkok', 13.7563, 100.5018),
	('chiang-mai', 'Chiang Mai', 18.7883, 98.9853),
	('phuket', 'Phuket', 7.8804, 98.3923),
	('khon-kaen', 'Khon Kaen', 16.4322, 102.8236),
	('hat-yai', 'Hat Yai', 7.0086, 100.4747);

create table hourly_forecast (
	city_id integer references city(city_id),
	forecast_time_utc text,
	forecast_date_local text,
	forecast_hour_local integer,
	temperature_c real,
	precipitation_mm real,
	precip_prob_pct real,
	ingested_at_utc text,
	primary key (city_id, forecast_time_utc)
);

create index idx_hourly_forecast_city_date on hourly_forecast (city_id, forecast_date_local);
