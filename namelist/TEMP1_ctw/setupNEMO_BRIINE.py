#!/usr/bin/env python 
#   Author: Christopher Bull. 
#   Affiliation:  Department of Geography and Environmental Sciences, 
#                 Northumbria University, Newcastle upon Tyne, UK
#   Contact: christopher.bull@northumbria.ac.uk
#   Date created: Mon, 15 Feb 2021 09:43:25
#   Machine created on: SB2Vbox
#
#   Update (15/02/2021): modified to work on ARCHER2 with nemo3.6 STABLE 
"""
 This is the script to set-up NEMO runs

 Update (16/05/2022): removed a lot of fluff to put it on github

 Update (13/11/2023): hacked with Louis S for psmn e5

 Update (10/10/2024): Louis S removed a lot of stuff
"""
import sys,os
import datetime
import contextlib as ctx
import shutil
import glob
import subprocess
import f90nml
import numpy as np

class bcolors:
    """
    stolen: https://stackoverflow.com/questions/287871/how-to-print-colored-text-in-python
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def mkdir(p):
    """make directory of path that is passed"""
    try:
       os.makedirs(p)
       print("output folder: "+p+ " does not exist, we will make one.")
    except OSError as exc: # Python >2.5
       import errno
       if exc.errno == errno.EEXIST and os.path.isdir(p):
          pass
       else: raise

def mkdomcfg(rP_WORKDIR,workfol,DOMAINcfg,BFILE,rP_nml_patch,killisf):
    """function to do leg work for making domain_cfg.nc
    """
    os.mkdir(rP_WORKDIR+'/domaincfg/')
    os.chdir(rP_WORKDIR+'/domaincfg/')
    wdir=workfol+'domaincfg/'

    ifiles=sorted(glob.glob(wdir+'*'))
    assert(ifiles!=[]),"glob didn't find anything!"
    for f in ifiles:
        if os.path.isfile(f):
            shutil.copy2(f,rP_WORKDIR+'/domaincfg/'+os.path.basename(f))

    os.symlink(DOMAINcfg, 'make_domain_cfg.exe')
    if not killisf:
        os.symlink(BFILE, 'isf_draft_meter.nc')
        os.symlink(BFILE, 'bathy_meter.nc')
    else:
        shutil.copy2(BFILE,rP_WORKDIR+'/domaincfg/bathy_meter_template.nc')
        subprocess.call('module load nco;ncks -x -v isf_draft bathy_meter_template.nc bathy_meter_middle.nc;ncrename -v Bathymetry_isf,Bathymetry bathy_meter_middle.nc bathy_meter.nc;',shell=True)
        if os.path.exists(rP_WORKDIR+'/domaincfg/bathy_meter.nc'):
            print("We have sucessfully killed the ice-shelf!") 
        else:
            print("We have not sucessfully killed the ice-shelf!") 
            import pdb;pdb.set_trace()
        os.remove(rP_WORKDIR+'/domaincfg/bathy_meter_middle.nc')
        os.remove(rP_WORKDIR+'/domaincfg/bathy_meter_template.nc')


def mkmesh(workfol,rP_WORKDIR,DOMAINcfg,BFILE,rP_nml_patch=None,killisf=False,extdomaincfg=['','']):
    """NEMO 4 in some cases, needs you to make a domain_cfg.nc file

    Note to make the namelist_cfg that worked for NEMO 4.0.4 we had to, hacking from:
        /mnt/lustre/a2fs-work2/work/n02/n02/chbull/nemo/nemo_output/aj_ts_melt_off_dynlin_014/0001/namelist.0001
        -change jp_cfg into an integer
        -remove various elements from namrun
        -remove a few things from namdom (everything between rn_rdt and ln_crs)
        -added ln_teos10    = .true.
    
    :DOMAINcfg: executable to use
    :extdomaincfg: 3 options
        ['',''] - default, we will use parameters provided or modified via namelist (alone)
        ['hacked','/PATH/TO/pythonscripttohack_domain_cfg.nc'] - uses default but will additionally hack the domain_cfg.nc output using passed file
        ['rogue','/PATH/TO/domain_cfg.nc'] - total rogue, i.e., if you'd rather use an externally provided domaincfg (made elsewhere).
    :returns: @todo
    """
    if extdomaincfg[0]=='':
        mkdomcfg(rP_WORKDIR,workfol,DOMAINcfg,BFILE,rP_nml_patch,killisf)
    elif extdomaincfg[0]=='hacked':
        mkdomcfg(rP_WORKDIR,workfol,DOMAINcfg,BFILE,rP_nml_patch,killisf)
        print(bcolors.HEADER+ "WARNING: "+bcolors.ENDC   +'We are going to hack the domaincfg, using '+os.path.dirname(extdomaincfg[1])+'/'+bcolors.HEADER+os.path.basename(extdomaincfg[1])+ bcolors.ENDC)
    elif extdomaincfg[0]=='rogue':
        assert(os.path.exists(extdomaincfg[1])),"domain_cfg passed does not exist!" + extdomaincfg[1]
        #shutil.copy2(extdomaincfg[1],rP_WORKDIR+'/domain_cfg.nc')
        os.symlink(extdomaincfg[1], rP_WORKDIR+'/domain_cfg.nc')
        print(bcolors.HEADER+ "WARNING: "+bcolors.ENDC   +'We are using an externally provided domaincfg '+os.path.dirname(extdomaincfg[1])+'/'+bcolors.HEADER+os.path.basename(extdomaincfg[1])+ bcolors.ENDC)
    else:
        pass
        print(bcolors.WARNING + "ERROR: "  +'Do not know what to do with your passed argument for extdomaincfg'+  bcolors.ENDC )
        import pdb;pdb.set_trace()

    return

def convert_FS_to_str(list_FS):
    # list_FS contains all sfx (g/m²/s), for each year
    # list_str contains the corresponding indexes
    list_str = []
    for FS in list_FS:
        index_forc = int(FS * 10000)
        string = str(index_forc).zfill(4)
        list_str.append(string)
    
    return list_str


def mk_hyst(year_max, year_increment, Fs_begin, Fs_increment):
    # make the Fs_list for Hysteresis exp    
    year_top = year_max//2
    Fs_list = [Fs_begin]*year_increment

    steps = year_top//year_increment - 1
    for i in range(steps):
        Fs_list += [Fs_begin + (i+1)*Fs_increment]*year_increment

    Fs_list_bw = Fs_list.copy()
    Fs_list_bw.reverse()
    Fs_list += Fs_list_bw

    return Fs_list


def mk_steps(year_max, year_increment, Fs_begin, Fs_increment):
    # Make Fs_list for hysteresis exp only fw or bw
    Fs_list = [Fs_begin]*year_increment

    steps = year_max//year_increment - 1
    for i in range(steps):
        Fs_list += [Fs_begin + (i+1)*Fs_increment]*year_increment
        
    return Fs_list



def main(workfol,rP_CONFIG,rP_CONFIG_TYPE,rP_CASE,NEMOexe,WCONFIG,BFILE,TSFILE,rP_nml_patch=None,FLXFCE='',extdomaincfg=['','']):
    """@todo: Docstring for main
    
    :DOMAINcfg: executable to use
    :extdomaincfg: 3 options
        ['',''] - default, we will use parameters provided or modified via namelist (alone)
        ['hacked','/PATH/TO/pythonscripttohack_domain_cfg.nc'] - uses default but will additionally hack the domain_cfg.nc output using passed file
        ['rogue','/PATH/TO/domain_cfg.nc'] - total rogue, i.e., if you'd rather use an externally provided domaincfg (made elsewhere).
    :returns: @todo
    """
    # check here that the symlinks exist
    print("Check forcing files (bathymetry/ts/executable) exist..")
    assert(os.path.exists(BFILE)),"can't find file: "+BFILE
    assert(os.path.exists(TSFILE)),"can't find file: "+TSFILE
    assert(os.path.exists(NEMOexe)),"can't find file: "+NEMOexe
    print(".. Forcing files exist!")


    #change me alethea to tippaccs (check spelling)
    rP_PROJ='PhD_Project'

    
    rP_DESC="RUN DESCRIPTION. Backward"
    

    N_nodes=1
    core_per_node=24
    rP_OCEANCORES=N_nodes*core_per_node  # number of core
    running_time='8-0:00:00'   # day-hours:minutes:seconds
    partition='Lake'   # 'Lake-short' (4h)   'Lake' (8d)   'Cascade' (8d)
    rP_PARTITION='Lake'

    RDIR="/scratch/"+rP_PARTITION+"/lsaddier/nemo/run"
    rP_WORKDIR=RDIR+'/'+rP_CONFIG+'_'+rP_CASE

    rP_YEAR0=1
    rP_YEAR_MAX=160

    year_increment = 10 #y
    FS_begin = 0. #g/m²/s
    FS_increment = 0.005 #g/m²/s

    FS_list = mk_steps(rP_YEAR_MAX,year_increment,FS_begin,FS_increment)

    FS_list.reverse()

    #FS_list = np.ones(rP_YEAR_MAX) * 0.05


    #change me alethea - run dir for output of runs
    rP_STOCKDIR="/scratch/"+rP_PARTITION+"/lsaddier/nemo/nemo_output" #- restart and output directory; now that rdf is offline


    FORCING='/work/n01/shared/core2'

    #make sure you've compiled this!
    #rP_RBUILD_NEMO='/home/lsaddier/nemo/models/nemo_4.2.1/tools/REBUILD_NEMO/rebuild_nemo'
    rP_RBUILD_NEMO='/home/lsaddier/nemo/models/nemo_4.2.1/tools/REBUILD_NEMO/BLD/bin/rebuild_nemo.exe'
    rP_MKPSI='/work/n02/n02/chbull/nemo/bld_configs/input_ajtoy/ncj_psi/post_grid_UV'

    DATE=str(datetime.datetime.now())

    ##-- User's choices END

    ##############################################
    ##-- initializations

    print("****************************************************")
    print("*          NEMO SIMULATION                         " )
    print("*   project      "+rP_PROJ                              )
    print("*   config       "+rP_CONFIG                          )
    print("*   config_type  "+bcolors.WARNING+rP_CONFIG_TYPE                     +bcolors.ENDC  )
    print("*   NEMOexe      "+NEMOexe                           )
    print("*   wconfig      "+WCONFIG                           )
    print("*   case         "+bcolors.WARNING+rP_CASE                            +bcolors.ENDC  )
    print("*   desc         "+rP_DESC                              )
    print("****************************************************")

    #############################################################
    ###-- prepare run dir

    print( "  ")
    print( "NOTE: we are using wconfig:"+WCONFIG)
    print( "  ")

    ##create run folder
    if os.path.exists(rP_WORKDIR):
        print(bcolors.FAIL+"WARNING: "+rP_WORKDIR+" already exists, so we will STOP"+bcolors.ENDC  )
        sys.exit("")
    else:
        print("WARNING: "+rP_WORKDIR+" does not exist , so we will try "+bcolors.WARNING+"CREATE"+bcolors.ENDC +' it.' )
        os.mkdir(rP_WORKDIR)
        os.chdir(rP_WORKDIR)

        with ctx.closing(open(rP_WORKDIR+'/README','w')) as handle:
            handle.write('*****************************************************'+"\n")
            handle.write('*          NEMO SIMULATION                          *'+"\n")
            handle.write('*   project   '+rP_PROJ            +'                     *'+"\n")
            handle.write('*   config    '+rP_CONFIG          +'                     *'+"\n")
            handle.write('*   NEMOexe   '+NEMOexe         +'                     *'+"\n")
            handle.write('*   case      '+rP_CASE            +'                     *'+"\n")
            handle.write('*   Desc      '+rP_DESC            +'                     *'+"\n")
            handle.write('*   Date      '+DATE            +'                     *'+"\n")
            handle.write('*                                                   *'+"\n")
            handle.write('*   Users choices:                                 *'+"\n")
            handle.write('*   rP_PROJ        '+rP_PROJ        + '                      *'+"\n")
            handle.write('*   rP_CONFIG      '+rP_CONFIG      + '                      *'+"\n")
            handle.write('*   rP_CONFIG_TYPE '+rP_CONFIG_TYPE + '                      *'+"\n")
            handle.write('*   BFILE       '+BFILE       + '                      *'+'\n')
            handle.write('*   TSFILE      '+TSFILE      + '                      *'+'\n')
            if FLXFCE!='':
                handle.write('*   FLXFILE      '+FLXFCE      + '                      *'+'\n')
                #handle.write('*   ENAME      '+ifile.attrs['ename']      + '                      *'+'\n')
            handle.write('*   rP_CASE        '+rP_CASE        + '                      *'+'\n')
            handle.write('*   rP_YEAR0       '+str(rP_YEAR0)      + '                      *'+'\n')
            handle.write('*   rP_YEAR_MAX    '+str(rP_YEAR_MAX)   + '                      *'+'\n')
            handle.write('*   RDIR        '+RDIR        + '                      *'+'\n')
            handle.write('*   rP_WORKDIR     '+rP_WORKDIR     + '                      *'+'\n')
            handle.write('*   rP_STOCKDIR    '+rP_STOCKDIR    + '                      *'+'\n')
            handle.write('*   rP_CONFIG     '+rP_CONFIG     + '                      *'+'\n')
            handle.write('*   FORCING     '+FORCING     + '                      *'+'\n')
            handle.write('*   NEMOdir     '+NEMOdir     + '                      *'+'\n')
            handle.write('*****************************************************'+'\n')

        #cat << EOF > ./env_rec
        with ctx.closing(open(rP_WORKDIR+'/env_rec','w')) as handle:
            handle.write('*   Date      '+DATE            +'*'+"\n")
            handle.write('*   record of current env:      '+"\n")
            ENV= os.getenv('ENV')
            handle.write(str(ENV)+"\n")
            handle.write(''+"\n")
            handle.write('*   record of current path:      '+"\n")
            ENV= os.getenv('PATH')
            handle.write(ENV+"\n")


        #nemo and xios
        #os.symlink(src, dst)
        os.symlink(NEMOexe, 'nemo.exe')
        #os.symlink('/work/n02/n02/asmou/NEMORC/cfgs/ROSS025_4.2/EXP02/domain_cfg.nc', 'domain_cfg.nc')

        os.symlink(WCONFIG+'/domain_cfg.nc', 'domain_cfg.nc')  #Note for LS: geometry is actually contained in this file!


        #change me alethea -- add all namelist ref and cfg files, AND xml files for xios into GoGGoNEMO
        ifiles=sorted(glob.glob(workfol+'*'))
        assert(ifiles!=[]),"glob didn't find anything!"
        for f in ifiles:
            if os.path.isfile(f):
                shutil.copy2(f,rP_WORKDIR+'/')

        #Important part: manage surface forcing
        #shutil.move(rP_WORKDIR+'/'+'namelist_ref',rP_WORKDIR+'/'+'namelist_ref')
        #print(bcolors.WARNING + "WARNING: Using namelist_ref" + bcolors.ENDC)

        os.mkdir(rP_WORKDIR+'/flxfce/')
  
        print()
        print(bcolors.WARNING + "WARNING: Using flxfce " +  FLXFCE + bcolors.ENDC)
        print()
            

        list_string = convert_FS_to_str(FS_list)
        for yy in np.arange(rP_YEAR0,rP_YEAR_MAX+1):
            index_forc = list_string[yy-rP_YEAR0]
                    
            flx_path = FLXFCE+index_forc
            assert(os.path.exists(flx_path+'T.nc')),"can't find flux forcing grid_T file: "+flx_path+'T.nc'
            assert(os.path.exists(flx_path+'U.nc')),"can't find flux forcing grid_T file: "+flx_path+'U.nc'
            assert(os.path.exists(flx_path+'V.nc')),"can't find flux forcing grid_T file: "+flx_path+'V.nc'
            yy=str(yy).zfill(4)+'.nc'
            os.symlink(flx_path+'T.nc', rP_WORKDIR+'/flxfce/flxforce_grid_T_y'+yy)
            os.symlink(flx_path+'U.nc', rP_WORKDIR+'/flxfce/flxforce_grid_U_y'+yy)
            os.symlink(flx_path+'V.nc', rP_WORKDIR+'/flxfce/flxforce_grid_V_y'+yy)
                    
        #### End of surface flux forcing implementation                   
      


        if rP_nml_patch is not None:
            nmlpath=rP_WORKDIR+'/namelist_ref'
            assert(os.path.exists(nmlpath)),"can't find namelist_ref"
            print(bcolors.HEADER+ "WARNING: "+bcolors.ENDC   +'We are patching the main NEMO namelist '+nmlpath+' with: '+  bcolors.HEADER +str(rP_nml_patch) +bcolors.ENDC + " (this shortly gets copied to be namelist_cfg, which then gets patched by preNEMO.py ...)")
            f90nml.patch(nmlpath, rP_nml_patch, out_path=nmlpath+'_new')
            shutil.move(nmlpath+'_new', nmlpath)


        shutil.copy2(rP_WORKDIR+'/'+'namelist_ref',rP_WORKDIR+'/'+'namelist_cfg')

        print(bcolors.WARNING + "WARNING: Using bathymetry and ice-shelf draft" + bcolors.ENDC+" from: "+BFILE)
        print("WARNING: ")

        os.symlink(BFILE, 'isf_draft_meter.nc')
        os.symlink(BFILE, 'bathy_meter.nc')

        print("WARNING: ")
        print(bcolors.WARNING + "WARNING: Using restoring and non-standard temp init"+ bcolors.ENDC+": "+TSFILE)
        os.symlink(TSFILE, 'TS_init.nc')
        os.symlink(TSRESTOFILE, 'resto.nc')
        print("WARNING: ")



    #file that will be imported by GoGoNEMO.py for all run parameters
    with ctx.closing(open(rP_WORKDIR+'/rPARAMS.py','w')) as handle:
            handle.write(''+'\n')

            handle.write('"""'+'\n')
            handle.write("This is the script that captures all the key run parameters and is imported by GoGoNEMO.py"+"\n")
            handle.write('"""'+'\n')
            handle.write(''+'\n')

            handle.write("rP_OCEANCORES='"  +str(rP_OCEANCORES)+"'"+'\n')
            handle.write("rP_STOCKDIR='"  +str(rP_STOCKDIR)+"'"+'\n')
            handle.write("rP_WORKDIR='"  +str(rP_WORKDIR)+"'"+'\n')
            handle.write("rP_RBUILD_NEMO='"  +str(rP_RBUILD_NEMO)+"'"+'\n')
            handle.write("rP_MKPSI='"  +str(rP_MKPSI)+"'"+'\n')
            handle.write("rP_PROJ='"  +str(rP_PROJ)+"'"+'\n')
            handle.write("rP_CONFIG='"  +str(rP_CONFIG)+"'"+'\n')
            handle.write("rP_CASE='"  +str(rP_CASE)+"'"+'\n')
            handle.write("rP_DESC='"  +str(rP_DESC)+"'"+'\n')
            handle.write("rP_YEAR0='"  +str(rP_YEAR0)+"'"+'\n')
            handle.write("rP_YEAR_MAX='"  +str(rP_YEAR_MAX)+"'"+'\n')
            handle.write("rP_PARTITION='" +str(rP_PARTITION)+"'"+'\n') #LS add when use different partitions

            handle.write(''+'\n')
            handle.write("if __name__ == '__main__':" +"\n")
            handle.write("    print('This script is designed to be imported...')"+"\n")




    with ctx.closing(open(rP_WORKDIR+'/goNEMOquick.sh','w')) as handle:
        handle.write('#!/bin/bash'+'\n')
        handle.write('#SBATCH --job-name=BRIINE'+'\n')
        handle.write('#SBATCH -o ./%x.%j.%N.out           # output file'+'\n')
        handle.write('#SBATCH -e ./%x.%j.%N.err           # errors file'+'\n')
        handle.write('#'+'\n')
        handle.write('#SBATCH -p '+partition+'\n')
        handle.write('#SBATCH --nodes='+str(N_nodes)+'\n')
        handle.write('#SBATCH --ntasks-per-node='+str(core_per_node)+'\n')
        handle.write('#SBATCH --cpus-per-task=1'+'\n')
        handle.write('#SBATCH --time=0-4:00:00           # day-hours:minutes:seconds'+'\n')
        handle.write('#SBATCH --mem-per-cpu=3G'+'\n')
        handle.write('###SBATCH --ntasks='+str(rP_OCEANCORES)+'\n')
        handle.write('#SBATCH --exclusive'+'\n')
        handle.write('#'+'\n')
        handle.write('echo "The job ${SLURM_JOB_ID} is running on these nodes:"'+'\n')
        handle.write('echo ${SLURM_NODELIST}'+'\n')
        handle.write('echo'+'\n')
        handle.write('#'+'\n')
        handle.write('cd $SLURM_SUBMIT_DIR    # go to the work / submission directory'+'\n')
        handle.write('#'+'\n')
        handle.write('#'+'\n')
        handle.write('module purge'+'\n')
        handle.write('module use /applis/PSMN/debian11/E5/modules/all/'+'\n')
        handle.write('module load netCDF-Fortran/4.6.1-gompi-2023a'+'\n')

        handle.write('export PYTHONPATH=/home/lsaddier/miniconda3/pkgs;export PATH=/home/lsaddier/miniconda3/bin:$PATH;source activate root'+'\n')

        handle.write(''+'\n')

        handle.write('#'+'\n')
        handle.write("#This is the script allows you to run NEMO real quick..."+"\n")
        handle.write(''+'\n')

        handle.write('python preNEMO.py'+'\n')
        handle.write('mpirun -np $SLURM_NTASKS ./nemo.exe'+'\n')
        handle.write('python postNEMO.py'+'\n')




    subprocess.call('chmod u+x '+rP_WORKDIR+'/goNEMOquick.sh',shell=True)

    with ctx.closing(open(rP_WORKDIR+'/goNEMOlong.sh','w')) as handle:
        handle.write('#!/bin/bash'+'\n')
        handle.write('#SBATCH --job-name=BRIINE'+'\n')
        handle.write('#SBATCH -o ./%x.%j.%N.out           # output file'+'\n')
        handle.write('#SBATCH -e ./%x.%j.%N.err           # errors file'+'\n')
        handle.write('#'+'\n')
        handle.write('#SBATCH -p '+partition+'\n')
        handle.write('#SBATCH --nodes='+str(N_nodes)+'\n')
        handle.write('#SBATCH --ntasks-per-node='+str(core_per_node)+'\n')
        handle.write('#SBATCH --cpus-per-task=1'+'\n')
        handle.write('#SBATCH --time='+running_time+'           # day-hours:minutes:seconds'+'\n')
        handle.write('#SBATCH --mem-per-cpu=3G'+'\n')
        handle.write('###SBATCH --ntasks='+str(rP_OCEANCORES)+'\n')
        handle.write('#SBATCH --exclusive'+'\n')
        handle.write('#'+'\n')
        handle.write('#SBATCH --mail-type=BEGIN,END,FAIL'+'\n') # please *NEVER* use the 'ALL' flag, as it will overload mail servers
        handle.write('#SBATCH --mail-user=louis.saddier@ens-lyon.fr'+'\n')
        handle.write('echo "The job ${SLURM_JOB_ID} is running on these nodes:"'+'\n')
        handle.write('echo ${SLURM_NODELIST}'+'\n')
        handle.write('echo'+'\n')
        handle.write('#'+'\n')
        handle.write('cd $SLURM_SUBMIT_DIR    # go to the work / submission directory'+'\n')
        handle.write('#'+'\n')
        handle.write('#'+'\n')
        handle.write('module purge'+'\n')
        handle.write('module use /applis/PSMN/debian11/E5/modules/all/'+'\n')
        handle.write('module load netCDF-Fortran/4.6.1-gompi-2023a'+'\n')

        handle.write('export PYTHONPATH=/home/lsaddier/miniconda3/pkgs;export PATH=/home/lsaddier/miniconda3/bin:$PATH;source activate root'+'\n')

        handle.write(''+'\n')

        handle.write('#'+'\n')
        handle.write("#This is the script allows you to run NEMO one job at a time..."+"\n")
        handle.write('echo "Current Date and Time is (start): " '+'`date`'+"\n")
        handle.write(''+'\n')



        handle.write(' '+"\n")
        #bug? cwd was empty on e5 (and archer?!)
        #handle.write('cd $cwd'+"\n")

        handle.write('    pwd'+"\n")
        handle.write('    cd '+rP_WORKDIR+"\n")
        handle.write('    echo "Current directory is:"'+"\n")
        handle.write('    pwd'+"\n")

        handle.write("if [ -f time.year.step ]; then"+"\n")
        handle.write("   source time.year.step"+"\n")
        handle.write('else'+"\n")
        handle.write("   echo 'year=1' > time.year.step"+"\n")
        handle.write("   source time.year.step"+"\n")
        handle.write(' '+"\n")
        handle.write("fi"+"\n")
        handle.write('echo "Running year: "'+"\n")
        handle.write('echo "Running year: "$year" out of '+str(rP_YEAR_MAX)+'"'+"\n")
        handle.write('echo " "'+"\n")
        handle.write("while [ $year -lt "+str(int(rP_YEAR_MAX)+1)+" ]"+"\n")
        #handle.write('for i in {1..'+rP_YEAR_MAX+'}'+"\n")
        #handle.write('for i in {1..'+rP_YEAR_MAX+'}'+"\n")
        handle.write('do'+"\n")

        handle.write('    echo "Current Date and Time is ("$year" start): " '+'`date`'+"\n")
        handle.write('    echo "Run NEMO"'+"\n")

        handle.write('    cd '+rP_WORKDIR+"\n")
        handle.write('    echo "Current directory is:"'+"\n")
        handle.write('    pwd'+"\n")
        handle.write('    python preNEMO.py'+"\n")
        #handle.write('    srun --ntasks='+str(rP_OCEANCORES)+' ./nemo.exe'+'\n')
        handle.write('    mpirun -np $SLURM_NTASKS ./nemo.exe'+'\n')
        handle.write(' '+"\n")

        handle.write('    echo "Clean up NEMO"'+"\n")
        #handle.write('    srun --ntasks='+'1'+' --tasks-per-node='+'1'+' --cpus-per-task=1 python postNEMO.py '+"\n")
        handle.write('    python postNEMO.py'+'\n')

        handle.write('    wait'+"\n")
        handle.write('    echo "Current Date and Time is ("$year" end): " '+'`date`'+"\n")

        handle.write('    '+"\n")

        handle.write('    echo "And repeat."'+"\n")

        handle.write("    year=$[$year+1]"+"\n")
        handle.write('    cd $cwd'+"\n")
        handle.write("    echo 'year='$year > time.year.step"+"\n")
        handle.write('done'+"\n")

        handle.write('echo "Current Date and Time is (end): " '+'`date`'+"\n")
        handle.write('echo "Its over..."'+"\n")

    subprocess.call('chmod u+x '+rP_WORKDIR+'/goNEMOlong.sh',shell=True)


    #so we can run lots at once
    mkdir(workfol+'rfiles/')
    if not os.path.exists(workfol+'rfiles/runme'):
        with ctx.closing(open(workfol+'rfiles/runme','w')) as handle:
            handle.write(str(rP_YEAR_MAX)+''+'\n')

    with ctx.closing(open(workfol+'rfiles/runme','a')) as handle:
        handle.write(rP_WORKDIR+'/ '+'\n')

    return rP_WORKDIR


