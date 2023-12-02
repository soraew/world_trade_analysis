
/* TASK 3 */

/* 3.0 create csvs for 2017 data */
/* 3.0.1 create empty table baci_xab */

create table baci_xab(year INT(5), economy INT(15), economy_label VARCHAR(200), partner INT(15), partner_label VARCHAR(200), flow INT(5), flow_label VARCHAR(10), product VARCHAR(15), product_label VARCHAR(200), KUSD FLOAT(22), KUSD_footnote FLOAT(10)); 

/* fill baci_xab with data */
load data local infile '/private/tmp/xab' into table baci_xab fields terminated by ',' enclosed by '"' lines terminated by '\n' ignore 1 rows;


/* 3.1 compute RCA for USA and China, 2017 */
/* 3.1.1 get sum within countries */

/* xaa-2017 */
select 'product', 'product_label', 'economy_label', 'flow', 'sum_kusd'
union all
select product, product_label, economy_label, flow, sum(KUSD) as sum_kusd
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


/* merge above tables into one */
create table product_2017_19 as
select * from product_2017
union all
select * from product_2018
union all
select * from product_2019
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


