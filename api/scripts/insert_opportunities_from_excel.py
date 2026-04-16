import argparse
import os
from pathlib import Path
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load MongoDB connection settings from the repo .env file
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / '.env')
MONGODB_URL = os.getenv(
    'MONGODB_URL',
    'mongodb+srv://scholarsite:1LdbHC9zmSZxWKrR@cluster0.djrvguc.mongodb.net/?appName=Cluster0'
)
DATABASE_NAME = os.getenv('DATABASE_NAME', 'scholarsite')

COLUMN_MAPPING = {
    'ID': 'id',
    'Title': 'title',
    'Category': 'category',
    'Tags': 'tags',
    'Description': 'description',
    'Rating': 'rating',
    'State': 'state',
    'Cost': 'cost',
    'Web Link': 'sourceLink',
    'Deadline': 'deadline'
}


def normalize_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return value


def row_to_document(row: dict) -> dict:
    doc = {}
    for source_col, dest_field in COLUMN_MAPPING.items():
        value = normalize_value(row.get(source_col))
        if value is None:
            continue
        doc[dest_field] = value

    if 'state' in doc and 'location' not in doc:
        doc['location'] = doc['state']

    doc['source'] = 'excel file'
    return doc


async def insert_opportunities_from_excel(excel_path: Path):
    if not excel_path.exists():
        raise FileNotFoundError(f'Excel file not found: {excel_path}')

    df = pd.read_excel(excel_path)
    documents = [row_to_document(row) for row in df.to_dict(orient='records')]
    documents = [doc for doc in documents if 'id' in doc]

    if not documents:
        print('No valid opportunity documents were found in the Excel file.')
        return

    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    collection = db.opportunities

    print(f'Connecting to MongoDB: {MONGODB_URL}')
    print('Creating unique index on id...')
    await collection.create_index('id', unique=True)

    upserted = 0
    for opportunity in documents:
        result = await collection.update_one(
            {'id': opportunity['id']},
            {'$set': opportunity},
            upsert=True
        )
        if result.upserted_id or result.matched_count:
            upserted += 1

    total = await collection.count_documents({})
    print(f'Upserted {upserted} opportunities. Total documents now: {total}')
    client.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Insert opportunities from an Excel file into MongoDB.')
    parser.add_argument(
        'excel_file',
        nargs='?',
        default=r'C:\Users\tauft\Downloads\List of opportunities.xlsx',
        help='Path to the Excel file containing opportunities.'
    )
    args = parser.parse_args()
    excel_path = Path(args.excel_file)

    import asyncio

    asyncio.run(insert_opportunities_from_excel(excel_path))
