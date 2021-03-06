# -*- coding: utf-8 -*-
"""CS6216_taylor_series_identification.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1IZKKy0qOvQ4FbWazHa944Iv2QRVmyAe_
"""

import pandas as pd
import numpy as np
import math


def create_power_matrix(vector, series_length = 10): #helper function for knowledge dataframe creation
  matrix = np.power(vector,0)
  for i in range(1,series_length):
    matrix = np.hstack((matrix, np.power(vector, i)))
  return matrix


def knowledge_dataframe_creation(list_of_nodes, number_of_samples, series_length = 10):
  #this function returns a dataframe based on the existing nodes in the knowledge graph
  #the arguments to the function are the list of nodes (in the KG, which comprise the name of the node and its taylor series),
  #the number of samples that we want to train the neural network with for each node type (larger is better but takes more time to train)
  #and the series length, which is the length of the taylor series (the default is 10, which is taylor series up to and including x^9)
  #the dataframe is later used to train the neural network
  #the dataframe has columns {input, output} (which are the inputs to the dataframe), 
  #{label} (which is just so that a reader can view and identify the taylor series),
  #and {ts_1 till ts_10} (the outputs of the neural network)
  #note that the input, output columns of the dataframe are generated based on knowledge we have about a function.
  #we assume that a function has inputs of domain 1-3 and outputs in the range taylor_series(1) to taylor_series(3)
  ts_list = ["ts_%s" %i for i in range(0,series_length)]
  columns = ["input", "output", "label"] + ts_list
  df = pd.DataFrame(columns = ["input", "output"]) 
  for i in list_of_nodes:
    name = i[0]
    taylor_series = i[1]["taylor_series"]
    # print([taylor_series]*number_of_samples)
    data_for_dataframe = np.transpose(np.array([np.random.rand(number_of_samples)])*10) #implicitly assume that the domain is 0-10
    # print(np.transpose(data_for_dataframe))
    # print(np.sum(np.multiply(data_for_dataframe, taylor_series), axis = 1))
    # print([name]*number_of_samples)
    data_for_dataframe = np.hstack((data_for_dataframe, 
                                    np.transpose([np.sum(np.multiply(create_power_matrix(data_for_dataframe, series_length = series_length), 
                                                                     taylor_series), axis=1)]), 
                                    np.transpose([[name]*number_of_samples]),
                                    [taylor_series]*number_of_samples))
    df_new = pd.DataFrame(data = data_for_dataframe, columns = columns)
    df = df.append(df_new, ignore_index= True)
  return df

#testing
# knowledge_dataframe_creation([["sine", [0,1,0,-1/math.factorial(3),0,1/math.factorial(5),0,-1/math.factorial(7),0,1/math.factorial(9)]],
#                               ["cosine", [1,0,-1/math.factorial(2),0,1/math.factorial(4),0,-1/math.factorial(6),0,1/math.factorial(8),0]],
#                               ["expon", [1,1,1/math.factorial(2),1/math.factorial(3),1/math.factorial(4),1/math.factorial(5),
#                                   1/math.factorial(6),1/math.factorial(7),1/math.factorial(8),1/math.factorial(9)]],
#                               ["quadr", [0,0,1,0,0,0,0,0,0,0]]], 
#                              number_of_samples = 2000)

import tensorflow
tensorflow.random.set_seed(1)
from tensorflow.python.keras.layers import Dense
from tensorflow.keras.layers import Dropout
from tensorflow.python.keras.models import Sequential
from tensorflow.python.keras.wrappers.scikit_learn import KerasRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

