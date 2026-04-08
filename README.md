## Branch Update

This branch extends the working authentication flow and adds the first integrated machine learning prediction feature to the current bike-sharing web application.

### Main updates in this branch

#### 1. Authentication flow
- Added a login page (`login.html`) and a register page (`register.html`)
- Added matching frontend styling files for both pages (`login.css`, `register.css`)
- Added Flask routes for:
  - `/`
  - `/login`
  - `/register`
  - `/index`
  - `/map`
- Updated the page flow so that:
  - the default entry point `/` redirects to the login page
  - successful login redirects the user to the main page (`index.html`)
  - if a user is not found, they are guided to register first
- Copied the main map interface structure into `index.html`, which is now used as the main front-end page
- Implemented backend registration logic:
  - validates required fields
  - checks for duplicate email addresses
  - hashes the password before storing it
  - inserts the new user into the database
- Implemented backend login logic:
  - checks whether the user exists
  - verifies the hashed password
  - only allows valid login to proceed to the main page
- Added flash message support for login/register feedback
- Added a `users` table to the database schema in `sql/init.sql`

#### 2. Machine learning notebook
- Added an ML notebook for bike availability prediction:
  - `ml_model/bike_availability_prediction.ipynb`
- The notebook defines the prediction goal as:
  - predicting the number of available bikes at a selected station and selected time
- The notebook includes:
  - dataset inspection
  - basic data cleaning checks
  - time-based feature engineering
  - practical feature selection for deployment
  - train/test split
  - model comparison across four regression models
  - final model selection
  - model export as `.pkl`
- The earlier data inspection / cleaning foundation was based on prior group work and then extended in this branch into a complete model-selection and deployment-oriented notebook

#### 3. Final ML model
- Compared four models:
  - Linear Regression
  - Ridge Regression
  - Decision Tree Regressor
  - Random Forest Regressor
- Selected **Random Forest** as the final model because it provided the best balance between:
  - predictive performance
  - and practical deployment in the web application
- Saved the trained model as:
  - `ml_model/best_bike_model.pkl`

#### 4. Prediction feature integrated into Flask
- Added a bike availability prediction panel to the main front-end page
- Users can:
  - select a station on the map
  - enter a date
  - enter a time
  - request a prediction
- Implemented a Flask prediction route:
  - `/api/predict`
- The backend prediction flow now:
  - receives `station_id`, `date`, and `time`
  - derives time-based features
  - retrieves station-related information
  - retrieves weather-related values
  - loads the trained `.pkl` model
  - performs prediction
  - returns the predicted number of available bikes as JSON
- The front end displays the predicted available bikes directly in the prediction panel on the main page

---

## Users table fields
- `id`
- `first_name`
- `last_name`
- `email`
- `phone_number`
- `password_hash`
- `created_at`

---

## Current status

### Authentication
- Registration has been tested successfully with data stored in the database
- Login correctly validates credentials before redirecting
- The application now follows the intended page flow:
  - Login → Register (if needed) → Index

### Machine learning
- The prediction notebook is complete in its main structure
- The final selected model has been saved as a `.pkl` file
- The prediction feature has been connected to the Flask application
- The web page can now display predicted available bikes for a selected station, date, and time

---

## Notes
- The ML notebook focuses on a deployment-oriented prediction goal rather than only offline model performance
- Feature selection was guided not only by predictive value, but also by whether the required features can realistically be reconstructed at runtime from:
  - user input
  - station information
  - and weather data
- EC2 deployment and related environment integration are handled separately