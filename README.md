**AudiobookShelf Batch Processor**

This script processes a batch of audiobooks from an AudiobookShelf (ABS) instance and performs arbitrary tasks. It also assumes your files are named the way I like it. You probably want to read, understand and customize this script for your own needs.

**Usage**

To run this script, simply execute `python abs-process.py` from your terminal or command prompt. You can also specify a limit for the number of items to retrieve using the `--limit` option:

```
python abs-process.py --limit 100
```

**Requirements**

* Python 3.x
* `requests` library (installed by default with Python)
* AudiobookShelf API key and instance URL (configure in `abs.ini` file, remember to add /api to your url)

**Configuration**

The script reads its configuration from an `abs.ini` file, which should contain the following settings:

* `BASE_URL`: The URL of your AudiobookShelf instance.
* `API_KEY`: Your AudiobookShelf API key.
* `LIBRARY`: The name of the library to process.

Use `cp abs.ini.sample abs.ini` to create one.
