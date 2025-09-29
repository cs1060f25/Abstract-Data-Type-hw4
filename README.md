# CS1060 Homework 4 - County Health Data API

This project provides an API for querying county health data by ZIP code.

## Attribution

This project was created with generative AI assistance (Cascade) and reviewed/edited by the student.

## Project Structure

```
.
├── api/
│   ├── __init__.py          # Python package marker
│   └── county_data.py       # FastAPI endpoint implementation
├── csv_to_sqlite.py         # Script to convert CSV to SQLite
├── data.db                  # SQLite database (included in repo)
├── requirements.txt         # Python dependencies
├── vercel.json              # Vercel deployment configuration
├── link.txt                 # Deployed API endpoint URL
├── test_api.sh              # API test script
├── .gitignore
└── README.md
```

**Note:** CSV source files (`county_health_rankings.csv`, `zip_county.csv`) are tracked using **Git LFS** (Large File Storage) due to their large size (30MB total). The generated `data.db` (32MB) is also included for deployment.

## Part 1: Data Processing

The `csv_to_sqlite.py` script converts CSV files into SQLite database tables.

### Usage

```bash
python3 csv_to_sqlite.py data.db zip_county.csv
python3 csv_to_sqlite.py data.db county_health_rankings.csv
```

### Features

- Creates tables named after CSV filenames (without extension)
- All columns are TEXT type
- Uses parameterized queries for safe insertion
- Batch inserts for performance

## Part 2: API Endpoint

The `/county_data` endpoint accepts POST requests with JSON data.

### Request Format

```bash
curl -X POST https://your-deployment.vercel.app/county_data \
  -H "Content-Type: application/json" \
  -d '{"zip": "02138", "measure_name": "Adult obesity"}'
```

### Required Parameters

- `zip`: 5-digit ZIP code (string)
- `measure_name`: One of the following health measures:
  - Violent crime rate
  - Unemployment
  - Children in poverty
  - Diabetic screening
  - Mammography screening
  - Preventable hospital stays
  - Uninsured
  - Sexually transmitted infections
  - Physical inactivity
  - Adult obesity
  - Premature Death
  - Daily fine particulate matter

### Response Codes

- **200**: Success - returns JSON array of matching health records
- **400**: Bad Request - missing required parameters or invalid format
- **404**: Not Found - no data found for the given ZIP/measure combination
- **418**: I'm a teapot - returned when `coffee=teapot` is in the request

### Example Response

```json
[
  {
    "confidence_interval_lower_bound": "0.22",
    "confidence_interval_upper_bound": "0.24",
    "county": "Middlesex County",
    "county_code": "17",
    "data_release_year": "2012",
    "denominator": "263078",
    "fipscode": "25017",
    "measure_id": "11",
    "measure_name": "Adult obesity",
    "numerator": "60771.02",
    "raw_value": "0.23",
    "state": "MA",
    "state_code": "25",
    "year_span": "2009"
  }
]
```

## Security

- All SQL queries use parameterized statements to prevent SQL injection
- Input validation on ZIP code format and measure names
- No raw string interpolation in SQL queries

## Local Development

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Generate database
python3 csv_to_sqlite.py data.db zip_county.csv
python3 csv_to_sqlite.py data.db county_health_rankings.csv

# Run locally with uvicorn
uvicorn api.county_data:app --reload
```

### Testing Locally

```bash
# Test valid request
curl -X POST http://localhost:8000/county_data \
  -H "Content-Type: application/json" \
  -d '{"zip": "02138", "measure_name": "Adult obesity"}'

# Test 418 easter egg
curl -X POST http://localhost:8000/county_data \
  -H "Content-Type: application/json" \
  -d '{"coffee": "teapot"}'

# Test 400 error (missing parameters)
curl -X POST http://localhost:8000/county_data \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Deployment to Vercel

1. Install Vercel CLI: `npm i -g vercel`
2. Login: `vercel login`
3. Deploy: `vercel --prod`
4. Update `link.txt` with your deployment URL

## Data Sources

- **ZIP to County**: [RowZero Zip Code to County](https://rowzero.io/blog/zip-code-to-state-county-metro)
- **County Health Rankings**: [County Health Rankings & Roadmaps](https://www.countyhealthrankings.org/health-data)

## License

Academic project for CS1060 - Fall 2025
