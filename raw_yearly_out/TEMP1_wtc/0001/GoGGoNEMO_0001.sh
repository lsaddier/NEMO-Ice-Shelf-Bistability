#!/bin/bash 
cd /scratch/Lake/lsaddier/nemo/run/jpo002_006/
echo "Current directory is:"
pwd
 

echo "Re-combining: mesh_mask"
cp /home/lsaddier/nemo/models/nemo_4.2.1/tools/REBUILD_NEMO/BLD/bin/rebuild_nemo.exe rebuild_nemo
mpirun -np 1 rebuild_nemo nam_rebuild

if [ -f mesh_mask.nc ]; then
   echo "File: mesh_mask.nc reassembled ok"
   rm mesh_mask_*.nc
else
   echo "!@#$% PROBLEM WITH RE-ASSEMBLY OF FILE mesh_mask"
   echo ">>>>>>>>>> STOP !"
   exit 1
fi
if [ -f output.init_0000.nc ]; then
   
   echo "Re-combining: output.init"
   mpirun -np 1 rebuild_nemo output.init 24
   
   if [ -f output.init.nc ]; then
      echo "File: output.init.nc reassembled ok"
      rm output.init_*.nc
   else
      echo "!@#$% PROBLEM WITH RE-ASSEMBLY OF FILE output.init"
      echo ">>>>>>>>>> STOP !"
      exit 1
   fi
else
   echo "no output.init"
fi


echo "Re-combining: jpo002_006_00086400_restart.nc"
mkdir tempo 
mv nam_rebuild_restart tempo/nam_rebuild
mv jpo002_006_00086400_restart_????.nc tempo/
cp rebuild_nemo* tempo/
cd tempo 
mpirun -np 1 rebuild_nemo nam_rebuild
if [ -f jpo002_006_00086400_restart.nc ]; then
   echo "File: jpo002_006_00086400_restart.nc reassembled ok"
   mv jpo002_006_00086400_restart.nc ..
   rm jpo002_006_00086400_restart_????.nc
else
   echo "!@#$% PROBLEM WITH RE-ASSEMBLY OF FILE jpo002_006_00086400_restart.nc"
   echo ">>>>>>>>>> STOP !"
   exit 1
fi
cd ..
rm -r tempo/
