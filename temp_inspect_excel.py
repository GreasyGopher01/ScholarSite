from pathlib import Path
import pandas as pd

path = Path(r'C:\Users\tauft\Downloads\List of opportunities.xlsx')
if not path.exists():
    raise FileNotFoundError(path)

df = pd.read_excel(path)
print('COLUMNS:')
print(list(df.columns))
print('ROWS:', len(df))
print(df.head(10).to_dict(orient='records'))
