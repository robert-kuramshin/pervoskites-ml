#initial model test
#initial feature importance 

import numpy as np
import pandas as pd

from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV
from sklearn.preprocessing import StandardScaler

from sklearn.metrics import mean_squared_error
from sklearn.metrics import r2_score

import pickle

#read data
test = pd.read_csv("../data/battery/test.csv")
train = pd.read_csv("../data/battery/train.csv")

#specify feature column names
feature_cols = [
"HOMO (eV)",
"LUMO (eV)",
"EA (eV)",
"# C",
"# B",
"# O",
"HOMO-LUMO gap",
"# Li",
"# H",
"No. of Aromatic Rings",
]

feature_names = [
"HOMO (eV)",
"LUMO (eV)",
"EA (eV)",
"# C",
"# B",
"# O",
"HOMO-LUMO gap",
"# Li",
"# H",
"No. of Aromatic Rings",
"RP (V) - DFT",
]

#splitting into dependant and independant variables
X_train = train.loc[:, feature_cols]
y_train = train['RP (V) - DFT']

X_test = test.loc[:, feature_cols]
y_test = test['RP (V) - DFT']


#normalizing 
scaler = StandardScaler()  
scaler.fit(X_train)  
X_train = scaler.transform(X_train)  
X_test = scaler.transform(X_test)  

tuned_parameters = [{'n_estimators': [100,150,200],
                     'max_depth': [1,2,3,4,5,6,7,8],
                     'min_samples_leaf':[1,2,3,4,5],
                    'min_samples_split': [0.5,0.75,1.0,2,3,4,5],
                    'learning_rate': [0.05,0.075,0.1,0.125,0.15,0.2],
               "loss":['ls','lad','huber']}]

# clf = GridSearchCV(GradientBoostingRegressor(), tuned_parameters, cv=5,n_jobs=5)
# clf.fit(X_train, y_train)

# print(clf.best_params_)

# y_pred = clf.predict(X_test)
# print(mean_squared_error(y_test, y_pred))
# print(r2_score(y_test, y_pred))

# np.savetxt("res/no-comp/gbr_raw.csv", y_pred, delimiter=",")

X_train = pd.DataFrame(X_train,columns=feature_cols)
y_train = pd.DataFrame(y_train,columns=['RP (V) - DFT'])

X_test = pd.DataFrame(X_test,columns=feature_cols)
y_test = pd.DataFrame(y_test,columns=['RP (V) - DFT'])

corr = X_train.corr()
corr.to_csv("res/no-comp/corr.csv")

columns = np.full((corr.shape[0],), True, dtype=bool)
for i in range(corr.shape[0]):
    for j in range(i+1, corr.shape[0]):
        if corr.iloc[i,j] >= 0.999:
            if columns[j]:
                columns[j] = False
selected_columns = X_train.columns[columns]

X_test[selected_columns].to_csv("res/no-comp/X_test_corr.csv")
X_train[selected_columns].to_csv("res/no-comp/X_train_corr.csv")

#gbr based recursive feature elimination results

in_x_train = pd.read_csv("res/no-comp/X_train_corr.csv",index_col=0)
in_x_test = pd.read_csv("res/no-comp/X_test_corr.csv",index_col=0)
in_y_train = pd.read_csv("res/y_train.csv",index_col=0)
in_y_test = pd.read_csv("res/y_test.csv",index_col=0)

feature_cols = in_x_train.columns.values

validation_ratio = 0.7
dataset_size = len(in_x_train)

X_train = in_x_train.loc[validation_ratio*dataset_size:]
y_train = in_y_train.loc[validation_ratio*dataset_size:]

X_val = in_x_train.loc[:validation_ratio*dataset_size]
y_val = in_y_train.loc[:validation_ratio*dataset_size]

params = [{'n_estimators': [500], 'max_depth': [3,4,5],'min_samples_leaf':[3,4], 'min_samples_split': [3,4,5],
          'learning_rate': [0.1], 'loss': ['ls']}]

clf = GridSearchCV(GradientBoostingRegressor(), params, cv=5,n_jobs=5,)
clf.fit(X_train, y_train)

y_true, y_pred = y_val, clf.predict(X_val)

print("MSE with all features")

all_feature_mse = mean_squared_error(y_true, y_pred)
print(all_feature_mse)

print("Starting feature relevance analysis")

mse_arr = []
feature_arr = []

