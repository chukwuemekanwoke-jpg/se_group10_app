# Dublin Bikes Web App - COMP30830
## Project Structure

A Flask-based web application for visualising and interacting with Dublin Bikes data. The app integrates live bike station information, weather data, and machine learning functionality to support analysis and prediction features.

##Overview

This project was developed as part of COMP30830. It provides a web-based interface for viewing Dublin Bikes station information, using live external APIs and historical data to deliver a more informative user experience.

The application includes:

1. A Flask backend
2. A frontend interface built with HTML, CSS, and JavaScript
3. Integration with the JCDecaux API for bike station data
4. Integration with the OpenWeather API for weather data
5. A machine learning component for predictions based on historical datasets
6. Deployment on AWS EC2
7. A MySQL Database hosted on AWS RDS

The main branch is simply for production only files.

##Features
1. Display Dublin Bikes station information
2. Retrieve live bike station data from the JCDecaux API
3. Retrieve weather information from the OpenWeather API
4. Provide a browser-based user interface through Flask
5. Store and access data using AWS RDS
6. Support machine learning workflows using historical data
7. Deploy in a cloud-based environment using AWS EC2

```
se_group10_app/
│
├── app.py                  # Main Flask application entry point
├── requirements.txt        # Python dependencies
├── .gitignore              # Git ignore rules
├── .env                    # Environment variables (not committed)
│
├── static/                 # Frontend assets
│   ├── index.html          # Main webpage
│   ├── css/
│   │   └── style.css       # Stylesheet
│   └── js/
│       └── main.js         # Frontend logic (maps, charts, API calls)
│
├── ml_model/               # Machine learning files
│   ├── train_model.py      # Model training script
│   └── model.pkl           # Saved trained model
│
└── data/                   # Historical data files
    └── historical.csv      # Example dataset
```


## Technologies Used
1. Python
2. Flask
3. HTML / CSS / JavaScript
4. AWS EC2
5. AWS RDS
6. JCDecaux API
7. OpenWeather API
8. Machine Learning tools (depending on packages in requirements.txt)

## Requirements
Before running the applicaiton, ensure you have;
1. Python 3.12
2. pip
3. Access to the required valid JCDecaux API key
4. Access to the required valid OpenWeather API key
5. A configured .env file
6. Access to the configured AWS RDS database


## Installation
Clone the repository and install dependencies

```
bash
git clone https://github.com/chukwuemekanwoke-jpg/se_group10_app.git
cd se_group10_app
pip install -r requirements.txt

```
## Environment Configuration
This project uses a .env file to manage enviornment variables. 
Create a .env file in the project root and add the required configuration values:

```
.env
SECRET_KEY=your_secret_key
JCDECAUX_API_KEY=your_jcdecaux_key
OPENWEATHER_API_KEY=your_openweather_key
DB_HOST=your_rds_endpoint
DB_NAME=your_database_name
DB_USER=your_database_username
DB_PASSWORD=your_database_password
DB_PORT=3306
#Do not commit the .env file to GitHub.
```

## Running the Application Locally
Once dependencies are installed and the .env file is configured, run;
```
bash

python app.py
```
Then open the app in your browser:
```
bash
http://127.0.0.1:5000
```

## Deployment
The application is deployed on AWS EC2, with AWS RDS used as the database service.

## EC2 Deployment
To launch the applicaiton on the EC2 instance:
```
bash

python app.py
```
Then access the application via:

```
bash

http://<your-ec2-public-ip>:5000
```
### Deployment notes
Make sure that
1. Port 5000 is open in the EC2 security group
2. The EC2 instance can connect to the RDS instance
3. The RDS security group allows traffic from the EC2 instance
4. All requried environment variables are present in the .env file

## Database
The application uses MySQL DB hosted on AWS RDS as its database backend.

Typical database environment variables include:
1. DB_HOST
2. DB_NAME
3. DB_USER
4. DB_PASSWORD
5. DB_PORT

Make sure the following are correctly configured:
1. The RDS instance is active
2. Credentials are valid
3. Network access between EC2 and RDS is allowed

## Machine Learning
The ml_model/ directory contains files related to the machine learning functionality.

### ML Files
1. train_model.py - trains the machine learning model
2. model.pkl - stores the trained model

To retrain the model:
```
bash
pythin ml_model/train_model.py
```

## Data
Historical data used for analytics or model training is stored in the data/directory
Example;
```
bash

data/historical.csv
```
This dataset can be updated or extended depending on the project requirements.

## Troubleshooting

### Application does not start
1. Ensure all dependencies are installed
2. Check that the .env file exists and contains valid values
3. Verify that API keys are correct

### Database connection issues
1. Confirm the AWS RDS endpoint, username, password, and port
2. Ensure the RDS security group allows traffic from the EC2 instance
3. Check that the database instance is running

### EC2 deployment issues
1. Confirm the Flask app is running on the server
2. Ensure port 5000 is open in the EC2 security group
3. Verify the correct EC2 public IP or DNS is being used

## Development Notes
1. Keep all sensitive credentials in the .env files
2. Ensure .env is listed in .gitignore
3. Avoid harcoding API keys or secrets in source code
4. Keep the main branch focused on stable, deployment-ready code

## License
This project was developed for COMP30830.
