-- guard against LAG comparing non-adjacent days at the window edges
with daily as (
	select
		c.city_id,
		c.name,
		f.forecast_date_local,
		avg(f.temperature_c) as avg_temp_c
	from hourly_forecast f
	join city c on c.city_id = f.city_id
	group by c.city_id, f.forecast_date_local
),
with_lag as (
	select
		name,
		forecast_date_local,
		round(avg_temp_c, 1) as avg_temp_c,
		lag(avg_temp_c) over (partition by city_id order by forecast_date_local) as prev_avg_temp_c,
		lag(forecast_date_local) over (partition by city_id order by forecast_date_local) as prev_date
	from daily
)
select
	name,
	forecast_date_local,
	avg_temp_c,
	case
		when julianday(forecast_date_local) - julianday(prev_date) = 1
			then round(avg_temp_c - prev_avg_temp_c, 1)
		else null
	end as delta_vs_prev_day_c
from with_lag
order by name, forecast_date_local;
