grep -r --include='*.py' 'ty:ignore' pylustrator/ | wc -l
grep -r --include='*.py' -o 'ty:ignore\[[^]]*\]' pylustrator/ | sort | uniq -c | sort -rn
grep -r --include='*.py' -o 'ty:ignore' pylustrator/ | sort | uniq -c | sort -rn