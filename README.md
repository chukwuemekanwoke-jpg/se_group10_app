# Dublin Bikes Web App - COMP30830

## Project Structure

```
dublinbikes/
│
├── app.py                  ← MAIN FILE - Run this to start the Flask server
├── requirements.txt        ← Python packages needed (install with pip)
├── .gitignore              ← Files to NOT upload to GitHub (keys, passwords)
│
├── static/                 ← Frontend files (served directly to browser)
│   ├── index.html          ← Main HTML page
│   ├── css/
│   │   └── style.css       ← Styles
│   └── js/
│       └── main.js         ← JavaScript (map, charts, API calls)
│
├── ml_model/               ← Machine Learning files
│   ├── train_model.py      ← Script to train and save the model
│   └── model.pkl           ← Saved trained model (generated after training)
│
└── data/                   ← Historical data files (CSV/JSON if not using DB)
    └── historical.csv      ← Example historical data file
```

## How to Run Locally

```bash
pip install -r requirements.txt
python app.py
```
Then open: http://127.0.0.1:5000

## How to Run on EC2

```bash
python app.py
```
Then open: http://<your-EC2-public-IP>:5000

## Environment Variables (DO NOT put real keys in code!)

Set these in your terminal before running:
```bash
export SECRET_KEY="your_secret_key"
export JCDECAUX_API_KEY="your_jcdecaux_key"
export OPENWEATHER_API_KEY="your_openweather_key"
```
