"""
Forja Viral — Admin Tool (CLI)

Use to manage licenses on your running license_server.

Requires:
- requests

Examples:

Create license (30 days):
python admin_tool.py create --base-url http://127.0.0.1:8787 --admin-token SUA_SENHA --license-key FV-001 --days 30 --plan monthly

Extend license:
python admin_tool.py extend --base-url http://127.0.0.1:8787 --admin-token SUA_SENHA --license-key FV-001 --days 30

Ban:
python admin_tool.py ban --base-url http://127.0.0.1:8787 --admin-token SUA_SENHA --license-key FV-001

Unban:
python admin_tool.py unban --base-url http://127.0.0.1:8787 --admin-token SUA_SENHA --license-key FV-001
"""

import argparse
import requests
import time
import sys


def post(url, data, admin_token):
    headers = {"x-admin-token": admin_token}
    r = requests.post(url, json=data, headers=headers, timeout=10)
    try:
        return r.json()
    except Exception:
        print("Invalid response:", r.text)
        sys.exit(1)


def create(args):
    exp = int(time.time()) + (args.days * 86400)
    data = {
        "license_key": args.license_key,
        "exp": exp,
        "plan": args.plan,
    }
    resp = post(f"{args.base_url}/admin/create_license", data, args.admin_token)
    print(resp)


def extend(args):
    exp = int(time.time()) + (args.days * 86400)
    data = {
        "license_key": args.license_key,
        "exp": exp,
    }
    resp = post(f"{args.base_url}/admin/extend_license", data, args.admin_token)
    print(resp)


def ban(args):
    data = {
        "license_key": args.license_key,
        "banned": True,
    }
    resp = post(f"{args.base_url}/admin/ban_license", data, args.admin_token)
    print(resp)


def unban(args):
    data = {
        "license_key": args.license_key,
        "banned": False,
    }
    resp = post(f"{args.base_url}/admin/ban_license", data, args.admin_token)
    print(resp)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--base-url", required=True)
    common.add_argument("--admin-token", required=True)
    common.add_argument("--license-key", required=True)

    p_create = sub.add_parser("create", parents=[common])
    p_create.add_argument("--days", type=int, required=True)
    p_create.add_argument("--plan", default="monthly")

    p_extend = sub.add_parser("extend", parents=[common])
    p_extend.add_argument("--days", type=int, required=True)

    p_ban = sub.add_parser("ban", parents=[common])
    p_unban = sub.add_parser("unban", parents=[common])

    args = parser.parse_args()

    if args.command == "create":
        create(args)
    elif args.command == "extend":
        extend(args)
    elif args.command == "ban":
        ban(args)
    elif args.command == "unban":
        unban(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
