#!/bin/bash
# Script lybniz-i18n was written by Alexey Loginov for lybniz internationalisation
# License: GPLv3+
# https://www.transifex.com/Magic/lybniz/

echo "Starting script lybniz-i18n.sh"

A=`which xgettext`
if [ "$A" = "" ]
then
  echo "Error: missing xgettext"
  exit 1
fi

echo "Creating POT file"
xgettext --language=Python --keyword=_ --keyword=N_ --output=lybniz.pot ../lybniz.py
xgettext --language=Desktop --output=lybniz.pot ../lybniz.desktop --from-code=utf-8 -j
echo "Done for creating POT file."

echo "Merge translations"
for a in *.po; do
  msgmerge -U $a lybniz.pot
done
rm -f *.po~
echo "Done for merge translations."

echo "Compiling translations"
rm -rf ../locale
for lang in `ls|grep -v \.pot|grep -v lybniz-i18n|cut -d "." --fields=1`
do
  echo "     Compiling $lang"
  mkdir -p ../locale/$lang/LC_MESSAGES
  msgfmt $lang.po -o $lang.mo
  mv -f $lang.mo ../locale/$lang/LC_MESSAGES/lybniz.mo
  echo "     Done for $lang"
done
echo "Done for compiling translations."

echo "Script lybniz-i18n.sh was finished."
