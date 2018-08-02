"""
Functions for various graphs in Kojak
"""
import matplotlib.pyplot as plt
import numpy as np
from sklearn.model_selection import learning_curve

def home_price_prediction_resids (predictions, actuals):
	"""
	Graph home price predictions versus Residuals

	"""

	fig, ax = plt.subplots()
	plt.scatter(predictions, (predictions - actuals), alpha = 0.2)
	ax.set(title='Residuals versus Predictions', xlabel='Home Price Prediction', ylabel='Residual')
	ax.axhline(y=np.mean((predictions- actuals)), color='r', label='Average', linestyle='--', linewidth=1)


def home_price_prediction_resids_as_percentage (predictions, actuals):
	"""
	Graph home price predictions versus Residuals as Percentage of Actual Home Price

	"""

	fig, ax = plt.subplots()
	plt.scatter(predictions, abs (predictions - actuals) / actuals, alpha = 0.2)
	ax.set(title='Residuals versus Predictions', xlabel='Home Price Prediction', ylabel='Residual')
	ax.axhline(y=np.mean( abs(predictions- actuals) / actuals), color='r', label='Average', linestyle='--', linewidth=1)


def draw_learning_curve (model, X_train, y_train, metric):
	"""
	Pass a model and get a learning curve 

	model is a scikit learn model
	X_train,y_train are the feature / target arrays to train the model
	"""

	train_sizes, train_scores, test_scores = learning_curve(model,X_train,y_train, scoring = metric, cv=10)


	train_scores = np.array(-1) * train_scores
	test_scores = np.array(-1) * test_scores


	train_mean = np.mean(train_scores, axis = 1)
	train_std = np.std(train_scores, axis =1)

	test_mean = np.mean(test_scores, axis=1)
	test_std = np.std(test_scores, axis=1)


	fig = plt.figure(figsize=(15,10))
	plt.plot(train_sizes,np.mean(train_scores, axis=1), color ='blue',marker = 'o', label ="training "  + metric)
	plt.plot(train_sizes, np.mean(test_scores, axis=1), color = 'green',marker = 's',label ="validation " + metric)

	plt.fill_between(train_sizes,
	                train_mean + train_std,
	                train_mean - train_std,
	                alpha=0.2, color = 'blue')

	plt.fill_between(train_sizes,
	                test_mean + test_std,
	                test_mean - test_std,
	                alpha=0.2, color = 'green')


	plt.title("Learning Curve", fontsize = 25)
	plt.xlabel('Number of Training Samples', fontsize = 25)
	plt.ylabel('Error', fontsize = 25)
	plt.tick_params(labelsize=20)
	plt.legend(loc='upper right', fontsize = 18)