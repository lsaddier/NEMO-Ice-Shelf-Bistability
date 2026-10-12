
echo "Re-combining: jpo002_006_01123200_restart.nc"
mkdir tempo 
mv nam_rebuild_restart tempo/nam_rebuild
mv jpo002_006_01123200_restart_????.nc tempo/
cp rebuild_nemo* tempo/
cd tempo 
mpirun -np 1 rebuild_nemo nam_rebuild
if [ -f jpo002_006_01123200_restart.nc ]; then
   echo "File: jpo002_006_01123200_restart.nc reassembled ok"
   mv jpo002_006_01123200_restart.nc ..
   rm jpo002_006_01123200_restart_????.nc
else
   echo "!@#$% PROBLEM WITH RE-ASSEMBLY OF FILE jpo002_006_01123200_restart.nc"
   echo ">>>>>>>>>> STOP !"
   exit 1
fi
cd ..
rm -r tempo/
