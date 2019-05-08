while read p; do
  echo "$p"
  python test.py "$p"
done <model_runs.txt