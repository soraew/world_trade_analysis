
products = 
('281', '764', '874', '782', '759', '333', '728',
 '334', '752', '821', '776', '784', '781', '778', '222', '971', '542')

    and products in ('281', '764', '874', '782', '759', '333', '728',
     '334', '752', '821', '776', '784', '781', '778', '222', '971', '542')
/* 3.3. create table top_ex_imp_2017 */
create table top_ex_imp_2017 as
select year, product, product_label, economy_label, partner_label, flow, KUSD
from baci_xaa
where
    year = 2017
    and products in ('281', '764', '874', '782', '759', '333', '728',
     '334', '752', '821', '776', '784', '781', '778', '222', '971', '542')
union all
select year, product, product_label, economy_label, partner_label, flow, KUSD
from baci_xab
where
    year = 2017
    and products in ('281', '764', '874', '782', '759', '333', '728',
     '334', '752', '821', '776', '784', '781', '778', '222', '971', '542')
;

/* 3.4. create table top_ex_imp_2018 */
create table top_ex_imp_2018 as
select year, product, product_label, economy_label, partner_label, flow, KUSD
from baci_xab
where
    year = 2018
    and products in ('281', '764', '874', '782', '759', '333', '728',
     '334', '752', '821', '776', '784', '781', '778', '222', '971', '542')
;

/* 3.5. create table top_ex_imp_2019 */
create table top_ex_imp_2019 as
select year, product, product_label, economy_label, partner_label, flow, KUSD
from baci_xab
where
    year = 2019
    and products in ('281', '764', '874', '782', '759', '333', '728',
     '334', '752', '821', '776', '784', '781', '778', '222', '971', '542')
union all
select year, product, product_label, economy_label, partner_label, flow, KUSD
from baci_xac
where
    year = 2019
    and products in ('281', '764', '874', '782', '759', '333', '728',
     '334', '752', '821', '776', '784', '781', '778', '222', '971', '542')
;

create table top_ex_imp_2020 as
select year, product, product_label, economy_label, partner_label, flow, KUSD
from baci_xac
where
    year = 2020
    and products in ('281', '764', '874', '782', '759', '333', '728',
     '334', '752', '821', '776', '784', '781', '778', '222', '971', '542')
union all
select year, product, product_label, economy_label, partner_label, flow, KUSD
from baci_xad
where
    year = 2020
    and products in ('281', '764', '874', '782', '759', '333', '728',
     '334', '752', '821', '776', '784', '781', '778', '222', '971', '542')
;
alter table product_2020
add column year int first;
update product_2020 set year = 2020;

create table top_ex_imp_2021 as
select year, product, product_label, economy_label, partner_label, flow, KUSD
from baci_xad
where
    year = 2021
    and products in ('281', '764', '874', '782', '759', '333', '728',
     '334', '752', '821', '776', '784', '781', '778', '222', '971', '542')
union all
select year, product, product_label, economy_label, partner_label, flow, KUSD
from baci_xae
where
    year = 2021
    and products in ('281', '764', '874', '782', '759', '333', '728',
     '334', '752', '821', '776', '784', '781', '778', '222', '971', '542')
;

/* merge above tables into one */
create table top_ex_imp_2017_19 as
select * from top_ex_imp_2017
union all
select * from top_ex_imp_2018
union all
select * from top_ex_imp_2019
;
select
'year', 'product', 'product_label', 'economy_label', 'partner_label', 'flow', 'KUSD'
union all
select
year, product, product_label, economy_label, partner_label, flow, KUSD
from top_ex_imp_2017_19
into outfile '/private/tmp/top_ex_imp_2017_19.csv'
fields terminated by ','
enclosed by '"'
lines terminated by '\n'
;

create table top_ex_imp_2017_21 as
select * from top_ex_imp_2017_19
union all
select * from top_ex_imp_2020
union all
select * from top_ex_imp_2021
;
select
'year', 'product', 'product_label', 'economy_label', 'partner_label', 'flow', 'KUSD'
union all
select
year, product, product_label, economy_label, partner_label, flow, KUSD
from top_ex_imp_2017_21
into outfile '/private/tmp/top_ex_imp_2017_21.csv'
fields terminated by ','
enclosed by '"'
lines terminated by '\n'
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
