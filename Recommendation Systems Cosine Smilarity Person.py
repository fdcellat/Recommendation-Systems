# -*- coding: utf-8 -*-
"""
Created on Tue Sep 13 11:06:35 2022

@author: T006940
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import cx_Oracle as ora

conn = ora.connect("username", "password", "DB", encoding="UTF-8")
cur = conn.cursor()

df = pd.read_sql_query(""" SQL SCRİPT
""", conn)

# copy df------------------------------------------------------------------------------------------

df2=df.copy()


# convert user_name to user_index
z=int(input('User no giriniz: '))

a=list(map(lambda x:[x],list(df2.iloc[z,:])))
# selecting rows based on condition 
#rslt_df = df[df['smoker'].isin(a) ]&df[df['time'].isin(b) ]&df[df['day'].isin(c) ]

#-------------------------------------------------------------------Filtrelemek istediğin sütunları seç
df=df2[df2['SF'].isin(a[2])&df2['SE'].isin(a[3])&df2['KANAL_YENI'].isin(a[5])]

df.drop(df.iloc[:,0:16],inplace=True, axis =1)
# df.drop(columns=df.columns[-2:], 
#         axis=1, 
#         inplace=True)

df.drop('HA - Kredili Hayat', axis=1,inplace=True)

#-------------------------------------------------------------------hiç kullanılmayan ürünleri çıkarır
df=df.loc[:, (df != 0).any(axis=0)]
# df = df.iloc[0:10000,:]
#------------------------------------------------------------------hiç ürünü olmayan kişileri çıkarır
df=df.T
df=df.loc[:, (df != 0).any(axis=0)]
# df=df.T
# df.reset_index(inplace=True)
# df.drop('index', axis=1, inplace=True)

#df=df.T
df1 = df.copy()

# find the nearest neighbors using NearestNeighbors(n_neighbors=3)
from sklearn.neighbors import NearestNeighbors
n_neighbors=3
number_neighbors = 3
knn = NearestNeighbors(metric='cosine', algorithm='brute')
knn.fit(df.values)
distances, indices = knn.kneighbors(df.values, n_neighbors=number_neighbors)


user_index = df.columns.tolist().index(z)

# t: product_title, m: the row number of t in df
for m,t in list(enumerate(df.index)):
  
  # find products without ratings by user_4
  if df.iloc[m, user_index] == 0:
    sim_products = indices[m].tolist()
    product_distances = distances[m].tolist()
    
    # Generally, this is the case: indices[3] = [3 6 7]. The product itself is in the first place.
    # In this case, we take off 3 from the list. Then, indices[3] == [6 7] to have the nearest NEIGHBORS in the list. 
    if m in sim_products:
      id_product = sim_products.index(m)
      sim_products.remove(m)
      product_distances.pop(id_product) 

    # However, if the percentage of ratings in the dataset is very low, there are too many 0s in the dataset. 
    # Some products have all 0 ratings and the products with all 0s are considered the same products by NearestNeighbors(). 
    # Then,even the product itself cannot be included in the indices. 
    # For example, indices[3] = [2 4 7] is possible if product_2, product_3, product_4, and product_7 have all 0s for their ratings.
    # In that case, we take off the farthest product in the list. Therefore, 7 is taken off from the list, then indices[3] == [2 4].
    else:
      sim_products = sim_products[:n_neighbors-1]
      product_distances = product_distances[:n_neighbors-1]
        
    # product_similarty = 1 - product_distance    
    product_similarity = [1-x for x in product_distances]
    product_similarity_copy = product_similarity.copy()
    nominator = 0

    # for each similar product
    for s in range(0, len(product_similarity)):
      
      # check if the rating of a similar product is zero
      if df.iloc[sim_products[s], user_index] == 0:

        # if the rating is zero, ignore the rating and the similarity in calculating the predicted rating
        if len(product_similarity_copy) == (number_neighbors - 1):
          product_similarity_copy.pop(s)
          
        else:
          product_similarity_copy.pop(s-(len(product_similarity)-len(product_similarity_copy)))

      # if the rating is not zero, use the rating and similarity in the calculation
      else:
        nominator = nominator + product_similarity[s]*df.iloc[sim_products[s],user_index]

    # check if the number of the ratings with non-zero is positive
    if len(product_similarity_copy) > 0:
      
      # check if the sum of the ratings of the similar products is positive.
      if sum(product_similarity_copy) > 0:
        predicted_r = nominator/sum(product_similarity_copy)

      # Even if there are some products for which the ratings are positive, some products have zero similarity even though they are selected as similar products.
      # in this case, the predicted rating becomes zero as well  
      else:
        predicted_r = 0

    # if all the ratings of the similar products are zero, then predicted rating should be zero
    else:
      predicted_r = 0

  # place the predicted rating into the copy of the original dataset
    df1.iloc[m,user_index] = predicted_r

def recommend_products(user, num_recommended_products):

  print('{} in Sahip oldugu ürünler \n'.format(user))

  for m in df[df[user] > 0][user].index.tolist():
    print(m)
  
  print('\n')

  recommended_products = []

  for m in df[df[user] == 0].index.tolist():

    index_df = df.index.tolist().index(m)
    predicted_rating = df1.iloc[index_df, df1.columns.tolist().index(user)]
    recommended_products.append((m, predicted_rating))

  sorted_rm = sorted(recommended_products, key=lambda x:x[1], reverse=True)
  
  print('Önerilen ürünlerin listesi ve ratingi \n')
  rank = 1
  for recommended_product in sorted_rm[:num_recommended_products]:
    
    print('{}: {} - predicted rating:{}'.format(rank, recommended_product[0], recommended_product[1]))
    rank = rank + 1
    
recommend_products(z, 3)