def create_neural_network(df_known, series_length = 64):
  #this function takes in the dataframe created based on the knowledge graph and trains a neural network with it
  #it returns a neural network model and the scaler x and scaler y,
  #with which to scale any new data that we get with input and output values that we want to identify the taylor series of
  X = df_known[["input", "output"]].values
  ts_list = ["ts_%s" %i for i in range(0,series_length)]
  y = df_known[ts_list].values

  X_train, X_test, y_train, y_test = train_test_split(X,y, test_size = 0.05, shuffle = True)
  # print(X_train.shape, X_test.shape, y_train.shape, y_test.shape)

  scaler_x = MinMaxScaler()
  scaler_y = MinMaxScaler()
  scaler_x.fit(X_train)
  xtrain_scale=scaler_x.transform(X_train)
  scaler_x.fit(X_test)
  xval_scale=scaler_x.transform(X_test)
  scaler_y.fit(y_train)
  ytrain_scale=scaler_y.transform(y_train)
  scaler_y.fit(y_test)
  yval_scale=scaler_y.transform(y_test)

  model = Sequential()
  model.add(Dense(32, input_dim=2, kernel_initializer='normal', activation='relu'))
  model.add(Dense(64, activation='relu'))
  model.add(Dense(100, activation='relu'))
  model.add(Dense(128, activation='relu'))
  model.add(Dense(150, activation='relu'))
  model.add(Dropout(0.5))
  model.add(Dense(256, activation='relu'))
  model.add(Dense(512, activation='relu'))
  model.add(Dense(1024, activation='relu'))
  model.add(Dropout(0.5))
  model.add(Dense(256, activation='relu'))
  model.add(Dropout(0.5))
  model.add(Dense(series_length, activation='linear'))
  model.summary()

  import tensorflow.keras.backend as kb
  def maape(y_actual,y_pred):
      maape = kb.mean(tensorflow.math.atan(tensorflow.math.abs((y_actual - y_pred) / (y_actual + 1e-10))))
      return maape

#   model.compile(loss='mse', optimizer='adam', metrics=['mse','mae', maape])
  model.compile(loss='mse', optimizer='adam', metrics=['mse','mae', maape])
  history=model.fit(xtrain_scale, ytrain_scale, epochs=200, batch_size=64, verbose=1, validation_split=0.2)
  # predictions = model.predict(xval_scale)
  return model, scaler_x, scaler_y

# test_dataframe = knowledge_dataframe_creation([["sine", [0,1,0,-1/math.factorial(3),0,1/math.factorial(5),0,-1/math.factorial(7),0,1/math.factorial(9)]],
#                               ["cosine", [1,0,-1/math.factorial(2),0,1/math.factorial(4),0,-1/math.factorial(6),0,1/math.factorial(8),0]],
#                               ["expon", [1,1,1/math.factorial(2),1/math.factorial(3),1/math.factorial(4),1/math.factorial(5),
#                                   1/math.factorial(6),1/math.factorial(7),1/math.factorial(8),1/math.factorial(9)]],
#                               ["quadr", [0,0,1,0,0,0,0,0,0,0]],
#                               ["cubic", [0,0,0,1,0,0,0,0,0,0]]], 
#                              number_of_samples = 500)

# knowledge_df = knowledge_dataframe_creation([["sine", [0,1,0,-1/math.factorial(3),0,1/math.factorial(5),0,-1/math.factorial(7),0,1/math.factorial(9)]],
#                               ["cosine", [1,0,-1/math.factorial(2),0,1/math.factorial(4),0,-1/math.factorial(6),0,1/math.factorial(8),0]],
#                               ["expon", [1,1,1/math.factorial(2),1/math.factorial(3),1/math.factorial(4),1/math.factorial(5),
#                                   1/math.factorial(6),1/math.factorial(7),1/math.factorial(8),1/math.factorial(9)]],
#                               ["quadr", [0,0,1,0,0,0,0,0,0,0]],
#                               ["cubic", [0,0,0,1,0,0,0,0,0,0]]], 
#                              number_of_samples = 2000)

def make_prediction(knowledge_dataframe, test_dataframe, series_length):
  #this function takes in the dataframe that we create based on current knowledge (ie the KG) 
  #and the test dataframe, which contains inputs and outputs of an unknown function that we want to identify
  #it returns the predictions of the taylor series of this unknown function
  nnmodel, scaler_x, scaler_y = create_neural_network(knowledge_dataframe, series_length) 
  return scaler_y.inverse_transform(nnmodel.predict(scaler_x.transform(test_dataframe)))


# prediction_ts = make_prediction(knowledge_df, test_dataframe[["input", "output"]].values)

# test = prediction_ts

