# Alternative Internet Contributing Guide

## As contributor

The current index reads its projects from the JSON files in `projects/`.

To add a new project, make a pull request with a JSON file according to this template:

```json
  {
    "name": "Project name",
    "description": "A description, in markdown format"
  }
```

The script used to generate the index, sources project statistics from Ohloh.net. It is possible that the metadata is incorrect due to Ohloh's search engine returning the wrong project. You can skip the Ohloh metadata for such a project, using the
following JSON structure:

```json
  {
    "name": "Project name",
    "description": "A description, in markdown format",
    "ohloh": {
      "skip": true
    }
  }
```

Alternatively, you can manually look up the project on Ohloh and get the correct Ohloh identifier for this project. You can tell the script to use that identifier with the following JSON structure:

```json
  {
    "name": "Project name",
    "description": "A description, in markdown format",
    "ohloh": {
      "id": "1234567"
    }
  }
```

## As maintainer

After a pull request is accepted, the `update.py` script should be run to update the index. 

This script reads a bunch of JSON files, finds appropriate metadata on Ohloh and writes everything neatly to a table.

To process the JSON files in a given directory and find metadata on Ohloh, use:

`python update.py -a [your-ohloh-api-key] -d [the-directory-to-store-in]`

To use the default directory ("projects"), simply omit the -d parameter:

`python update.py -a [your-ohloh-api-key]`

If you don't want to get information from Ohloh and just generate the table, omit the -a parameter:

`python update.py`

After this, the updates index should be committed to the repository.