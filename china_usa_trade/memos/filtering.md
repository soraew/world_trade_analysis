# filtering
## mysql approach

### create table
(done)
```sql
create table baci_xaa(year INT(5), economy INT(15), economy_label VARCHAR(200), partner INT(15), partner_label VARCHAR(200), flow INT(5), flow_label VARCHAR(10), product VARCHAR(15), product_label VARCHAR(200), KUSD FLOAT(22), KUSD_footnote FLOAT(10)); 
```
(done)
```sql
set global local_infile=ON;
```
(done)
```sql
load data local infile '/private/tmp/xaa' into table baci_xaa fields terminated by ',' enclosed by '"' lines terminated by '\n' ignore 1 rows;
```

### create csvs for computing RCA
(this not working tho)
```sql
with cte as (select sum(KUSD) as sum_total from baci_xaa)
select product, product_label, sum(KUSD)/cte.sum_total as product_ratio
from baci_xaa
where year = 2016
group by product, product_label
order by product_ratio
```
(done)
```sql
select 'product', 'product_label', 'sum_kusd'
union all
select product, product_label, sum(KUSD) as sum_kusd
from baci_xaa
where year = 2016
group by product, product_label
into outfile '/private/tmp/RCA_t.csv'
fields terminated by ','
enclosed by '"'
lines terminated by '\n'
;
```
(done)
```sql
select 'product', 'product_label', 'economy_label', 'flow', 'sum_kusd'
union all
select product, product_label, economy_label, flow, sum(KUSD) as sum_kusd
from baci_xaa
where year = 2016
group by product, product_label, economy_label, flow
into outfile '/private/tmp/RCA_n.csv'
fields terminated by ','
enclosed by '"'
lines terminated by '\n'
;
```
