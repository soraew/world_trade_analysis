/* TASK 1 */
/* 1. get sum across countries */
select 'product', 'product_label', 'sum_kusd'
union all
select product, product_label, sum(KUSD) as sum_kusd
from baci_xaa
where year = 2016
group by product, product_label
into outfile '/private/tmp/tradewar_tmp/RCA.csv'
fields terminated by ','
enclosed by '"'
lines terminated by '\n'
;

/* 2. get sum within countries */
select 'product', 'product_label', 'economy_label', 'flow', 'sum_kusd'
union all
select product, product_label, economy_label, flow, sum(KUSD) as sum_kusd
from baci_xaa
where year = 2016
group by product, product_label, economy_label, flow
into outfile '/private/tmp/RCA_p.csv'
fields terminated by ','
enclosed by '"'
lines terminated by '\n'
;

/* 3. for getting product network of top 5 exports of China and USA */
/* for 2016 on baci_xaa */
select 'product', 'product_label', 'economy_label', 'partner_label', 'flow', 'kusd'
union all
select product, product_label, economy_label, partner_label, flow, KUSD
from baci_xaa
where
    year = 2016
    and product in ('222', '334', '752', '764', '778', '784', '821', '851', '874')
into outfile '/private/tmp/for_product_network_2016.csv'
fields terminated by ','
enclosed by '"'
lines terminated by '\n'
;

/* for 2017 on baci_xaa */

/* for 2017 on baci_xab */

/* for 2018 on baci_xab */

/* TASK 3 */

/* 3.1 compute RCA for USA and China, 2017 */
/* 3.1.1 get sum across countries */
select 'product', 'product_label', 'sum_kusd'
union all
select product, product_label, sum(KUSD) as sum_kusd
from baci_xab
where year = 2017
group by product, product_label
into outfile '/private/tmp/tradewar_tmp/rca_p_2017.csv'
fields terminated by ','
enclosed by '"'
lines terminated by '\n'
;
/* 3.1.2 get sum within countries */
select 'product', 'product_label', 'economy_label', 'flow', 'sum_kusd'
union all
select product, product_label, economy_label, flow, sum(KUSD) as sum_kusd
from baci_xab
where year = 2017
group by product, product_label, economy_label, flow
into outfile '/private/tmp/tradewar_tmp/rca_n_2017.csv'
fields terminated by ','
enclosed by '"'
lines terminated by '\n'
;

/* 3.3. for getting product network of top 5 exports of China and USA */
select 'product', 'product_label', 'economy_label', 'partner_label', 'flow', 'kusd'
union all
select product, product_label, economy_label, partner_label, flow, KUSD
from baci_xab
where
    year = 2018
    and product in ()
into outfile '/private/tmp/for_product_network_2018.csv'
fields terminated by ','
enclosed by '"'
lines terminated by '\n'
;

/* for 2019 on baci_xab */
select 'product', 'product_label', 'economy_label', 'partner_label', 'flow', 'kusd'
union all
select product, product_label, economy_label, partner_label, flow, KUSD
from baci_xab
where
    year = 2019
    and product in ()
into outfile '/private/tmp/for_product_network_2019.csv'
fields terminated by ','
enclosed by '"'
lines terminated by '\n'
;

/* for 2019 on baci_xac */
select 'product', 'product_label', 'economy_label', 'partner_label', 'flow', 'kusd'
union all
select product, product_label, economy_label, partner_label, flow, KUSD
from baci_xab
where
    year = 2019
    and product in ('222', '334', '752', '764', '778', '784', '821', '851', '874')
into outfile '/private/tmp/for_product_network_2019.csv'
fields terminated by ','
enclosed by '"'
lines terminated by '\n'
;
/* for 2020 on baci_xac */
/* for 2020 on baci_xad */





/* 2017 : baci_xaa */
/*        baci_xab */
/* 2018 : baci_xab */
/* 2019 : baci_xab */
/*        baci_xac */
/* 2020 : baci_xac */
/*        baci_xad */