if __name__ == "__main__":
    #for idx,offset in zip([6,7,8,9],[0.02,0.04,0.06,0.08]):
    workfol='/home/lsaddier/runnemo/'

    CASE='7'
    rP_CASE=CASE.zfill(3)

    rP_CONFIG_TYPE="BRIINE"

    mkillisf=False
    rP_nml_patch={}


    if rP_CONFIG_TYPE=="BRIINE":
        NUM=2
        rP_CONFIG='jpo'+str(NUM).zfill(3)

        WCONFIG='/home/lsaddier/nemo/bld_configs/BRIINE/jpo_2km_20m_SSS340'

        NEMOdir='/home/lsaddier/nemo/models/nemo_4.2.1/'
        NEMOexe='/home/lsaddier/nemo/models/nemo_4.2.1/tests/MY_ISOMIP+_FLX/BLD/bin/nemo.exe'

        BFILE =WCONFIG+'/geom.nc'

        # Do not forget to specify TS profiles !
        TSFILE=WCONFIG+'/TS_init_conv.nc'        # initialization
        TSRESTOFILE=WCONFIG+'/TS_1.nc'   # restoring

        # And surface flux forcing !
        flxfce=WCONFIG+'/flx/'

        #rP_nml_patch=None

        rP_nml_patch['namdom']={'rn_Dt':float(360.0)}
        
        #rP_nml_patch['namdyn_adv']={'ln_dynadv_vec':True,'ln_dynadv_ubs':False} # Centered/Upwind advection schemes
        
        rP_nml_patch['namdyn_ldf']={'rn_Lv':float(1e3),'rn_Uv':float(12*0.01*6.4)} # Bilap. LDF dyn (3rd number e7 m4/s)
        rP_nml_patch['namtra_ldf']={'rn_Ld':float(1e3),'rn_Ud':float(12*0.01*6.4)} # Bilap. LDF tra (3rd number e7 m4/s) 
 
        #rP_nml_patch['namzdf']={'ln_zdfevd':True} # Convection parameterization
      
        rP_nml_patch['namlbc']={'rn_shlat':float(2.)} #Lateral Boundary condition (0 -> free, 2 -> no) 
        
        #rP_nml_patch['namisf']={'rn_htbl':float(30.0),'rn_gammat0':float(0.0215),'rn_gammas0':float(0.614e-3)} # ISF melt parameters

        rP_nml_patch['namsbc_ssr']={'nn_sstr':int(1),'rn_dqdt':float(-40.),'cn_dir':WCONFIG} #SSR

        rP_nml_domcfgpatch={}
        rP_nml_domcfgpatch['namcfg']={'jpiglo':int(64),'jpidta':int(64),'jpjglo':int(64),'jpjdta':int(64)}
        rP_nml_domcfgpatch['namdom']={'pphmax':float(2000.0)}
        customdomcfg=['','']


    elif rP_CONFIG_TYPE=="CONV":
        NUM=1
        rP_CONFIG='conv'+str(NUM).zfill(3)

        WCONFIG='/home/lsaddier/nemo/bld_configs/CONV/conv_1km_24m'

        NEMOdir='/home/lsaddier/nemo/models/nemo_4.2.1/'
        NEMOexe='/home/lsaddier/nemo/models/nemo_4.2.1/tests/MY_ISOMIP+_FLX/BLD/bin/nemo.exe'

        BFILE =WCONFIG+'/geom.nc'

        # Do not forget to specify TS profiles !
        TSFILE=WCONFIG+'/TS_warm.nc'
        TSRESTOFILE=WCONFIG+'/TS_warm.nc'

        # And surface flux forcing !
        flxfce=WCONFIG+'/flx/'

        #rP_nml_patch=None

        rP_nml_patch['namdom']={'rn_Dt':float(360.0)}
    
        rP_nml_patch['namdyn_adv']={'ln_dynadv_vec':False,'ln_dynadv_ubs':True} # Upwind adv
        
        #rP_nml_patch['namdyn_ldf']={'ln_dynldf_lap':False,'ln_dynldf_blp':True,'rn_Lv':float(1e3),'rn_Uv':float(12*0.01)} # Bilap. LDF dyn
        #rP_nml_patch['namtra_ldf']={'ln_traldf_lap':False,'ln_traldf_blp':True,'rn_Ld':float(1e3),'rn_Ud':float(12*0.01),'ln_traldf_msc':True} # Bilap. LDF tra
        
        #rP_nml_patch['namzdf']={'ln_zdfevd':False}
        
        #rP_nml_patch['namlbc']={'rn_shlat':float(0.)} #Lateral Boundary condition (0 -> free, 2 -> no)

        rP_nml_patch['namisf']={'ln_isfcav_mlt':False,'ln_isf':False} # Deactivate ice-shelf module
        rP_nml_patch['namdyn_hpg']={'ln_hpg_isf':False,'ln_hpg_sco':True} # Deactivate s-coord (sco) adapted to isf -> sco

        rP_nml_domcfgpatch={}
        rP_nml_domcfgpatch['namcfg']={'jpiglo':int(64),'jpidta':int(64),'jpjglo':int(64),'jpjdta':int(64)}
        rP_nml_domcfgpatch['namdom']={'pphmax':float(2000.0)}
        customdomcfg=['','']


    elif rP_CONFIG_TYPE=="ISOMIP":
        NUM=5
        rP_CONFIG='iso'+str(NUM).zfill(3)

        WCONFIG='/home/lsaddier/nemo/bld_configs/ISO/iso_oce3'

        NEMOdir='/home/lsaddier/nemo/models/nemo_4.2.1/'
        NEMOexe='/home/lsaddier/nemo/models/nemo_4.2.1/tests/MY_ISOMIP+_FLX/BLD/bin/nemo.exe'

        BFILE =WCONFIG+'/isomip+_NEMO_242_geom_ocean3.nc'

        # Do not forget to specify TS profiles !
        TSFILE=WCONFIG+'/nemo_base_WARM.nc'
        TSRESTOFILE=WCONFIG+'/nemo_base_WARM.nc'

        # And surface flux forcing !
        flxfce=WCONFIG+'/flx_smooth/'

        #rP_nml_patch=None

        rP_nml_patch['namdom']={'rn_Dt':float(360.0)}
       
        #rP_nml_patch['namisf']={'rn_htbl':float(20.0)} # Losch layer thickness
        #rP_nml_patch['namlbc']={'rn_shlat':float(0.)} #Lateral Boundary condition (0 -> free, 2 -> no)
        #rP_nml_patch['namzdf']={'ln_zdfcst':False,'ln_zdfrix':True}
        #rP_nml_patch['namisf']={'rn_gammat0':0.,'rn_gammas0':0.,'rn_vtide':0.,'cn_gammablk':'spe'}
        #rP_nml_patch['namisf']={'rn_gammat0':0.0215,'cn_gammablk':'spe'}
        #rP_nml_patch['namisf']={'rn_gammat0':0.0215 + offset}
        
        rP_nml_domcfgpatch={}
        rP_nml_domcfgpatch['namcfg']={'jpiglo':int(64),'jpidta':int(64),'jpjglo':int(64),'jpjdta':int(64)}
        rP_nml_domcfgpatch['namdom']={'pphmax':float(2000.0)}
        customdomcfg=['','']



    else:
        print(bcolors.FAIL + "We are using config_type: "+rP_CONFIG_TYPE + bcolors.ENDC)
        print(bcolors.FAIL + "E R R O R: I don't know what to do with this config type."+ bcolors.ENDC)
        sys.exit()

    print(bcolors.WARNING + "WARNING: "  +'Hard overwriting'+  bcolors.ENDC + ' of NEMO version')
    
    rP_WORKDIR=main(workfol,rP_CONFIG,rP_CONFIG_TYPE,rP_CASE,NEMOexe,WCONFIG,BFILE,TSFILE,FLXFCE=flxfce,rP_nml_patch=rP_nml_patch,extdomaincfg=customdomcfg)

    #domaincfg='/home/lsaddier/nemo/models/nemo_4.2.1/tools/DOMAINcfg/BLD/bin/make_domain_cfg.exe'
    #mkmesh(workfol,rP_WORKDIR,domaincfg,BFILE,rP_nml_patch=rP_nml_domcfgpatch,killisf=mkillisf,extdomaincfg=customdomcfg)
    #subprocess.call('cd '+rP_WORKDIR+' ; sbatch '+rP_WORKDIR+'/goNEMOquick.sh',shell=True)
    subprocess.call('cd '+rP_WORKDIR+'; sbatch '+rP_WORKDIR+'/goNEMOlong.sh',shell=True)
