
/* TASK 3 */

/* 3.0 create csvs for 2017 data */
/* 3.0.1 create empty table baci_xab */

create table baci_xab(year INT(5), economy INT(15), economy_label VARCHAR(200), partner INT(15), partner_label VARCHAR(200), flow INT(5), flow_label VARCHAR(10), product VARCHAR(15), product_label VARCHAR(200), KUSD FLOAT(22), KUSD_footnote FLOAT(10));

/* fill baci_xab with data */
load data local infile '/private/tmp/xab' into table baci_xab fields terminated by ',' enclosed by '"' lines terminated by '\n' ignore 1 rows;


/* 3.1 compute RCA for USA and China, 2017 */
/* 3.1.1 get sum within countries */

/* xaa-2017 */
select 'product', 'product_label', 'economy_label', 'flow', 'sum_kusd' union all select product, product_label, economy_label, flow, sum(KUSD) as sum_kusd
from baci_xaa
where year = 2017
group by product, product_label, economy_label, flow
into outfile '/private/tmp/tradewar_tmp/rca_n_xaa_2017.csv'
fields terminated by ','
enclosed by '"'
lines terminated by '\n'
;

/* xab-2017 */
select 'product', 'product_label', 'economy_label', 'flow', 'sum_kusd'
union all
select product, product_label, economy_label, flow, sum(KUSD) as sum_kusd
from baci_xab
where year = 2017
group by product, product_label, economy_label, flow
into outfile '/private/tmp/tradewar_tmp/rca_n_xab_2017.csv'
fields terminated by ','
enclosed by '"'
lines terminated by '\n'
;

/* 3.2 create csvs for 2019 data */
/* 3.2.1 create empty table baci_xac */
create table baci_xac(year INT(5), economy INT(15), economy_label VARCHAR(200), partner INT(15), partner_label VARCHAR(200), flow INT(5), flow_label VARCHAR(10), product VARCHAR(15), product_label VARCHAR(200), KUSD FLOAT(22), KUSD_footnote FLOAT(10)); 
/* fill baci_xac with data */
load data local infile '/private/tmp/xac' into table baci_xac fields terminated by ',' enclosed by '"' lines terminated by '\n' ignore 1 rows;


/* 3.3. create table product_2017 */
create table product_2017 as
select product, product_label, economy_label, partner_label, flow, KUSD
from baci_xaa
where
    year = 2017
    and product in ('222', '334', '728', '752', '759', '764', '778', '784', '821', '874')
union all
select product, product_label, economy_label, partner_label, flow, KUSD
from baci_xab
where
    year = 2017
    and product in ('222', '334', '728', '752', '759', '764', '778', '784', '821', '874')
;

/* 3.4. create table product_2018 */
create table product_2018 as
select product, product_label, economy_label, partner_label, flow, KUSD
from baci_xab
where
    year = 2018
    and product in ('222', '334', '728', '752', '759', '764', '778', '784', '821', '874')
;

/* 3.5. create table product_2019 */
create table product_2019 as
select product, product_label, economy_label, partner_label, flow, KUSD
from baci_xab
where
    year = 2019
    and product in ('222', '334', '728', '752', '759', '764', '778', '784', '821', '874')
union all
select product, product_label, economy_label, partner_label, flow, KUSD
from baci_xac
where
    year = 2019
    and product in ('222', '334', '728', '752', '759', '764', '778', '784', '821', '874')
;

create table baci_xae(year INT(5), economy INT(15), economy_label VARCHAR(200), partner INT(15), partner_label VARCHAR(200), flow INT(5), flow_label VARCHAR(10), product VARCHAR(15), product_label VARCHAR(200), KUSD FLOAT(22), KUSD_footnote FLOAT(10)); 
load data local infile '/private/tmp/xae' into table baci_xae fields terminated by ',' enclosed by '"' lines terminated by '\n' ignore 1 rows;

create table product_2020 as
select product, product_label, economy_label, partner_label, flow, KUSD
from baci_xac
where
    year = 2020
    and product in ('222', '334', '728', '752', '759', '764', '778', '784', '821', '874')
union all
select product, product_label, economy_label, partner_label, flow, KUSD
from baci_xad
where
    year = 2020
    and product in ('222', '334', '728', '752', '759', '764', '778', '784', '821', '874')
;
alter table product_2020
add column year int first;
update product_2020 set year = 2020;

create table product_2021 as
select product, product_label, economy_label, partner_label, flow, KUSD
from baci_xad
where
    year = 2021
    and product in ('222', '334', '728', '752', '759', '764', '778', '784', '821', '874')
union all
select product, product_label, economy_label, partner_label, flow, KUSD
from baci_xae
where
    year = 2021
    and product in ('222', '334', '728', '752', '759', '764', '778', '784', '821', '874')
;
alter table product_2021
add column year int first;
update product_2021 set year = 2021;


/* merge above tables into one */
create table product_2017_19 as
select * from product_2017
union all
select * from product_2018
union all
select * from product_2019
;

create table product_2017_21 as
select * from product_2017_19
union all
select * from product_2020
union all
select * from product_2021
;
select
'year', 'product', 'product_label', 'economy_label', 'partner_label', 'flow', 'KUSD'
union all
select
year, product, product_label, economy_label, partner_label, flow, KUSD
from product_2017_21
into outfile '/private/tmp/product_2017_21.csv'
fields terminated by ','
enclosed by '"'
lines terminated by '\n'
;

/* calculate exposure of United States of America to China */
select KUSD 
from 
    baci_xab
where
    economy = 842
    and flow = 1 -- Imports
    and year = 2017
    and product_label = 'TOTAL ALL PRODUCTS';
;

-- creating a table for the commodity codes
create table s3_codes(
classification VARCHAR(10),
code VARCHAR(10),
description VARCHAR(200),
code_parent VARCHAR(10),
level INT(5),
isleaf INT(2));
load data local infile '/private/tmp/commodity_code.csv'
into table s3_codes fields terminated by ','
enclosed by '"' lines terminated by '\n' ignore 1 rows;
select code, description
from s3_codes
where level=3;

-- getting top imports of USA for 2017
create table us_trade_2017 as
select product, product_label, economy_label, partner_label, flow, KUSD
from baci_xab
where
    year = 2017
    and economy_label = "United States of America"
;

select
'economy_label', 'partner_label', 'product','product_label', 'flow', 'KUSD'
union all
(select economy_label, partner_label, product, product_label, flow, sum(KUSD)
from us_trade_2017
where economy_label = "United States of America"
group by economy_label, partner_label, product, product_label, flow)
into outfile '/private/tmp/us_trade_2017.csv'
fields terminated by ','
enclosed by '"'
lines terminated by '\n'
;

-- getting top exports of China for 2017
create table ch_trade_2017 as
select product, product_label, economy_label, partner_label, flow, KUSD
from baci_xaa
where
    year = 2017
    and economy_label = "China"
;

select
'economy_label', 'partner_label', 'product','product_label', 'flow', 'KUSD'
union all
(select economy_label, partner_label, product, product_label, flow, sum(KUSD)
from ch_trade_2017
where economy_label = "China"
group by economy_label, partner_label, product, product_label, flow)
into outfile '/private/tmp/ch_trade_2017.csv'
fields terminated by ','
enclosed by '"'
lines terminated by '\n'
;
