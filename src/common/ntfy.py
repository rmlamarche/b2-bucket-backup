#!/usr/bin/python3
import os
import requests
import argparse

def send_ntfy(url, message, title, priority, tags):
    ntfy_headers = {}
    if title is not None:
        ntfy_headers['Title'] = title
    if priority is not None:
        ntfy_headers['Priority'] = str(priority)
    if tags is not None:
        ntfy_headers['Tags'] = tags

    r = requests.post(url, headers=ntfy_headers, data=message)
    print(r.json())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', type=str, required=True, help='URL with topic (e.g. https://ntfy.sh/my-alerts)')
    parser.add_argument('-m', '--message', type=str, help='notification body text')
    parser.add_argument('-T', '--title', type=str, help='notification title')
    parser.add_argument('-p', '--priority', type=int, choices=[1, 2, 3, 4, 5], help='notification priority')
    parser.add_argument('-t', '--tags', type=str, help='comma separated list of tags')

    args = parser.parse_args()

    send_ntfy(args.url, args.message, args.title, args.priority, args.tags)


if __name__ == '__main__':
    main()