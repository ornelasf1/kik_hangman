#!/bin/bash

timestamp() {
	date +"%Y-%m-%d_%H-%M-%S"
}

APPDIR="/var/www/FlaskApp/FlaskApp/"

status=$(systemctl is-active FlaskApp.service)
if [[ $status != "active"  ]] ; then
	systemctl restart FlaskApp.service
	echo "$(timestamp) Flask App was not active!" >> "${APPDIR}status.output"
fi
mysqlstatus=$(systemctl is-active mysql.service)
if [[ $mysqlstatus != "active" ]] ; then
	systemctl restart mysql.service
	echo "$(timestamp) Mysql.service was not active!" >> "${APPDIR}status.output"
fi
