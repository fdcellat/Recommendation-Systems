# -*- coding: utf-8 -*-
"""
Created on Tue Sep 13 11:04:14 2022

@author: T006940
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import cx_Oracle as ora

conn = ora.connect("ASAPMAZ", "ASAPMAZ123", "DWH", encoding="UTF-8")
cur = conn.cursor()

df = pd.read_sql_query("""
SELECT*
from asapmaz.sil_inforce_ownership_table_
where se = 'S'
AND sf = 'S'
and region='TR'
and RowNum<10000
ORDER BY police
""", conn)


df.drop(df.iloc[:,0:16],inplace=True, axis =1)
df.drop(columns=df.columns[-2:], 
        axis=1, 
        inplace=True)

df.drop('HA - Kredili Hayat', axis=1,inplace=True)

#-------------------------------------------------------------------hiç kullanılmayan ürünleri çıkarır
df=df.loc[:, (df != 0).any(axis=0)]
# df = df.iloc[0:10000,:]
#------------------------------------------------------------------hiç ürünü olmayan kişileri çıkarır
df=df.T
df=df.loc[:, (df != 0).any(axis=0)]
df=df.T
df.reset_index(inplace=True)
df.drop('index', axis=1, inplace=True)

#-------------------------------------------------------------------sadece 1 ürün alan kişileri çıkarır

df=df.T
# def stoplam (datarow):
#     a=0
#     for i in datarow:
#         if i==0 :
#             a+=1
#     return a
# df['ss']=df.apply(lambda x: stoplam(x),axis=1)
# df=df[df['ss']<55]
# df.drop('ss',axis=1,inplace=True)

from sklearn.neighbors import NearestNeighbors
knn = NearestNeighbors(metric='cosine', algorithm='brute')
knn.fit(df.values)
distances, indices = knn.kneighbors(df.values, n_neighbors=3)


a=str(input('Ürün adı giriniz:'))
# get the index for 'product_0'
index_for_product = df.index.tolist().index(a)
# find the indices for the similar products
sim_products = indices[index_for_product].tolist()
# distances between 'product_0' and the similar products
product_distances = distances[index_for_product].tolist()
# the position of 'product_0' in the list sim_products
id_product = sim_products.index(index_for_product)
# remove 'product_0' from the list sim_products
sim_products.remove(index_for_product)
# remove 'product_0' from the list product_distances
product_distances.pop(id_product)
print('Secilen urune en yakın urunler:', df.iloc[sim_products,:0].index)
print('urun_uzakligi:', product_distances)