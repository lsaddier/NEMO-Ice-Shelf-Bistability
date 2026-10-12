
"""
This is the script that captures all the key run parameters and is imported by GoGoNEMO.py
"""

rP_OCEANCORES='24'
rP_STOCKDIR='/scratch/Lake/lsaddier/nemo/nemo_output'
rP_WORKDIR='/scratch/Lake/lsaddier/nemo/run/jpo001_010'
rP_RBUILD_NEMO='/home/lsaddier/nemo/models/nemo_4.2.1/tools/REBUILD_NEMO/BLD/bin/rebuild_nemo.exe'
rP_MKPSI='/work/n02/n02/chbull/nemo/bld_configs/input_ajtoy/ncj_psi/post_grid_UV'
rP_PROJ='PhD_Project'
rP_CONFIG='jpo001'
rP_CASE='010'
rP_DESC='RUN DESCRIPTION. Free-slip (fw 001, and bw 002)'
rP_YEAR0='1'
rP_YEAR_MAX='160'
rP_PARTITION='Lake'

if __name__ == '__main__':
    print('This script is designed to be imported...')
