#!/usr/bin/python3
import os
import requests
import subprocess

def main():
    API_TOKEN = os.getenv('MEALIE_API_TOKEN')
    BASE_URL = os.getenv('MEALIE_BASE_URL')
    B2_APPLICATION_KEY_ID = os.getenv('B2_APPLICATION_KEY_ID')
    B2_APPLICATION_KEY = os.getenv('B2_APPLICATION_KEY')
    B2_BUCKET = os.getenv('B2_BUCKET')
    BACKUP_DEST = os.getenv('BACKUP_DEST', '/opt/b2-bucket-backup')

    auth_headers = {
        "Authorization": "Bearer {}".format(API_TOKEN)
    }

    r = requests.get("{}{}".format(BASE_URL, "/api/admin/backups"), headers=auth_headers)
    print(r.json())

    r = requests.post("{}{}".format(BASE_URL, "/api/admin/backups"), headers=auth_headers)
    print(r.json())

    r = requests.get("{}{}".format(BASE_URL, "/api/admin/backups"), headers=auth_headers)
    backup_to_download = r.json()['imports'][0]['name']

    print('Downloading backup: {}'.format(backup_to_download))
    r = requests.get("{}{}".format(BASE_URL, "/api/admin/backups/{}".format(backup_to_download)), headers=auth_headers)
    fileToken = r.json()['fileToken']
    tmp_file_path = '{}/{}.zip'.format(BACKUP_DEST, backup_to_download)
    with requests.get("{}{}".format(BASE_URL, "/api/utils/download?token={}".format(fileToken)), headers=auth_headers, stream=True) as r:
        r.raise_for_status()
        with open(tmp_file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    
    print('Wrote backup to tmp file, uploading to b2')
    cmd = ['b2', 'account', 'get']
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print("ERROR: could not get b2 account using provided credentials. Check env vars")
    cmd = ['b2', 'file', 'upload', B2_BUCKET, tmp_file_path, backup_to_download, '--no-progress']
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print("ERROR: failed to upload file to b2")
    
    print("deleting backup from mealie")
    r = requests.delete("{}{}".format(BASE_URL, "/api/admin/backups/{}".format(backup_to_download)), headers=auth_headers)

if __name__ == '__main__':
    main()
