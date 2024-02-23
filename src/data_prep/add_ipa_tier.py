from glob import glob
from pympi import Elan
from pathlib import Path

GDRIVE_DIR = 'data/gdrive_eafs'
EAF_DIR = 'data/tira-elan-ac-pass2'
UNFLAT_DIR = 'data/unflat'
OVERLAP_DIR = 'data/overlap'

def main():
    eafs = glob(EAF_DIR+'/*/*.eaf')

    gdrive_eafs = glob(GDRIVE_DIR+'/*.eaf')
    basename_to_gdrive = {Path(eaf).stem:eaf for eaf in gdrive_eafs}
    for eaf in eafs:
        basename = Path(eaf).stem

        ipa_eaf_fp = get_ipa_overlap(eaf, basename_to_gdrive[basename])
        unflat_eaf_fp = unflatten_tiers(ipa_eaf_fp)
        print("output saved to", unflat_eaf_fp)

def get_ipa_overlap(eaf_fp, gdrive_eaf_fp):
    eaf = Elan.Eaf(eaf_fp)
    eaf.rename_tier('default-lt', 'label')
    gdrive_eaf = Elan.Eaf(gdrive_eaf_fp)
    ipa_tier_data = gdrive_eaf.get_annotation_data_for_tier('IPA Transcription')
    eaf.add_tier('ipa')
    for start, end, val in ipa_tier_data:
        eaf.add_annotation('ipa', start, end, val)
    overlaps = eaf.get_gaps_and_overlaps2('ipa', 'label')
    for o_start, o_end, val in overlaps:
        if val.startswith('P') or val.startswith('G'):
            # don't care about silent intervals
            continue
        midpoint = (o_start+o_end)//2
        start, end, _ = eaf.get_annotation_data_at_time('label', midpoint)[0]
        
        eaf.remove_annotation('label', (start+end)//2)
        if val == 'W12':
            eaf.add_annotation('label', start, end, 'TIC')
        else:
            eaf.add_annotation('label', start, end, 'TIC(+crosstalk?)')

    eaf.remove_tier('ipa')
    eaf.remove_tier('default')
    out_fp = Path(OVERLAP_DIR)/Path(eaf_fp).name
    eaf.to_file(out_fp)
    return out_fp

def unflatten_tiers(eaf_fp):
    eaf = Elan.Eaf(eaf_fp)
    parent_tier = 'label'
    child_tiers = ['ENG', 'TIC']
    child_type = 'ac_prob'
    eaf.add_linguistic_type(
        child_type,
        constraints='Symbolic_Association',
        timealignable=False,
    )
    for tier in child_tiers:
        tier_data = eaf.get_annotation_data_for_tier(tier)
        eaf.remove_tier(tier)
        eaf.add_tier(tier, ling=child_type, parent=parent_tier)

        for start, end, val in tier_data:
            eaf.add_ref_annotation(
                tier,
                tier2=parent_tier,
                time=(start+end)//2,
                value=val,
            )
        
    out_fp = Path(UNFLAT_DIR)/Path(eaf_fp).name
    eaf.to_file(out_fp)
    return out_fp

if __name__ == '__main__':
    main()