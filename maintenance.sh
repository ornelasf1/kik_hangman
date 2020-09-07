#!/bin/bash
log="hangmanlog.log"
logdir="log_bks/"
nextnum=0
APPDIR="/var/www/FlaskApp/FlaskApp/"
logdirsize=$(du -sb $APPDIR$log | cut -f1)
LG='\033[1;32m'
NC='\033[0m'

timestamp() {
	date +"%Y-%m-%d_%H-%M-%S"
}

if [[ -e $APPDIR$log ]] ; then
	for f in $APPDIR$logdir*; do
		file=${f##*/}
		nums=${file#"hangmanlog.log.bk"}
		lastchar=${file:$((${#file}-1)):1}
		re='^[0-9]+$'
		if [[ $nums =~ $re ]] && (( $nums > $nextnum )); then
			nextnum=$nums
		fi
	done

	nextnum=$((nextnum+1))
	echo -e "$(timestamp) Copying ${LG}"$APPDIR$log " ${NC}to ${LG}" $APPDIR$logdir$log".bk${nextnum}${NC}" >> "${APPDIR}status.output"
	echo -e "$(timestamp) Clean ${LG}$APPDIR$log${NC}." >> "${APPDIR}status.output"
	cp $APPDIR$log $APPDIR$logdir$log".bk$nextnum" && truncate -s 0 $APPDIR$log
fi

if [[ $logdirsize > 1000000000 ]] ; then
	#echo -e "${logdir} exceeded 1G. Zipping into"	
fi


#Restart service
echo -e "Stopping service..."
echo "$(timestamp) Stopping service..." >> "${APPDIR}status.output"
systemctl stop FlaskApp.service
echo -e "Restarting MYSQL..."
echo "$(timestamp) Restarting MYSQL" >> "${APPDIR}status.output"
systemctl restart mysql.service
echo -e "Starting Flask service..."
echo "$(timestamp) Starting Flask Service..." >> "${APPDIR}status.output"
systemctl start FlaskApp.service
echo -e "Done"
echo "$(timestamp) Done" >> "${APPDIR}status.output"

