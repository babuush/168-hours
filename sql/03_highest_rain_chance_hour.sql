-- nulls last so a real high doesn't lose to a null; ties break to the
-- earliest hour via forecast_time_utc.
select
	name,
	forecast_date_local,
	forecast_hour_local,
	precip_prob_pct
from (
	select
		c.name,
		f.forecast_date_local,
		f.forecast_hour_local,
		f.precip_prob_pct,
		row_number() over (
			partition by f.city_id, f.forecast_date_local
			order by f.precip_prob_pct desc nulls last, f.forecast_time_utc
		) as rn
	from hourly_forecast f
	join city c on c.city_id = f.city_id
)
where rn = 1
order by name, forecast_date_local;
