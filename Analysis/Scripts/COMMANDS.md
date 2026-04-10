### fix h spc
python3 fix_h_spc.py -j 30

#se criou .bak faça:
rm *.bak

### Iterate over a folder to create the index
VALOR="1.00"   # mude para 0.00 quando quiser desativar
ls *.mol2 | awk -v v="$VALOR" '{printf "%d %s     %s\n", NR+2186, $0, v}' > DB_FRAG.list

### BUILD
build -Automatic build.input
 
parallel -j 30 < run_HsDHODH.list
