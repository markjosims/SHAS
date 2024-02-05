import pandas as pd
import os
from glob import glob
from typing import Dict
from pathlib import Path

GDRIVE_METADATA = 'data/tira-metadata-gdrive.csv'
GDRIVE_RECORDINGS_DIR = 'G:\Shared drives\Tira\Recordings'

def main():
    df = pd.read_csv(GDRIVE_METADATA)
    is_annotated = df['Annotations done(ish)?'].str.contains('done') |\
        df['Annotations done(ish)?'].str.contains('yes')
    print(f"Of {len(df)} recordings {len(df[is_annotated])} are annotated.")

    eaf_filestems = get_eaf_filestems(GDRIVE_RECORDINGS_DIR)
    annotated = df[is_annotated]

def get_segment_metadata(row: pd.Series) -> pd.Series:
    ...


def get_eaf_filestems(eaf_dir: str) -> Dict[str, str]:
    """
    find all .eaf files in `eaf_dir` recursively
    return dict that maps the file stem to the full path
    """
    eaf_list = glob(os.path.join(eaf_dir, '**\\*.eaf'), recursive=True)
    filestem_dict = {
        Path(eaf_path).stem: eaf_path for eaf_path in eaf_list
    }
    return filestem_dict

if __name__ == '__main__':
    main()