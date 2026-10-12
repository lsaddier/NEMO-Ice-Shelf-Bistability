
echo "Re-combining: jpo001_010_10195200_restart.nc"
mkdir tempo 
mv nam_rebuild_restart tempo/nam_rebuild
mv jpo001_010_10195200_restart_????.nc tempo/
cp rebuild_nemo* tempo/
cd tempo 
mpirun -np 1 rebuild_nemo nam_rebuild
if [ -f jpo001_010_10195200_restart.nc ]; then
   echo "File: jpo001_010_10195200_restart.nc reassembled ok"
   mv jpo001_010_10195200_restart.nc ..
   rm jpo001_010_10195200_restart_????.nc
else
   echo "!@#$% PROBLEM WITH RE-ASSEMBLY OF FILE jpo001_010_10195200_restart.nc"
   echo ">>>>>>>>>> STOP !"
   exit 1
fi
cd ..
rm -r tempo/
