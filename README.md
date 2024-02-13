# Misc Fetcher

Uses the internal (public?) API of PIMD (Party in my Dorm) app/game to fetch showcases of any person.

Note: the TechTree SQLite DB may need to be updated from time to time.

## Installation

Clone the repo with git

```bash
 git clone URL
```

You'll need a `tokens.json` file in the same directory filled with the `refresh_token` and `access_token` (can be empty, will be re-requested) in the following format

`tokens.json`

```json
{
    "refresh_token": "refresh_token here",
    "access_token": "access_token here"
}
```

and run

```bash
python misc_fetcher.py <username>
```

```bash
python misc_fetcher.py -h

Gets and calculated misc of given username

positional arguments:
  username

optional arguments:
  -h, --help   show this help message and exit
  -H, --human  shows data in human readable numbers

APIs for the win
```

## Updating TechTree SQLite DB

To update the DB, download the latest APK from a source e.g. [APKPure](https://apkpure.com) and decomplile with APK Tool.

The SQLite file will be under `assets/databases/TechTree.sqlite`

## Subject to break

No guarantee is provided that it will continue to work in the future or that its unbannable. You may get banned.

## License

This project is [MIT licensed](LICENSE).
