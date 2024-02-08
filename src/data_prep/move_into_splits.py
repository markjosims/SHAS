import pandas as pd
import os
import shutil

DATA_DIR = '/mnt/cube/home/AD/mjsimmons/markjosims/tira-elan'
CSV = '/mnt/cube/home/AD/mjsimmons/markjosims/tira-annotated-splits.csv'

def main():
    df = pd.read_csv(CSV)
    df.apply(move_to_split, axis=1)

def move_to_split(row):
    split = row['split']
    filestem = row['Filename']
    path = os.path.join(DATA_DIR, filestem)
    new_path = os.path.join(DATA_DIR, split, filestem)
    shutil.move(path+'.eaf', new_path+'.eaf')
    shutil.move(path+'.wav', new_path+'.wav')

if __name__ == '__main__':
    main()