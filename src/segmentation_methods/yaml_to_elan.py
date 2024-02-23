from argparse import ArgumentParser
from typing import Optional, Sequence, Dict, Any
from pympi import Elan
from glob import glob
import pandas as pd
import yaml
import os
from pathlib import Path
from tqdm import tqdm

tqdm.pandas()

def main(argv: Optional[Sequence[str]] = None):
    args = parser.parse_args(argv)

    print('Loading yaml...')
    with open(args.yaml) as f:
        segments = yaml.safe_load(f)

    df = pd.DataFrame(segments)
    basenames = list(df['wav'].apply(lambda fp: Path(fp).stem))

    print('Finding eaf files...')
    eaf_paths = glob(
        os.path.join(args.eaf_dir, '*.eaf')
    )

    print('Making pympi Eafs objects...')
    basename_to_eafs = {
        Path(eafp).stem: Elan.Eaf(eafp) for eafp in eaf_paths
        if Path(eafp).stem in basenames
    }
    for eaf in basename_to_eafs.values():
        eaf.add_tier(args.tiername)

    df.progress_apply(
        lambda r: add_row_to_eaf(r, basename_to_eafs, args.tiername, args.overlap_tier),
        axis=1,
    )

    for stem, eaf in basename_to_eafs.items():
        out_path = os.path.join(
            args.out_dir, stem+'.eaf'
        )
        eaf.to_file(out_path)
    

def add_row_to_eaf(
        row: Dict[str, Any],
        basename_to_eafs: Dict[str, Elan.Eaf],
        tier: str,
        overlap_tier: Optional[str] = None,
    ) -> Dict[str, Any]:

    start = row['offset']
    duration = row['duration']
    end = start+duration
    start_ms = int(start*1000)
    end_ms = int(end*1000)

    stem = Path(row['wav']).stem
    eaf = basename_to_eafs[stem]

    value = ''
    if overlap_tier:
        midpoint_ms = (start_ms+end_ms)//2
        annotations = eaf.get_annotation_data_at_time(overlap_tier, midpoint_ms)
        if annotations:
            value = 'overlap'

    eaf.add_annotation(tier, start_ms, end_ms, value)


if __name__ == '__main__':
    parser = ArgumentParser("Create empty ELAN annotations from segments yaml file.")
    parser.add_argument("--yaml", "-y")
    parser.add_argument("--eaf_dir", "-e")
    parser.add_argument("--out_dir", "-o")
    parser.add_argument("--tiername", "-t")
    parser.add_argument("--overlap_tier")

    main()