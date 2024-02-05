import pandas as pd

GDRIVE_METADATA = 'data/tira-metadata-gdrive.csv'

def main():
    df = pd.read_csv(GDRIVE_METADATA)
    is_annotated = df['Annotations done(ish)?'].str.contains('done') |\
        df['Annotations done(ish)?'].str.contains('yes')
    print(f"Of {len(df)} recordings {len(df[is_annotated])} are annotated.")
    

if __name__ == '__main__':
    main()