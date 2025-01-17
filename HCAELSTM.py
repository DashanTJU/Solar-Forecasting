# Import necessary libraries
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import graphviz
from keras.layers import Convolution1D, Dense, Dropout, Flatten, MaxPooling1D, Activation, Lambda, Embedding, Bidirectional, LSTM, GRU, SimpleRNN
import tensorflow.keras.layers as L
from keras.callbacks import CSVLogger

# Load Dataset
df = pd.read_csv('Dataset.csv')
print(df)

# Analyze the dataset
print(df['Daily Power Production'].value_counts())
dpp_data = pd.DataFrame(list(df['Daily Power Production']), columns=['Daily Power Production'])
print(dpp_data)

# Data cleaning process - removing outliers
# Using Z-score method
from scipy import stats
z_scores = np.abs(stats.zscore(data))
data_cleaned = data[(z_scores < 3).all(axis=1)]

# Alternatively, using IQR method
Q1 = data.quantile(0.25)
Q3 = data.quantile(0.75)
IQR = Q3 - Q1
data_cleaned = data[~((data < (Q1 - 1.5 * IQR)) | (data > (Q3 + 1.5 * IQR))).any(axis=1)]

print(data_cleaned)

# Data scaling
from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler(feature_range=(0, 1))
dpp_data_scaled = scaler.fit_transform(dpp_data)
print(dpp_data_scaled.shape)

# Prepare the data for the model
timestep = 4
dpp_X = []
dpp_Y = []
for i in range(len(dpp_data_scaled) - timestep):
    dpp_X.append(dpp_data_scaled[i:i + timestep])
    dpp_Y.append(dpp_data_scaled[i + timestep])

dpp_X = np.array(dpp_X)
dpp_Y = np.array(dpp_Y)

# Split the data into training and validation sets
from sklearn.model_selection import train_test_split
dpp_X_train, dpp_X_valid, dpp_Y_train, dpp_Y_valid = train_test_split(dpp_X, dpp_Y, test_size=0.4, random_state=0)
print('Train set shape:', dpp_X_train.shape)
print('Validation set shape:', dpp_X_valid.shape)

# Import additional libraries for model creation
from tensorflow.keras.layers import RepeatVector, TimeDistributed, Conv1D, MaxPooling1D, Flatten, Bidirectional, Dropout
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.utils import plot_model

# Define CNN model
dpp_model_cnn = Sequential()
dpp_model_cnn.add(Conv1D(filters=64, kernel_size=2, activation='relu', input_shape=(dpp_X_train.shape[1], dpp_X_train.shape[2])))
dpp_model_cnn.add(MaxPooling1D(pool_size=2))
dpp_model_cnn.add(Flatten())
dpp_model_cnn.add(Dense(50, activation='relu'))
dpp_model_cnn.add(Dense(1))
dpp_model_cnn.compile(loss='mse', optimizer=Adam(learning_rate=0.001), metrics=['mse', 'mae'])
dpp_model_cnn.summary()

# Train the CNN model
dpp_csv_logger = CSVLogger('cnn_dpp.csv', separator=',', append=False)
dpp_cnn_history = dpp_model_cnn.fit(dpp_X_train, dpp_Y_train, validation_data=(dpp_X_valid, dpp_Y_valid), epochs=100, batch_size=32, verbose=1, shuffle=True, callbacks=[dpp_csv_logger])
print(dpp_model_cnn.summary())

# Define Autoencoder LSTM model
dpp_auto_model = Sequential()
dpp_auto_model.add(L.LSTM(10, activation='relu', input_shape=(4, 1), return_sequences=True))
dpp_auto_model.add(L.LSTM(6, activation='relu', return_sequences=True))
dpp_auto_model.add(L.LSTM(1, activation='relu'))
dpp_auto_model.add(L.RepeatVector(1))
dpp_auto_model.add(L.LSTM(10, activation='relu', return_sequences=True))
dpp_auto_model.add(L.LSTM(10, activation='relu', return_sequences=True))
dpp_auto_model.add(L.Dense(1))
dpp_auto_model.summary()

# Compile and train the Autoencoder LSTM model
dpp_auto_model.compile(loss='mse', optimizer=Adam(learning_rate=0.01), metrics=['mse', 'mae'])
dpp_csv_logger = CSVLogger('Autolstm_dpp.csv', separator=',', append=False)
dpp_history = dpp_auto_model.fit(dpp_X_train, dpp_Y_train, validation_data=(dpp_X_valid, dpp_Y_valid), epochs=100, batch_size=32, verbose=1, shuffle=True, callbacks=[dpp_csv_logger])
print(dpp_auto_model.summary())