def preprocessing(series1):
  #this function is a preprocessing function that preprocesses taylor series predictions before the function is identified
  #it takes in a taylor series prediction of an input and output pair
  #and returns a preprocessed taylor series prediction, preprocessed based on some heuristics below:
  for i in range(len(series1)-1):
    # if abs(series1[i]) < 1/math.factorial(i+2):
    if (abs(series1[i]) < abs(series1[i+1])) or (i > 4 and abs(series1[i]) < 1/math.factorial(i)): 
      #the second requirement should be removed if the taylor series does not use !
      #second requirement introduced because the first values in the series tend to be underestimated
      #later values tend to be overestimated
      series1[i] = 0
  return series1

def match_prediction_to_series(series_predictions, list_of_nodes):
  #this function takes in a taylor series prediction and knowledge of all the nodes in the KG
  #and returns a best guess as to what function the taylor series prediction expressed
  #this best guess is based on the maape between the prediction and the known taylor series in the KG
  def maape_comparison(actual, prediction):
    return np.mean(np.arctan(np.abs((np.array(actual) - np.array(prediction)) / (np.array(actual) + 1e-10))))

  def find_taylor_series(prediction, list_of_nodes):
    losses = []
    for i in possibilities:
      losses.append(maape_comparison(i, prediction))
    return losses
  
  ts_guess = list(map(preprocessing, series_predictions))
  errors = np.zeros((len(series_predictions), len(list_of_nodes)))
  print(errors.shape)
  answer = []
  for i in range(len(list_of_nodes)):
    answer.append(list_of_nodes[i][0])
    # errors[:,i] = list(map(maape_comparison, [list_of_nodes[i][1]]*len(series_predictions), ts_guess))
    errors[:,i] = list(map(maape_comparison, [list_of_nodes[i][1]["taylor_series"]]*len(series_predictions), series_predictions))
  final_errors = np.argmin(errors, axis = 1)
  prediction = np.array([answer]*len(series_predictions))
  return prediction[range(len(prediction)), final_errors]

# test = prediction_ts

# percentage = match_prediction_to_series(test, [["sine", [0,1,0,-1/math.factorial(3),0,1/math.factorial(5),0,-1/math.factorial(7),0,1/math.factorial(9)]],
#                               ["cosine", [1,0,-1/math.factorial(2),0,1/math.factorial(4),0,-1/math.factorial(6),0,1/math.factorial(8),0]],
#                               ["expon", [1,1,1/math.factorial(2),1/math.factorial(3),1/math.factorial(4),1/math.factorial(5),
#                                   1/math.factorial(6),1/math.factorial(7),1/math.factorial(8),1/math.factorial(9)]],
#                               ["quadr", [0,0,1,0,0,0,0,0,0,0]],
#                               ["cubic", [0,0,0,1,0,0,0,0,0,0]]])

# answer = ['sine']*500+['cosine']*500+['expon']*500 + ['quadr']*500+ ['cubic']*500
# print(percentage)
# print(answer)
# print(sum(list(map(int, percentage == answer)))/2500)

# try1 = preprocessing(prediction_ts[2001])
# print(try1)

# def maape_comparison1(actual, prediction):
#   return np.mean(np.arctan(np.abs((np.array(actual) - np.array(prediction)) / (np.array(actual) + 1e-10))))

# #for sine
# sine = [0,1,0,-1/math.factorial(3),0,1/math.factorial(5),0,-1/math.factorial(7),0,1/math.factorial(9)]
# # print(maape_comparison(sine, preprocessing(testing)))

# #for cosine
# cosine = [1,0,-1/math.factorial(2),0,1/math.factorial(4),0,-1/math.factorial(6),0,1/math.factorial(8),0]
# # print(maape_comparison(cosine, preprocessing(testing)))

# #for exponential
# expon = [1,1,1/math.factorial(2),1/math.factorial(3),1/math.factorial(4),1/math.factorial(5),1/math.factorial(6),1/math.factorial(7),1/math.factorial(8),1/math.factorial(9)]
# # print(maape_comparison(expon, preprocessing(testing)))

# #for quadratic
# quadr = [0,0,1,0,0,0,0,0,0,0]
# # print(maape_comparison(quadr, preprocessing(testing)))

# cubic = [0,0,0,1,0,0,0,0,0,0]
# # print(maape_comparison(quadr, preprocessing(testing)))

# print(maape_comparison1(sine, try1))
# print(maape_comparison1(cosine, try1))
# print(maape_comparison1(expon, try1))
# print(maape_comparison1(quadr, try1))
# print(maape_comparison1(cubic, try1))

# # print(y_test[1])