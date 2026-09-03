-- literal reading: max-min across the whole window. differs from "biggest
-- single-day swing", which needs a per-day max-min compared across days.
select
	c.name,
	max(f.temperature_c) as max_temp_c,
	min(f.temperature_c) as min_temp_c,
	round(max(f.temperature_c) - min(f.temperature_c), 1) as temp_range_c
from hourly_forecast f
join city c on c.city_id = f.city_id
group by c.city_id
order by temp_range_c desc;
