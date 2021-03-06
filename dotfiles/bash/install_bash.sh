#!/bin/sh --login

datestr=`date +"%Y%m%d"`

machine=$1

files="
bash_profile
bash_aliases
bash_functions
"
for file in $files; do
  [[ -f $HOME/.$file ]] && mv $HOME/.$file $HOME/.$file-$datestr
  cp $file $HOME/.$file
done

[[ -f $HOME/.bash_site ]] && mv $HOME/.bash_site $HOME/.bash_site-$datestr
cp machines/$machine $HOME/.bash_site

# Grab git prompt for bash
git clone https://github.com/magicmonty/bash-git-prompt $HOME/.bash-git-prompt

exit 0
