#!/usr/bin/python3
import datetime
import os
import subprocess
import sys

def main():
    LUBELOGGER_NAMESPACE = os.getenv('LUBELOGGER_NAMESPACE')
    LUBELOGGER_POD = os.getenv('LUBELOGGER_POD')
    LUBELOGGER_POSTGRES_POD = os.getenv('LUBELOGGER_POSTGRES_POD')
    LUBELOGGER_DATA_DIRS = ['/App/config', '/App/data', '/App/wwwroot/images', '/root/.aspnet/DataProtection-Keys']
    B2_APPLICATION_KEY_ID = os.getenv('B2_APPLICATION_KEY_ID')
    B2_APPLICATION_KEY = os.getenv('B2_APPLICATION_KEY')
    B2_BUCKET = os.getenv('B2_BUCKET')
    BACKUP_DEST = os.getenv('BACKUP_DEST', '/opt/b2-bucket-backup')

    # TODO backup postgres database
    # run pg_dump in cnpg container to /var/lib/postgresql/data/backups/filename.tgz
    archive_name = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    pgdump_file_name = '/var/lib/postgresql/data/backups/{}.dump'.format(archive_name)
    print('Dumping lubelogger postgres database in {} pod in {} namespace'.format(LUBELOGGER_POSTGRES_POD, LUBELOGGER_NAMESPACE))
    cmd = ['kubectl', '-n', LUBELOGGER_NAMESPACE, 'exec', LUBELOGGER_POSTGRES_POD, '--', '/usr/bin/pg_dump', '-Fc', '-d', 'lubelogger', '-f', pgdump_file_name]
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print('ERROR: failed to dump lubelogger postgres database')
        sys.exit(1)
    print('Created archive {}'.format(pgdump_file_name))

    print('Collecting lubelogger attachments in {} pod in {} namespace'.format(LUBELOGGER_POD, LUBELOGGER_NAMESPACE))
    archive_name_file_name = '/tmp/{}.tar.gz'.format(archive_name)
    cmd = ['kubectl', '-n', LUBELOGGER_NAMESPACE, 'exec', LUBELOGGER_POD, '--', '/usr/bin/tar', '-czf', archive_name_file_name, LUBELOGGER_DATA_DIRS]
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print('ERROR: failed to tar lubelogger data dirs')
        sys.exit(1)
    print('Created archive {}'.format(archive_name_file_name))

    print('Copying archives to tmp location')
    # copy lubelogger data archive
    cp_src = '{}:{}'.format(LUBELOGGER_POD, archive_name_file_name)
    cp_dst = '{}/{}'.format(BACKUP_DEST, archive_name_file_name.split('/')[-1])
    cmd = ['kubectl', '-n', LUBELOGGER_NAMESPACE, 'cp', cp_src, cp_dst]
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print('ERROR: failed to copy {} to {}'.format(cp_src, cp_dst))
        sys.exit(1)
    pg_cp_src = '{}:{}'.format(LUBELOGGER_POSTGRES_POD, pgdump_file_name)
    pg_cp_dst = '{}/{}'.format(BACKUP_DEST, pgdump_file_name.split('/')[-1])
    # copy postgres dump
    cmd = ['kubectl', '-n', LUBELOGGER_NAMESPACE, 'cp', pg_cp_src, pg_cp_dst]
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print('ERROR: failed to copy {} to {}'.format(pg_cp_src, pg_cp_dst))
        sys.exit(1)
    print('Archives copied')
    # clean up lubelogger data archive
    cmd = ['kubectl', '-n', LUBELOGGER_NAMESPACE, 'exec', LUBELOGGER_POD, '--', 'rm', '-f', archive_name_file_name]
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print('ERROR: failed cleanup on archive file {}'.format(archive_name_file_name))
        sys.exit(1)
    # cleanup postgres dump
    cmd = ['kubectl', '-n', LUBELOGGER_NAMESPACE, 'exec', LUBELOGGER_POSTGRES_POD, '--', 'rm', '-f', pgdump_file_name]
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print('ERROR: failed cleanup on archive file {}'.format(pgdump_file_name))
        sys.exit(1)
    print('Archive files cleaned')

    print('Creating lubelogger backup bundle')
    bundle_file_name = '{}/{}-bundle.tar'.format(BACKUP_DEST, archive_name)
    cmd = ['/bin/tar', '-cf', bundle_file_name, cp_dst, pg_cp_dst]
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print('ERROR: failed to create bundle {}'.format(bundle_file_name))
        sys.exit(1)
    print('Created bundle {}'.format(bundle_file_name))

    print('Uploading to b2')
    cmd = ['b2', 'account', 'get']
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print("ERROR: could not get b2 account using provided credentials. Check env vars")
        sys.exit(1)
    cmd = ['b2', 'file', 'upload', B2_BUCKET, bundle_file_name, bundle_file_name.split('/')[-1], '--no-progress']
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print("ERROR: failed to upload file to b2")
        sys.exit(1)
    print('Finished')

if __name__ == '__main__':
    main()
