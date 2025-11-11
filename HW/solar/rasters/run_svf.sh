#!/bin/bash
input_dir="./tiles"
output_dir="./skyfactor"
mkdir -p "$output_dir"

for f in "$input_dir"/*.tif; do
  base=$(basename "$f" .tif)
  echo "Procesando $base..."
  saga_cmd ta_lighting 3 \
    -DEM "$f" \
    -RADIUS 10000 -NDIRS 8 -METHOD 1 -DLEVEL 3 \
    -SVF "$output_dir/${base}_svf.sdat"
done
