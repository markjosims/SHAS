import pandas as pd
import os
from glob import glob
from typing import Dict, List, Union
from pathlib import Path
from pympi import Eaf
import yaml

GDRIVE_METADATA = 'data/tira-metadata-gdrive.csv'
GDRIVE_RECORDINGS_DIR = 'G:\Shared drives\Tira\Recordings'
CSV_OUT = 'data/tira-annotated-metadata.csv'
YAML_OUT = 'data/tira-speech-segments.yaml'

def main():
    df = pd.read_csv(GDRIVE_METADATA)
    is_annotated = df['Annotations done(ish)?'].str.contains('done') |\
        df['Annotations done(ish)?'].str.contains('yes')
    not_zoom = ~df['Filename'].apply(str.lower).str.contains('zoom')
    print(f"Of {len(df)} recordings {len(df[is_annotated])} are annotated.")
    print(f"{len(df[is_annotated&not_zoom])} are not listed as Zoom recordings.")

    print("Getting utterance metadata...")
    eaf_filestems = get_eaf_filestems(GDRIVE_RECORDINGS_DIR)
    annotated = df[is_annotated&not_zoom].apply(
        lambda row: get_segment_metadata(row, eaf_filestems),
        axis=1
    )
    print("Saving utterance metadata to", CSV_OUT)
    annotated.to_csv(CSV_OUT, index=False)

    print("Getting timestamps for utterances...")
    utterance_timestamps = []
    annotated['Filename'].apply(
        lambda fname: add_segments_to_list(eaf_filestems[fname], utterance_timestamps)
    )
    print(f"Found {len(utterance_timestamps)} utterances")
    print(f"Saving timestamps to {YAML_OUT}")
    with open(YAML_OUT, 'w') as f:
        yaml.dump(utterance_timestamps, f)


def get_segment_metadata(row: pd.Series, eaf_filestems: Dict[str, str]) -> pd.Series:
    filestem = row['Filename']
    if filestem not in eaf_filestems:
        print(f"{filestem=} not found in glob")
        return row
    eaf_path = eaf_filestems[filestem]
    eaf = Eaf(eaf_path)
    ipa_segments = eaf.get_annotation_data_for_tier('IPA Transcription')
    
    num_utterances  = len(ipa_segments)
    utterance_len_total = sum(
        end-start for start, end, _ in ipa_segments
    )
    utterance_len_avg = utterance_len_total//num_utterances
    
    row['num_utterances'] = num_utterances
    row['utterance_len_total'] = human_time(utterance_len_total)
    row['utterance_len_avg'] = human_time(utterance_len_avg)

    return row

def add_segments_to_list(eaf_path: str, seg_list: List[Dict[str, Union[str, float]]]) -> None:
    eaf = Eaf(eaf_path)
    segs = eaf.get_annotation_data_for_tier('IPA Transcription')
    for start_ms, end_ms, _ in segs:
        start_sec = start_ms/1000
        end_sec = end_ms/1000
        duration = end_sec-start_sec
        media_path = get_media_path(eaf)
        seg_list.append({
            'duration': duration,
            'offset': start_sec,
            'speaker_id': 'HIM',
            'wav': media_path,
        })

def get_media_path(eaf_obj: Eaf) -> str:
    media_paths = [x['MEDIA_URL'] for x in eaf_obj.media_descriptors]
    media = media_paths[0]
    # trim prefix added by ELAN
    # have to keep initial / on posix systems
    # and remove on Windows
    if os.name == 'nt':
        return media.replace('file:///', '')
    return media.replace('file://', '')
    # computers why must you be so silly

def human_time(time_ms: int) -> str:
    hours, remainder = time_ms//(3600*1000), time_ms%(3600*1000)
    min, remainder = remainder//(60*1000), remainder%(60*1000)
    sec = remainder//1000

    return f"{hours}:{min:02d}:{sec:02d}"

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