# Prepare data for CNN-Autoencoder LSTM model
dpp_subsequences = 2
dpp_timesteps = dpp_X_train.shape[1] // dpp_subsequences
dpp_X_train_series_sub = dpp_X_train.reshape((dpp_X_train.shape[0], dpp_subsequences, dpp_timesteps, 1))
dpp_X_valid_series_sub = dpp_X_valid.reshape((dpp_X_valid.shape[0], dpp_subsequences, dpp_timesteps, 1))
print('Train set shape:', dpp_X_train_series_sub.shape)
print('Validation set shape:', dpp_X_valid_series_sub.shape)

# Define CNN- Autoencoder LSTM model
dpp_model_cnn_Autolstm = Sequential()
dpp_model_cnn_Autolstm.add(TimeDistributed(Conv1D(filters=64, kernel_size=1, activation='relu'), input_shape=(None, dpp_X_train_series_sub.shape[2], dpp_X_train_series_sub.shape[3])))
dpp_model_cnn_Autolstm.add(TimeDistributed(MaxPooling1D(pool_size=2)))
dpp_model_cnn_Autolstm.add(TimeDistributed(Flatten()))
dpp_model_cnn_Autolstm.add(LSTM(50, activation='relu'))
dpp_model_cnn_Autolstm.add(Dense(1))
dpp_model_cnn_Autolstm.summary()

# Compile and train the CNN- Autoencoder LSTM model
dpp_model_cnn_Autolstm.compile(loss='mse', optimizer=Adam(learning_rate=0.01), metrics=['mse', 'mae'])
dpp_csv_logger = CSVLogger('cnnAutolstm_dpp.csv', separator=',', append=False)
dpp_history = dpp_model_cnn_Autolstm.fit(dpp_X_train_series_sub, dpp_Y_train, validation_data=(dpp_X_valid_series_sub, dpp_Y_valid), epochs=100, batch_size=32, verbose=2, shuffle=True, callbacks=[dpp_csv_logger])
print(dpp_model_cnn_Autolstm.summary())

# Plot model
plot_model(dpp_model_cnn_Autolstm, to_file='model_dpp.png')

# Make predictions
dpp_pred = dpp_model_cnn_Autolstm.predict(dpp_X_valid_series_sub)
print(dpp_pred)

# Define test data and predicted data arrays
dpp_test_data = [dpp_Y_valid]  # actual test data
dpp_predicted_data = [dpp_pred]  # predicted data

# Filter out zero values from test_data to avoid division by zero
dpp_non_zero_mask = dpp_test_data != 0
dpp_test_data_non_zero = dpp_test_data[dpp_non_zero_mask]
dpp_predicted_data_non_zero = dpp_predicted_data[dpp_non_zero_mask]

# Compute Mean Absolute Percentage Error (MAPE)
dpp_mape = np.mean(np.abs((dpp_test_data_non_zero - dpp_predicted_data_non_zero) / dpp_test_data_non_zero)) * 100
print("Mean Absolute Percentage Error (MAPE):", dpp_mape)

import numpy as np
from scipy.stats import pearsonr
from sklearn.metrics import r2_score

# Calculate Pearson correlation coefficient (r)
r, _ = pearsonr(dpp_Y_valid, dpp_pred)

# Calculate coefficient of determination (r2)
r2 = r2_score(dpp_Y_valid, dpp_pred)

print(f"correlation coefficient (r): {r}")
print(f"Coefficient of determination (r2): {r2}")

# Inverse transform predictions
dpp_pred1 = scaler.inverse_transform(dpp_pred)
dpp_Ytest1 = scaler.inverse_transform(dpp_Y_valid)

# Plot predictions
plt.figure(figsize=(10, 6))
plt.plot(dpp_Ytest1, 'blue', linewidth=5)
plt.plot(dpp_pred1, 'r', linewidth=4)
plt.legend(('Test', 'Predicted'))
plt.show()

# Save predictions to CSV
df_dpp_pred = pd.DataFrame(dpp_pred1)
dpp_csv_filename = 'dpp_pred1.csv'
df_dpp_pred.to_csv(dpp_csv_filename)

# Concatenate predictions and transform data for further processing
dpp_dataset_total1 = pd.concat((df_dpp_pred, df_dpp_pred), axis=0)
dpp_inputs1 = dpp_dataset_total1.values
dpp_inputs1 = dpp_inputs1.reshape(-1, 1)
dpp_inputs1 = scaler.transform(dpp_inputs1)

# Prepare test data for prediction
dpp_time_step = 4
dpp_X_test = []
for i in range(dpp_time_step, 365 + dpp_time_step):
    dpp_X_test.append(dpp_inputs1[i - dpp_time_step:i, 0])
dpp_X_test = np.array(dpp_X_test)
dpp_X_test = dpp_X_test.reshape((dpp_X_test.shape[0], dpp_X_test.shape[1], 1))
dpp_predicted1_val = dpp_model_cnn_Autolstm.predict(dpp_X_test)
dpp_predicted1_val = scaler.inverse_transform(dpp_predicted1_val)
