## 1. reproducing Ukraine product-network approach
### deadline: [[2023-09-31]]

1. Filter products
==Code steps:== [[filtering]]
```python
for country in (China, USA):
	for flow in (Export, Import):
```
- [x] filter using RCA
	- [x]  compute ratio of product within total network
		- [x] mySQL
	- [x] compute ratio of product within country
		- [x] merge naming structure with aggregated data
        -  (only use level3 for product)
        - [x] international_ratio = product/TOTAL
            - [ ] make sure TOTAL is correct
        - [x] national_ratio = product/sum(product)
            - [x] make sure TOTAL is correct

	- [x] search naming structure for BACI
        - [x] get csv file describing structure of commodity codes

2. Map product networks
- [x] compute centrality
    - china's top export(764)
        - [x] get data ready
            - [x] mysql filtered data
                - [x] un-filter for china and usa
            - [x] truncate data
                - **this cut off too much**
            - [x] create graph
        - [x] compute
            - [x] compute degree-centrality
            - [x] compute eigenvector-centrality
3. compute trade diversion between 2017-2019
    - [x] did the rca of products in china changed between 2016-2017?
        - hard to find what I'm looking for, moving to next step
    - [x] compute RCA on 2017 data and get product list
        - [x] create baci_xab
        - [x] **create rca_n_xaa_2017, rca_n_xab_2017**
            - xaa_2017
                - [x] n
            - xab_2017
                - [x] n
        - [x] load into ipynb
        - [x] merge for n axis
            - [x] n
        - [x] compute 2017 RCA
    - [x] create for_network tables for 2017, 2018, 2019
        - [x] filter products 
            - [x] create table baci_xac(2019)
                - create empty table
                - fill table
            - [x] create filtered tables 
                /* 2017 : baci_xaa */
                /*        baci_xab */
                /* 2018 : baci_xab */
                /* 2019 : baci_xab */
                /*        baci_xac */
                /* 2020 : baci_xac */
                /*        baci_xad */
                - [x] products_2017
                    - from baci_xaa, baci_xab
                - [x] products_2018
                    - from baci_xab
                - [x] products_2019
                    - from baci_xab
                    - from baci_xac
            - [x] merged filtered(year, products) tables into one
                - [x] export table as for_product_network_2017_19.csv
        - [x] compute china's centrality between top products per year
            - [x] compare degree centrality between years
                - [x] compute china's degree centrality for each year
                    - [x] 2017
                    - [x] 2018
                    - [x] 2019
        - [x] compute usa's centrality ...

    - [ ] **read**
        - [ ] find trade diversion metrics
            - [x] find 5 papers on trade diversion
            - [ ] read new measures paper
            - [ ] **read towards an input-output measure of trade diversion**
                    - SD analysis
                    - [ ] (Korea-US income/labor creation/diversion)
            - [ ] re-read WTN review by fagiolo et al. 
            - [ ] **read us-china diversion**
            - [ ] read review on security-trade network approach
    - [ ] **apply localization(Okada, 2016) to trade network**
        - [ ] do the newly formed trade diversion links reflect this?
            - [ ] soft reflection
                - some sector's imports have a reduction in non-localized areas,
                - and increases in localized ones
            - [ ] hard reflection
                - some sector's imports have fully pulled out from china-affected sub-networks
                - and moved to non-china-affected sub-networks 
                - **subnetworks: defined by localizaion rule**
        - [ ] how about in the context of security?

    - [ ] implement above metrics


4. Measure exposure


## 2. read china-us trade war network book
### deadline: [[2023-10-31]]


1. 


# refs
- network refs
    - [[https://gci.t.u-tokyo.ac.jp/tutorial/network/#%E4%BB%A3%E8%A1%A8%E7%9A%84%E3%81%AA%E3%83%84%E3%83%BC%E3%83%AB]]
- fixed effects
    - [[https://theeffectbook.net/ch-FixedEffects.html]]
