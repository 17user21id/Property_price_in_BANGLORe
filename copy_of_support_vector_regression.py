# -*- coding: utf-8 -*-
"""Copy of support_vector_regression.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Pmk1RvEYqlC5TBnBEEmCukLUtgdrBgJK

# Support Vector Regression (SVR)

## Importing the libraries
"""

# Commented out IPython magic to ensure Python compatibility.
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
# %matplotlib inline
import matplotlib
matplotlib.rcParams["figure.figsize"] = (20,10)

"""## Importing the dataset"""

df1 = pd.read_csv("/datasets_20710_26737_Bengaluru_House_Data.csv")
df1.head()

"""**Drop features that are not required to build our model**"""

df2 = df1.drop(['area_type' , 'society' , 'balcony' , 'availability'] , axis = 'columns')
df2.shape
df2.head()

"""##Data Cleaning: Handle NA values"""

df2.isnull().sum()

df3 = df2.dropna()
df3.isnull().sum()

"""##Feature Engineering

**Add new feature(integer) for bhk (Bedrooms Hall Kitchen)**
"""

df3['bhk'] = df3['size'].apply(lambda x: int(x.split(' ')[0]))
df3.bhk.unique()

"""**Explore total_sqft feature**"""

def is_float(x):
  try:
    float(x)
  except:
    return False
  return True

"""**Apply total sqft feature**"""

df3[~df3['total_sqft'].apply(is_float)].head(10)

"""**Above shows that total_sqft can be a range (e.g. 2100-2850). For such case we can just take average of min and max value in the range. There are other cases such as 34.46Sq. Meter which one can convert to square ft using unit conversion. I am going to just drop such corner cases to keep things simple**"""

def convert_sqft_to_num(x):
  tokens = x.split('-')
  if len(tokens) == 2:
    return (float(tokens[0]) + float(tokens[1]))/2
  try:
    return float(x)
  except:
    return None

df3.total_sqft = df3.total_sqft.apply(convert_sqft_to_num)
df3 = df3.dropna()
df3.isnull().sum()
df3.head(2)

"""##Feature Engineering

**Add new feature called price per square feet**
"""

df3['price_per_sqft'] = df3['price']*100000/df3['total_sqft']
df3.head()

"""**drop size column**"""

df3 = df3.drop(['size'] , axis = 'columns')
df3.head()

"""**Examine locations which is a categorical variable. We need to apply dimensionality reduction technique here to reduce number of locations**"""

df3.location = df3.location.apply(lambda x: x.strip())
location_stats = df3['location'].value_counts(ascending=False)
location_stats

"""##Dimensionality Reduction

**Any location having less than 10 data points should be tagged as "other" location. This way number of categories can be reduced by huge amount. Later on when we do one hot encoding, it will help us with having fewer dummy columns**
"""

location_stats_less_than_10 = location_stats[location_stats <= 10]
location_stats_less_than_10

df3.location = df3.location.apply(lambda x: 'other' if x in location_stats_less_than_10 else x)
len(df3.location.unique())

"""##Outlier Removal Using Business Logic

**As a data scientist when you have a conversation with your business manager (who has expertise in real estate), he will tell you that normally square ft per bedroom is 300 (i.e. 2 bhk apartment is minimum 600 sqft. If you have for example 400 sqft apartment with 2 bhk than that seems suspicious and can be removed as an outlier. We will remove such outliers by keeping our minimum thresold per bhk to be 300 sqft**
"""

df3[df3.total_sqft/df3.bhk < 300].head()

"""**Check above data points. We have 6 bhk apartment with 1020 sqft. Another one is 8 bhk and total sqft is 600. These are clear data errors that can be removed safely**

**creating a new column fro sqft per bhk**
"""

df3['sqft_per_bhk'] = df3['total_sqft']/df3['bhk']
df3.head()

"""**create a new function to to check sqft per bhk**"""

def check_sqft_per_bhk(x):
  if float(x) >= 300:
    return float(x)
  else:
    return None

"""**apply the sqft_per_bhk function**"""

df3.sqft_per_bhk = df3.sqft_per_bhk.apply(check_sqft_per_bhk)
df3 = df3.dropna()
df3.isnull().sum()
df3.shape

"""**Here we find that min price per sqft is 267 rs/sqft whereas max is 12000000, this shows a wide variation in property prices. We should remove outliers per location using mean and one standard deviation**"""

def remove_pps_outliers(df):
  df_out = pd.DataFrame()
  for key, subdf in df.groupby('location'):
    m = np.mean(subdf.price_per_sqft)
    st = np.std(subdf.price_per_sqft)
    reduced_df = subdf[(subdf.price_per_sqft>(m-st)) & (subdf.price_per_sqft<=(m+st))]
    df_out = pd.concat([df_out,reduced_df], ignore_index=True)
  return df_out
df4 = remove_pps_outliers(df3)
df4.shape

"""**Let's check if for a given location how does the 2 BHK and 3 BHK property prices look like**"""

def plot_scatter_chart(df,location):
  bhk2 = df[(df.location == location) & (df.bhk == 2)]
  bhk3 = df[(df.location == location) & (df.bhk == 3)]
  matplotlib.rcParams['figure.figsize'] = (15,10)
  plt.scatter(bhk2.total_sqft , bhk2.price , color='blue' , label = '2 BHK', s=50)
  plt.scatter(bhk3.total_sqft , bhk3.price , marker='+' , color='green' , label = '3 BHK' , s=50)
  plt.xlabel("Total Square feet Area")
  plt.ylabel("Price (Lakh Indian Rupees)")
  plt.title(location)
  plt.legend()
