import pandas as pd
import numpy as np
from collections import defaultdict
from pprint import pprint

CSV = 'data/tira-annotated-metadata.csv'
CSV_OUT = 'data/tira-annotated-splits.csv'
CATS = [
    'paradigms',
    'phrases',
    'alphabet book',
    'syntax',
    'story',
    'wordlists',
    'tonal elicitation'
 ]

def make_balanced_split(df, splitsize=0.8):
    total_utterances = df['num_utterances'].sum()
    split_records = total_utterances*splitsize
    new_df = pd.DataFrame(columns=df.columns)

    size_by_cat = {cat: 0 for cat in CATS}

    while new_df['num_utterances'].sum() < split_records:
        min_cat = min(size_by_cat, key=size_by_cat.get)
        has_cat = df['cat_list'].apply(lambda l: min_cat in l)
        if len(df[has_cat]) == 0:
            breakpoint()
        new_row = df[has_cat].sample()
        new_df = pd.concat([new_df, pd.DataFrame(new_row)])
        for cat in new_row['cat_list'].iloc[0]:
            size_by_cat[cat]+=new_row[cat].iloc[0]
        df = df.drop(new_row.index)
    return new_df, df

def count_cats_per_recording(row, cat):
    num_utts = row['num_utterances']
    cat_list = row['cat_list']
    if cat not in cat_list:
        return 0
    return num_utts / len(cat_list)

def softmax(x):
    return(np.exp(x)/np.exp(x).sum())

def as_percent(x):
    sum = x.sum()
    return x/sum

if __name__ == '__main__':
    df = pd.read_csv(CSV, keep_default_na=False)
    df['cat_list'] = df['Category']\
        .str.split('+')\
        .apply(lambda l: [s.strip().lower() for s in l])
    for cat in CATS:
        df[cat] = as_percent(df.apply(lambda row: count_cats_per_recording(row, cat), axis=1))
    df['split'] = ''

    val, remainder = make_balanced_split(df, splitsize=0.2)
    test, train = make_balanced_split(remainder, splitsize=0.25)
    
    splitdict = {'train': train, 'test': test, 'val': val}

    for name, split in splitdict.items():
        print(name)
        utterance_cats = defaultdict(lambda:0)
        recording_cats = defaultdict(lambda:0)

        def count_utterance_categories(row):
            cats = row['cat_list']
            num_utts = row['num_utterances']
            for cat in cats:
                utterance_cats[cat] += num_utts/len(cats)
                recording_cats[cat] += 1

        split.apply(count_utterance_categories, axis=1)
        pprint(dict(utterance_cats))
        pprint(dict(recording_cats))

        df.loc[split.index, 'split'] = name
    df.to_csv(CSV_OUT, index=False)