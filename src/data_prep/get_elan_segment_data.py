import pandas as pd
import os
from glob import glob
from typing import Dict
from pathlib import Path
from pympi import Eaf

GDRIVE_METADATA = 'data/tira-metadata-gdrive.csv'
GDRIVE_RECORDINGS_DIR = 'G:\Shared drives\Tira\Recordings'

def main():
    df = pd.read_csv(GDRIVE_METADATA)
    is_annotated = df['Annotations done(ish)?'].str.contains('done') |\
        df['Annotations done(ish)?'].str.contains('yes')
    not_zoom = ~df['Filename'].apply(str.lower).str.contains('zoom')
    print(f"Of {len(df)} recordings {len(df[is_annotated])} are annotated.")
    print(f"{len(df[is_annotated&not_zoom])} are not listed as Zoom recordings.")

    eaf_filestems = get_eaf_filestems(GDRIVE_RECORDINGS_DIR)
    annotated = df[is_annotated&not_zoom].apply(
        lambda row: get_segment_metadata(row, eaf_filestems),
        axis=1
    )

def get_segment_metadata(row: pd.Series, eaf_filestems: Dict[str, str]) -> pd.Series:
    filestem = row['Filename']
    if filestem not in eaf_filestems:
        print(f"{filestem=} not found in glob")
        return row
    eaf_path = eaf_filestems[filestem]
    eaf = Eaf(eaf_path)

    return row


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