plot_scatter_chart(df4, "Rajaji Nagar")

"""**Now we can remove those 2 BHK apartments whose price_per_sqft is less than mean price_per_sqft of 1 BHK apartment**"""

def remove_bhk_outliers(df):
    exclude_indices = np.array([])
    for location, location_df in df.groupby('location'):
        bhk_stats = {}
        for bhk, bhk_df in location_df.groupby('bhk'):
            bhk_stats[bhk] = {
                'mean': np.mean(bhk_df.price_per_sqft),
                'std': np.std(bhk_df.price_per_sqft),
                'count': bhk_df.shape[0]
            }
        for bhk, bhk_df in location_df.groupby('bhk'):
            stats = bhk_stats.get(bhk-1)
            if stats and stats['count']>5:
                exclude_indices = np.append(exclude_indices, bhk_df[bhk_df.price_per_sqft<(stats['mean'])].index.values)
    return df.drop(exclude_indices,axis='index')
df5 = remove_bhk_outliers(df4)
df5.shape

"""**It is unusual to have 2 more bathrooms than number of bedrooms in a home**"""

df5[df5.bath>10]

"""**removing such data**"""

df6 = df5[df5.bath < df5.bhk + 2]
df6.shape

"""**Removing Price per Sqft**"""

df7 = df6.drop(['price_per_sqft', 'sqft_per_bhk'], axis='columns')
df7.shape

"""## Use One Hot Encoding For Location"""

dummies = pd.get_dummies(df7.location)
dummies.head(3)

df8 = pd.concat([df7, dummies.drop('other', axis='columns')], axis='columns')
df8.head()

df9 = df8.drop('location',axis='columns')
df9.head(2)

df9.shape

"""##Droping the independent variable price"""

X = df9.drop(['price'], axis='columns')
X.head(3)

X.shape

y = df9.price
y.head(3)

len(y)

from sklearn.model_selection import train_test_split
X_train , X_test , y_train , y_test = train_test_split(X,y,test_size=0.2,random_state=10)

from sklearn.linear_model import LinearRegression
lr_clf = LinearRegression()
lr_clf.fit(X_train , y_train)
lr_clf.score(X_test, y_test)

"""##Use K Fold cross validation to measure accuracy of our LinearRegression model"""

from sklearn.model_selection import ShuffleSplit
from sklearn.model_selection import cross_val_score

cv = ShuffleSplit(n_splits=5, test_size=0.2, random_state=0)

cross_val_score(LinearRegression(), X, y, cv=cv)

"""**We can see that in 5 iterations we get a score above 80% all the time. This is pretty good but we want to test few other algorithms for regression to see if we can get even better score. We will use GridSearchCV for this purpose**

##Find best model using GridSearchCV
"""

from sklearn.model_selection import GridSearchCV

from sklearn.linear_model import Lasso
from sklearn.tree import DecisionTreeRegressor

def find_best_model_using_gridsearchcv(X,y):
    algos = {
        'linear_regression' : {
            'model': LinearRegression(),
            'params': {
                'normalize': [True, False]
            }
        },
        'lasso': {
            'model': Lasso(),
            'params': {
                'alpha': [1,2],
                'selection': ['random', 'cyclic']
            }
        },
        'decision_tree': {
            'model': DecisionTreeRegressor(),
            'params': {
                'criterion' : ['mse','friedman_mse'],
                'splitter': ['best','random']
            }
        }
    }
    scores = []
    cv = ShuffleSplit(n_splits=5, test_size=0.2, random_state=0)
    for algo_name, config in algos.items():
        gs =  GridSearchCV(config['model'], config['params'], cv=cv, return_train_score=False)
        gs.fit(X,y)
        scores.append({
            'model': algo_name,
            'best_score': gs.best_score_,
            'best_params': gs.best_params_
        })

    return pd.DataFrame(scores,columns=['model','best_score','best_params'])

find_best_model_using_gridsearchcv(X,y)

"""**Based on above results we can say that LinearRegression gives the best score. Hence we will use that.**

##Test the model for few properties
"""

def predict_price(location,sqft,bath,bhk):    
    loc_index = np.where(X.columns==location)[0][0]

    x = np.zeros(len(X.columns))
    x[0] = sqft
    x[1] = bath
    x[2] = bhk
    if loc_index >= 0:
        x[loc_index] = 1

    return lr_clf.predict([x])[0]

predict_price('1st Phase JP Nagar',1000, 2, 2)

predict_price('1st Phase JP Nagar',1000, 3, 3)

predict_price('Indira Nagar',1000, 2, 2)

predict_price('Indira Nagar',1000, 3, 3)

"""##Export the tested model to a pickle file"""

import pickle
with open('banglore_home_prices_model.pickle','wb') as f:
    pickle.dump(lr_clf,f)

"""**Export location and column information to a file that will be useful later on in our prediction application**"""

import json
columns = {
    'data_columns' : [col.lower() for col in X.columns]
}
with open("columns.json","w") as f:
    f.write(json.dumps(columns))