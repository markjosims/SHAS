import pandas as pd
from tqdm import tqdm
import os
from glob import glob
from typing import Dict, List, Union
from pathlib import Path
from pympi import Eaf
import shutil
import yaml

GDRIVE_METADATA = 'data/tira-metadata-gdrive.csv'
GDRIVE_RECORDINGS_DIR = 'G:\Shared drives\Tira\Recordings'
LOCAL_RECORDINGS_DIR = 'data/recordings/'
CSV_OUT = 'data/tira-annotated-metadata.csv'
YAML_OUT = 'data/tira-speech-segments.yaml'

tqdm.pandas()

def main():
    df = pd.read_csv(GDRIVE_METADATA)
    is_annotated = df['Annotations done(ish)?'].str.contains('done') |\
        df['Annotations done(ish)?'].str.contains('yes')
    not_zoom = ~df['Filename'].apply(str.lower).str.contains('zoom')
    print(f"Of {len(df)} recordings {len(df[is_annotated])} are annotated.")
    print(f"{len(df[is_annotated&not_zoom])} are not listed as Zoom recordings.")

    print("Getting utterance metadata...")
    eaf_filestems = get_eaf_filestems(GDRIVE_RECORDINGS_DIR)
    annotated = df[is_annotated&not_zoom].progress_apply(
        lambda row: get_segment_metadata(row, eaf_filestems),
        axis=1
    )
    print("Saving utterance metadata to", CSV_OUT)
    annotated.to_csv(CSV_OUT, index=False)

    print("Getting timestamps for utterances...")
    utterance_timestamps = []
    annotated['Filename'].progress_apply(
        lambda fname: add_segments_to_list(eaf_filestems[fname], utterance_timestamps)
    )
    print(f"Found {len(utterance_timestamps)} utterances")
    print(f"Saving timestamps to {YAML_OUT}")
    with open(YAML_OUT, 'w') as f:
        yaml.dump(utterance_timestamps, f)

    print(f"Copying files from GDrive to {LOCAL_RECORDINGS_DIR}...")
    annotated['Filename'].progress_apply(
        lambda fname: copy_recording_files(eaf_filestems[fname], Path(LOCAL_RECORDINGS_DIR))
    )


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
    media_path = get_media_path(eaf_path)
    segs = eaf.get_annotation_data_for_tier('IPA Transcription')
    for start_ms, end_ms, _ in segs:
        start_sec = start_ms/1000
        end_sec = end_ms/1000
        duration = end_sec-start_sec
        seg_list.append({
            'duration': duration,
            'offset': start_sec,
            'speaker_id': 'HIM',
            'wav': media_path,
        })

def copy_recording_files(eaf_path: str, new_dir: Path) -> None:
    media_path = get_media_path(eaf_path)
    eaf_name = Path(eaf_path).name
    media_name = Path(media_path).name
    new_eaf = str(new_dir/eaf_name)
    new_media = str(new_dir/media_name)
    try:
        if not os.path.exists(new_eaf):
            shutil.copy(eaf_path, new_eaf)
    except FileNotFoundError as error:
        print(error)
        print(f"Couldn't copy eaf file {eaf_name}, skipping")
    try:
        if not os.path.exists(new_media):
            shutil.copy(media_path, new_media)
    except FileNotFoundError as error:
        print(error)
        print(f"Couldn't copy wav file {media_name}, skipping")

def get_media_path(eaf_path: str) -> str:
    # # NOTE: media path in eaf file may be configured for various OS
    # # for this reason, get media path name and concatenate to eaf_path parent dir
    # eaf_obj = Eaf(eaf_path)
    # media_paths = [x['MEDIA_URL'] for x in eaf_obj.media_descriptors]
    # media = media_paths[0]
    # media_name = Path(media).name
    # return str(Path(eaf_path).parent/media_name)
    
    # probably safest to just assume media path is same as eaf path
    # with .wav extension
    return eaf_path.replace('.eaf', '.wav')

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