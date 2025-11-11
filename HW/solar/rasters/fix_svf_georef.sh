#!/bin/bash
# --- Reconstruir georreferencia de los SVF tiles desde el DEM original ---
# Mario Ponce – NYU Urban Systems / Nov 2025

DEM="./dem_sdiego.tif"     # ruta al DEM completo con georreferencia
SVF_DIR="./svf_fixed"                 # donde están los _svf.tif
EPSG=3857                   # proyección del DEM
TILE_SIZE=5000              # píxeles por tile (ajusta si usaste otro valor)
OVERLAP=100                  # overlap usado en gdal_retile
STEP=$(echo "$TILE_SIZE - $OVERLAP" | bc)   # desplazamiento real entre tiles

ULX=$(gdalinfo "$DEM" | grep "Origin" | cut -d '(' -f2 | cut -d ',' -f1)
ULY=$(gdalinfo "$DEM" | grep "Origin" | cut -d ',' -f2 | cut -d ')' -f1)
PIXW=$(gdalinfo "$DEM" | grep "Pixel Size" | cut -d '(' -f2 | cut -d ',' -f1)
PIXH=$(gdalinfo "$DEM" | grep "Pixel Size" | cut -d ',' -f2 | cut -d ')' -f1)

echo "DEM UL=($ULX,$ULY)"
echo "PixelSizeX=$PIXW  STEP=$STEP"

# 2. Aplicar a cada SVF tile
for f in ${SVF_DIR}/dem_sdiego_*_svf.tif; do
  name=$(basename "$f" .tif)
  col=$(echo "$name" | cut -d'_' -f3)
  row=$(echo "$name" | cut -d'_' -f4)

  # ⚠️  En tu caso, el primer número (_01_) debe controlar X (Este-Oeste),
  # y el segundo (_02_) debe controlar Y (Norte-Sur)
  # Por eso hacemos:
  i=$((10#$row - 1))  # ahora el segundo índice (Y) va a X
  j=$((10#$col - 1))  # el primero índice (X) va a Y

  if [[ $i -lt 0 || $j -lt 0 ]]; then
    echo "⚠️  Índices raros para $f (col=$col,row=$row)"
    continue
  fi

  # # Ojo: PIXH es negativo (-1), así que esto ya baja en Y
  # xmin=$(echo "$ULX + ($i * $TILE_SIZE * $PIXW)" | bc -l)
  # ymax=$(echo "$ULY + ($j * $TILE_SIZE * $PIXH)" | bc -l)
  # xmax=$(echo "$xmin + ($TILE_SIZE * $PIXW)" | bc -l)
  # ymin=$(echo "$ymax + ($TILE_SIZE * $PIXH)" | bc -l)

  # xmin=$(echo "$ULX + ($i * $TILE_SIZE * $PIXW)" | bc -l)
  # ymin=$(echo "$ULY - ($j * $TILE_SIZE * $PIXW)" | bc -l)  # cambio de signo aquí
  # xmax=$(echo "$xmin + ($TILE_SIZE * $PIXW)" | bc -l)
  # ymax=$(echo "$ymin - ($TILE_SIZE * $PIXW)" | bc -l)      # y aquí
  # echo "📍 $name : UL=($xmin,$ymax)  LR=($xmax,$ymin)"

  # desplazamiento usando STEP (no TILE_SIZE)
  xmin=$(echo "$ULX + ($i * $STEP * $PIXW)" | bc -l)
  ymax=$(echo "$ULY - ($j * $STEP * $PIXW)" | bc -l)

  # tamaño del tile sigue siendo TILE_SIZE px
  xmax=$(echo "$xmin + ($TILE_SIZE * $PIXW)" | bc -l)
  ymin=$(echo "$ymax - ($TILE_SIZE * $PIXW)" | bc -l)
  
  gdal_edit.py -a_srs EPSG:$EPSG -a_ullr $xmin $ymax $xmax $ymin "$f"

  base=$(basename "$f")
  tmpfile="${SVF_DIR}/tmp_${base}"
  gdalwarp -tr 1 -1 -r near -overwrite "$f" "$tmpfile" -co COMPRESS=LZW
  mv "$tmpfile" "$f"
done