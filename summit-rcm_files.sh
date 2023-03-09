#!/bin/sh

typ=${1}
action=${2}
source=${3}
target=${4}
tmpFile="/tmp/tmp.zip"
exit_on_error() {
	echo ${1}
	rm -f ${tmpFile}
	exit 1
}

do_zip(){

	#Encrypt the zip file and preserver symlinks
	cd ${source} && /usr/bin/zip --symlinks --password ${passwd} -9 -qqr ${target} * || exit_on_error "Failed to zip files in ${source}"
}

do_unzip_config(){

	#zip test: return error if file is not encrypted, or the password is not correct
	cd ${target} && unzip -P 1234 -qqt ${source} && exit_on_error "File is not encrypted"
	cd ${target} && unzip -P ${passwd} -qqt ${source} || exit_on_error "Failed to unzip due to wrong password"
	cd ${target} && rm -fr NetworkManager/ summit-rcm/ && /usr/bin/unzip -P ${passwd} -qqo ${source} || exit_on_error "Failed to unzip(decrypt) files to ${target}"
}

do_unzip_timezone(){

	cd ${target} && /usr/bin/unzip -u -qqo ${source} || exit_on_error "Failed to unzip files to ${target}"
}

do_openssl_encryption(){
	/usr/bin/zip -9 -qqr ${tmpFile} ${source} || exit_on_error "Failed to zip debug data"
	openssl smime -encrypt -aes256 -in ${tmpFile} -binary -outform DER -out ${target} ${cert} || exit_on_error "Failed to encrypt debug data"
	rm -f ${tmpFile}
}

if [ -f /bin/keyctl  ]; then
	/bin/keyctl link @us @s
fi

case ${typ} in
	debug)
		cert=${5}
		do_openssl_encryption
		;;

	config)
		passwd=${5}
		if [ ${action} = "zip" ]; then
			do_zip
		else
			do_unzip_config
		fi
		;;

	timezone)
		do_unzip_timezone
		;;

	log)
		passwd=${5}
		do_zip
		;;
esac
