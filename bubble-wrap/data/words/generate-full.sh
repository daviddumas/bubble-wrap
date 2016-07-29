for depth in 2 3 4 5 6; do
  echo DEPTH=$depth
  ./g2-commgen-words.sh $depth | magma -b | ./filter.py > g2-commgen-words-depth$depth.txt
done
