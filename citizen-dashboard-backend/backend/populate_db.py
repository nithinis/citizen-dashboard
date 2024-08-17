import pandas as pd
from sqlalchemy import create_engine, text
import json
import os
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load the Parquet file
df = pd.read_csv('/app/items_data.csv')

# Function to convert column names to slug case
def slugify(column_name):
    # Convert to lowercase, replace spaces with underscores, and remove non-alphanumeric characters
    return re.sub(r'[^a-z0-9_]', '', column_name.lower().replace(' ', '_'))

# Convert all column names to slug case
df.columns = [slugify(col) for col in df.columns]

# Convert all columns to JSON strings
for column in df.columns:
    df[column] = df[column].apply(lambda x: json.dumps(x) if pd.notnull(x) else None)

# Read the PostgreSQL database password from Docker secret
with open('/run/secrets/citizen_dashboard_sql_password', 'r') as file:
    password = file.read().strip()

# Create a connection to the PostgreSQL database
engine = create_engine(f'postgresql://postgres:{password}@db:5432/agenda_items')

# Define the table schema with JSONB columns
create_table_query = """
CREATE TABLE IF NOT EXISTS agenda_items (
    id SERIAL PRIMARY KEY,
    meeting_id TEXT UNIQUE,
    {}
);
""".format(", ".join([f"{col} JSONB" for col in df.columns if col != 'meeting_id']))

# Execute the table creation query
with engine.connect() as connection:
    connection.execute(text(create_table_query))
    logging.info("Table created successfully.")

# Append table to sql database
df.to_sql('agenda_items', engine, if_exists='append', index=False)