for feature in feature_cols:
    X_train_copy = X_train.loc[:, feature_cols].copy()
    y_train_copy = y_train.copy()
    X_test_copy = X_val.loc[:, feature_cols].copy()
    y_test_copy = y_val.copy()

    X_train_cut = X_train_copy.drop(columns=feature)
    X_test_cut = X_test_copy.drop(columns=feature)

    scaler = StandardScaler() 
    scaler.fit(X_train_cut)  
    X_train_cut = scaler.transform(X_train_cut)  
    X_test_cut = scaler.transform(X_test_cut)  

    
    clf = GridSearchCV(GradientBoostingRegressor(), params, cv=5,n_jobs=5,)
    clf.fit(X_train_cut, y_train_copy)

    y_true, y_pred = y_test_copy, clf.predict(X_test_cut)

    mse = mean_squared_error(y_true, y_pred)
    print("----------------------------------")
    print(feature)
    print(mse)
    mse_arr.append(mse)
    feature_arr.append(feature)

feature_importance = mse_arr
# make importances relative to max importance
feature_importance = 100.0 * (feature_importance / max(feature_importance))
sorted_idx = np.argsort(feature_importance)
pos = np.arange(sorted_idx.shape[0]) + .5
feature_arr = [feature_arr[i] for i in sorted_idx]

feature_cols = feature_arr
feature_importance.sort()

f_imp = pd.DataFrame()
f_imp["feature"] = feature_cols
f_imp["importance"] = feature_importance
print("----------------------------------")
print("----------------------------------")
print("----------------------------------")
print(f_imp)
print("----------------------------------")
print("----------------------------------")
print("----------------------------------")

f_imp.to_csv("res/no-comp/feature_importance_gbr_compound.csv")

#creating regressor and fitting data
tuned_parameters = [{'n_estimators': [500], 'max_depth': [3,4,5],'min_samples_leaf':[3,4], 'min_samples_split': [3,4,5],
          'learning_rate': [0.1], 'loss': ['ls']}]
          
reg = GridSearchCV(GradientBoostingRegressor(), tuned_parameters, cv=5, n_jobs=5,
                scoring='neg_mean_squared_error')

mse = []
r2 = []
feature = []

reg.fit(X_train, y_train.values.ravel())

predicted = reg.predict(X_val)

r2.append(r2_score(y_val, predicted))
mse.append(mean_squared_error(y_val, predicted))
feature.append("None")
print("----------------------------------")
print(mse[-1])
print("None")
feature.append(feature_cols[0])
feature_cols.remove(feature_cols[0])


while (feature_cols):
    X_train = X_train.loc[:, feature_cols]
    X_val = X_val.loc[:, feature_cols]

    reg = GridSearchCV(GradientBoostingRegressor(), tuned_parameters, cv=5, n_jobs=5,
                    scoring='neg_mean_squared_error')

    reg.fit(X_train, y_train.values.ravel())
    predicted = reg.predict(X_val)

    r2.append(r2_score(y_val, predicted))
    mse.append(mean_squared_error(y_val, predicted))

    print("----------------------------------")
    print(mse[-1])
    print(feature[-1])

    
    feature.append(feature_cols[0])

    feature_cols.remove(feature_cols[0])

f_elim = pd.DataFrame()
f_elim["feature"] = feature[:-1]
f_elim["mse"] = mse
f_elim["r2"] = r2
f_elim.to_csv("res/no-comp/feature_elim_gbr_compound.csv")

rfe_features = feature[np.argmin(mse)+1:]
in_x_train = in_x_train[rfe_features]
in_x_test = in_x_test[rfe_features]

in_x_train.to_csv("res/no-comp/X_train_rfe_gbr.csv")
in_x_test.to_csv("res/no-comp/X_test_rfe_gbr.csv")

#read data
X_train = pd.read_csv("res/no-comp/X_train_rfe.csv",index_col=0)
X_test = pd.read_csv("res/no-comp/X_test_rfe.csv",index_col=0)
y_train = pd.read_csv("res/y_train.csv",index_col=0)
y_test = pd.read_csv("res/y_test.csv",index_col=0)

tuned_parameters = [{'n_estimators': [100,150,200],
                     'max_depth': [1,2,3,4,5,6,7,8],
                     'min_samples_leaf':[1,2,3,4,5],
                    'min_samples_split': [0.5,0.75,1.0,2,3,4,5],
                    'learning_rate': [0.05,0.075,0.1,0.125,0.15,0.2],
               "loss":['ls','lad','huber']}]

clf = GridSearchCV(GradientBoostingRegressor(), tuned_parameters, cv=5,n_jobs=5,)
clf.fit(X_train, y_train)

print(clf.best_params_)

y_pred = clf.predict(X_test)
print(mean_squared_error(y_test, y_pred))
print(r2_score(y_test, y_pred))

np.savetxt("res/no-comp/gbr_compound_res.csv", y_pred, delimiter=",")

res_test = pd.DataFrame(index=X_train.index )
res_test["y"] = y_train
res_test["pred(y)"] = clf.predict(X_train)
res_test.to_csv("res/no-comp/gbr_compound_res_train.csv")

pickle.dump(clf, open("models/gbr_no_compound.sav", 'wb'))