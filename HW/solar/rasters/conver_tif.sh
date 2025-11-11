cd ./skyfactor
mkdir -p ../svf_tifs

for f in *.sgrd; do
  base=$(basename "$f" .sgrd)
  echo "Convirtiendo $f → ../svf_tifs/${base}.tif"
  saga_cmd io_gdal 1 -GRIDS "$f" -FILE "../svf_tifs/${base}.tif"
done
