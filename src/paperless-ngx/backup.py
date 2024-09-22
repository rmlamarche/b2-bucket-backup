#!/usr/bin/python3
import datetime
import os
import requests
import subprocess

def main():
    PAPERLESS_NGX_NAMESPACE = os.getenv('PAPERLESS_NGX_NAMESPACE')
    PAPERLESS_NGX_POD = os.getenv('PAPERLESS_NGX_POD')
    B2_APPLICATION_KEY_ID = os.getenv('B2_APPLICATION_KEY_ID')
    B2_APPLICATION_KEY = os.getenv('B2_APPLICATION_KEY')
    B2_BUCKET = os.getenv('B2_BUCKET')
    BACKUP_DEST = os.getenv('BACKUP_DEST', '/opt/b2-bucket-backup')
    PAPERLESS_NGX_PASSPHRASE = os.getenv('PAPERLESS_NGX_PASSPHRASE', None)

    print('Running paperless-ngx document_exporter in {} pod in {} namespace'.format(PAPERLESS_NGX_POD, PAPERLESS_NGX_NAMESPACE))
    zip_name = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    zip_file_name = '{}.zip'.format(zip_name)
    cmd = ['kubectl', '-n', PAPERLESS_NGX_NAMESPACE, 'exec', PAPERLESS_NGX_POD, '--', 'document_exporter', '../export', '--zip', '--zip-name', zip_name]
    if PAPERLESS_NGX_PASSPHRASE is not None:
        cmd.append('--passphrase', PAPERLESS_NGX_PASSPHRASE)
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print('ERROR: failed to run paperless-ngx document_exporter')
    print('Created archive {}'.format(zip_file_name))

    print('Copying archive to tmp location')
    cp_src = '{}:../export/{}'.format(PAPERLESS_NGX_POD, zip_file_name)
    cp_dst = '{}/{}'.format(BACKUP_DEST, zip_file_name)
    cmd = ['kubectl', '-n', PAPERLESS_NGX_NAMESPACE, 'cp', cp_src, cp_dst]
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print('ERROR: failed to copy {} to {}'.format(cp_src, cp_dst))
    print('Archive copied')
    cmd = ['kubectl', '-n', PAPERLESS_NGX_NAMESPACE, 'exec', PAPERLESS_NGX_POD, '--', 'rm', '-f', cp_src]
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print('ERROR: failed cleanup on exported zip file {}'.format(zip_file_name))
    print('Export zip file cleaned')

    print('Uploading to b2')
    cmd = ['b2', 'account', 'get']
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print("ERROR: could not get b2 account using provided credentials. Check env vars")
    cmd = ['b2', 'file', 'upload', B2_BUCKET, cp_dst, zip_file_name, '--no-progress']
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print("ERROR: failed to upload file to b2")
    print('Finished')

if __name__ == '__main__':
    main()
