-- group on forecast_date_local, not the UTC timestamp
select
	c.name,
	f.forecast_date_local,
	round(avg(f.temperature_c), 1) as avg_temp_c,
	max(f.temperature_c) as max_temp_c,
	min(f.temperature_c) as min_temp_c
from hourly_forecast f
join city c on c.city_id = f.city_id
group by c.city_id, f.forecast_date_local
order by c.name, f.forecast_date_local;
