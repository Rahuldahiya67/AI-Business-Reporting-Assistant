# AI Business Reporting Assistant

## Overview
This project is an AI-powered business reporting assistant built in Python. It leverages multiple specialized agents to analyze data, generate insights, and produce reports.

## Key Components
- **app.py**: Main application entry point.
- **orchestrator.py**: Coordinates the workflow between agents.
- **agents/**: 
  - `analysis_agent.py`: Performs data analysis.
  - `data_agent.py`: Handles data processing and loading.
  - `insight_agent.py`: Generates business insights.
- **data/**: Data generation and management utilities.
- **sql/**: SQL queries for database operations.
- **utils/**: Helper functions and metrics.

## Setup
1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Run setup:
   ```
   python run_setup.py
   ```
3. Run the app:
   ```
   python app.py
   ```

## Usage
The assistant processes business data to generate automated reports and insights.

## Licence
MIT