# Trading-Model
An automated trading model for the equity markets.

#### -- Project Status: [Active]

## Project Intro/Objective
This project was created to develop an automated trading model for the equity markets.  A few strategies were tested.  Expanding on the original scope, a predictive model was developed to predict whether a trade would be profitable or not, based on entry indicators/metrics.

### Methods Used
Data Scraping
Object Oriented Programming
Machine Learning
Predictive Modeling

### Technologies
Python
Yahoo Finance

### Requirements/Imports
Python 3.8.1
Pandas
Pandas Datareader
Numpy
Backtrader
Scikit Learn
Requests
Yahoo Finance
Pickle
Matplotlib

## Project Description
****1. Strategy Build:****  Wanted to have the strategy trade in time frames of less than a month.  Built around mean reversion, using a combination of indicators.

****2. Backtesting:****  Used old data (2010 - 2018) to develop and build strategy, as well as optimize indicator arguments (days for caluclations).  Took best strategy and did OOS testing on data from 2019 to now (April 2020).

****3. Model Build:****  Took trade data (indicator values at entry) and used to predict profitability from old data (2010 - 2018).
Tested model on OOS data.

****4. Forward Testing:**** Currently running model on live data and paper trading based on strategy.

****5.  Next Steps:**** Will determine after forward testing has more data

## Needs of this project
* Financial Acumen
* Trading Knowledge
* Equity Market Knowledge
* Predictive Modeling
* Feature Engineering

## Getting Started
1. Ensure local machine has program that can run python.
2. Download the following:
 * get data.v2.py
 * model1.rf.py
 * runLive.bat
 * Supplemental (Folder)
 * Data (Folder)
3. Run batch file
4. Download work.zip and extract for all other files used prior to finished product.

## Contributing Members

****Team Lead:**** [Joe Pollastrini](https://github.com/joepollastrini)
* ****Email:**** joepollastrini@gmail.com
* ****Phone:**** (630)-418-3594

## Contact
* Feel free to contact team leads with any questions, comments, or concerns!
