#!/bin/bash

set -Eeo pipefail

if [ -z "${B2_APPLICATION_KEY}" ] || [ -z "${B2_APPLICATION_KEY_ID}" ]; then
	echo "ERROR: missing b2 account credentials, please set B2_APPLICATION_KEY and B2_APPLICATION_KEY_ID"
	exit 1
fi

if [ -z "${B2_BUCKET}" ]; then
	echo "ERROR: B2_BUCKET is required"
	exit 1
fi

if [ -z "${BACKUP_SOURCE}" ]; then
	BACKUP_SOURCE=/data
fi

if [ -z "${SQLITE_DB_FILE}" ]; then
	SQLITE_DB_FILE=db.sqlite3
fi

if [ -z "${CLEAN_DAYS}" ]; then
	CLEAN_DAYS=30
fi

BACKUP_LOCATION=/opt/b2-bucket-backup
TMPDIR=$BACKUP_LOCATION/tmp
DATE_DIR=$(date -Iminutes)
BACKUP_DEST="${BACKUP_LOCATION}/${DATE_DIR}"

echo "### Begin backup $DATE_DIR"
echo "using backup source $BACKUP_SOURCE"
echo "keeping $CLEAN_DAYS days of backups in $BACKUP_LOCATION (if disk is persisted)"
b2 account get
mkdir -p $BACKUP_LOCATION
rm -rf $TMPDIR
mkdir -p $TMPDIR

# remove backups older than CLEAN_DAYS days
echo "removing backups older than $CLEAN_DAYS days"
if [ $(ls $BACKUP_LOCATION | wc -l) -gt 0 ]; then
  find $BACKUP_LOCATION/* -maxdepth 0 -type d -mtime +$CLEAN_DAYS | xargs rm -rf
fi

# create new backup
echo "making backup $BACKUP_DEST"
rm -rf $BACKUP_DEST
mkdir -p $BACKUP_DEST
echo "backing up sqlite db"
sqlite3 $BACKUP_SOURCE/$SQLITE_DB_FILE ".backup '$BACKUP_DEST/$SQLITE_DB_FILE"
for OTHER_FOLDER in "${ADDITIONAL_FOLDERS}"; do
	echo "backing up additional folder $OTHER_FOLDER"
	[[ -d $BACKUP_SOURCE/$OTHER_FOLDER ]] && cp -a $BACKUP_SOURCE/$OTHER_FOLDER $BACKUP_DEST/
done

# backup to remote
echo "creating temp archive in $TMPDIR/b2-bucket-backup-$DATE_DIR.tar.gz"
tar -czf $TMPDIR/b2-bucket-backup-$DATE_DIR.tar.gz -C $BACKUP_LOCATION $DATE_DIR
echo "pushing to b2"
b2 file upload $B2_BUCKET $TMPDIR/b2-bucket-backup-$DATE_DIR.tar.gz b2-bucket-backup-$DATE_DIR.tar.gz --no-progress
echo "removing temp archive"
rm -f $TMPDIR/b2-bucket-backup-$DATE_DIR.tar.gz

echo "### Done backup $DATE_DIR"
