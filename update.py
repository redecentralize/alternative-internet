#!/usr/bin/python
# -*- coding: utf-8 -*-
"""

    Alternative Internet Update Script
    Rolf Jagerman, Wendo Sabée, Laurens Versluis, Martijn de Vos
    TU Delft

This script reads a bunch of JSON files, finds appropriate metadata on Ohloh and writes everything neatly to a table.
The individual json files that represent the projects should have at least the following structure:

  {
    "name": "Project name",
    "description": "A description, in markdown format"
  }

This scripts adds additional ohloh metadata about the project. It is possible that this metadata is incorrect due to
Ohloh's search engine giving the wrong project. You can skip the ohloh metadata for such a project, using the
following json structure:

  {
    "name": "Project name",
    "description": "A description, in markdown format",
    "ohloh": {
      "skip": true
    }
  }

Alternatively, you can manually look up the project on Ohloh and get the correct Ohloh identifier for this project. You
can tell the script to use that identifier with the following json structure:

  {
    "name": "Project name",
    "description": "A description, in markdown format",
    "ohloh": {
      "id": "1234567"
    }
  }


Usage:

To process the JSON files in a given directory and find metadata on Ohloh, use

    python update.py -a [your-ohloh-api-key] -d [the-directory-to-store-in]

To use the default directory ("projects"), simply omit the -d parameter:

    python update.py -a [your-ohloh-api-key]

If you don't want to get information from Ohloh and just generate the table, omit the -a parameter:

    python update.py

"""

from __future__ import unicode_literals
from argparse import ArgumentParser
from os import listdir
from os.path import isfile, join
from operator import itemgetter
from collections import OrderedDict
import sys
import datetime
import logging
import codecs
import json

try:
    from urllib.request import urlopen
    from urllib.parse import urlencode
except ImportError:
    from urllib2 import urlopen
    from urllib import urlencode
try:
    from elementtree import ElementTree
except ImportError:
    from xml.etree import ElementTree


api_key = None
json_directory = 'projects'
table_file = 'README'
text_header = "# Alternative Internet\n" \
              "[Pull requests VERY welcome!](CONTRIBUTING.md)\n\n" \
              "Project statistics fetched from [Ohloh](https://www.ohloh.net).\n\n"
text_footer = ""


class SortableMarkdownTable:
    """
    Generates markdown files that represent a sortable table
    """

    def __init__(self):
        self.columns = []
        self.rows = []

    def add_column(self, title, sortable=False, suffix='', align='', width=3, reverse=False):
        """
        Adds a column to the table

        Keyword arguments:
        title -- The column's visible title
        sortable -- Whether this column is sortable (and should therefor generate a file)
        suffix -- The file suffix to write to
        align -- The column alignment
        width -- The column width
        reverse -- Whether the sorting should happen in reverse (useful for numbers)
        """
        if suffix != '':
            suffix = '_' + suffix
        self.columns.append({'title': title, 'sortable': sortable, 'reverse': reverse, 'suffix': suffix, 'align': align,
                             'width': width})

    def add_row(self, data):
        """
        Adds a row to the table

        Keyword arguments:
        data -- A list of data, the order of the data determines the column it ends up in
        """
        assert len(data) == len(self.columns)
        self.rows.append(data)

    def write_files(self, filename='README'):
        """
        Writes the table to markdown files

        Keyword arguments:
        filename -- The file to write to (without the .md extension)
        """
        for idx, column in enumerate(self.columns):
            if column['sortable']:
                self.write_file(filename, idx, column['reverse'])

    def write_file(self, filename, column_idx, reverse):
        """
        Writes a single file for a column index

        Keyword arguments:
        filename -- The file to write to
        column_idx -- The index of the column to sort on
        reverse -- Whether the sorting should happen in reverse
        """
        with codecs.open('%s%s.md' % (filename, self.columns[column_idx]['suffix']), 'w', 'utf8') as f:

            # Sort data according to column index
            data = sorted(self.rows, key=itemgetter(column_idx), reverse=reverse)

            # Write readme main text header
            f.write(text_header)

            # Write table header columns
            for idx, column in enumerate(self.columns):
                if column['sortable'] and idx != column_idx:
                    f.write('| [%s](%s) ' % (column['title'], '%s%s.md' % (filename, column['suffix'])))
                else:
                    f.write('| %s ' % column['title'])
            f.write('|\n')

            # Write spacing and alignment instructions for table
            for column in self.columns:
                f.write('| ')
                if column['align'] == 'L' or column['align'] == 'C':
                    f.write(':')
                f.write('-' * column['width'])
                if column['align'] == 'R' or column['align'] == 'C':
                    f.write(':')
                f.write(' ')
            f.write('|\n')

            # Write table data
            for row in data:
                for col in row:
                    if col is None:
                        col = '-'
                    if sys.version < '3':
                        col = unicode(col)
                    else:
                        col = str(col)
                    f.write(u'|' + col)
                f.write('|\n')

            # Write footer text
            f.write(text_footer)


def write_to_table(projects):
    """
    Writes the list of projects to several table files

    Keyword arguments:
    projects -- The list of projects to store
    """
    class OhlohValue:
        """
        Abstracts complex data and make it sortable and writable for the SortableMarkdownTable
        """
        def __init__(self, obj, value):
            if 'ohloh' in obj.keys() and value in obj['ohloh'].keys():
                self.value = obj['ohloh'][value]
            else:
                self.value = None
        def __lt__(self,other):
            if self.value == None:
                return True
            if other.value == None:
                return False
            return self.value < other.value

    class OhlohNumber(OhlohValue):
        """
        OhlohValue implementation for numeric data with a pretty unicode function for numbers that are very large
        """
        def __str__(self):
            try:
                value = float(self.value)
                sizes = ['G', 'M', 'K']
                size = ''
                while(value/(10**3) >= 1.0 and len(sizes) > 0):
                    value = value/(10**3)
                    size = sizes.pop()
                return '%d %s' % (round(value), size)
            except:
                return '-'

    class OhlohDate(OhlohValue):
        """
        OhlohValue implementation for dates with a pretty unicode function that shows the time difference
        """
        def __str__(self):
            td = datetime.datetime.now() - self.dateobj()
            if td.days < 0:
                return '-'
            if td.days < 30:  # ~one month
                return '<1 month'
            elif td.days < 356:  # ~one year
                return '%s month(s)' % int(td.days / 30)
            else:
                return '%s year(s)' % int(td.days / 356)
        def dateobj(self):
            try:
                return datetime.datetime(int(self.value[:4]), int(self.value[6:7]), int(self.value[9:10]))
            except:
                return datetime.datetime.max
        def __lt__(self,other):
            return self.dateobj() < other.dateobj()

    table = SortableMarkdownTable()

    table.add_column('Name', sortable=True, width=4)
    table.add_column('Description', width=11)
    table.add_column('Main Language',width=11, sortable=True, suffix='LANG', reverse=True)
    table.add_column('Commits', sortable=True, width=6, align='R', suffix='COMMITS', reverse=True)
    table.add_column('LOC', sortable=True, width=2, align='R', suffix='LOC', reverse=True)
    table.add_column('Total Contributors', sortable=True, width=2, align='R', suffix='CONTRIB', reverse=True)
    table.add_column('Age', sortable=True, width=2, align='R', suffix='AGE')


    for project in projects.values():
        table.add_row([project['name'],
                       project['description'],
                       OhlohValue(project,'main_language').value,
                       OhlohNumber(project, 'total_commit_count'),
                       OhlohNumber(project, 'total_code_lines'),
                       OhlohNumber(project, 'total_contributor_count'),
                       OhlohDate(project, 'min_month')
                       ])

    table.write_files(table_file)


def get_projects():
    """
    Gets a list of projects from a directory, where each json file is considered a project
    """
    projects = {}
    for file_name in listdir(json_directory):
        file_path = join(json_directory, file_name)
        if isfile(file_path) and file_path.endswith('.json'):
            print 'Loading', file_path
            projects[file_path] = json.load(open(file_path, 'r'), object_pairs_hook=OrderedDict)
    return projects


def save_project(project, file_path):
    """
    Saves given project as a json file

    Keyword arguments:
    project -- The project to store
    filename -- The filename to store the project in
    """
    json.dump(project, codecs.open(file_path, 'w', 'utf8'), indent=4)


def get_ohloh_api_request(url, api_key, params=None):
    """
    Sends an API request to Ohloh and returns the resulting xml tree or raises an exception if an error occurred.

    Keyword arguments:
    url -- The request url to get
    api_key -- The Ohloh API key to use
    params -- Additional parameters to send
    """
    parameters = {'api_key': api_key}
    if params is not None:
        for key, value in params.items():
            parameters[key] = value

    xml = urlopen('%s?%s' % (url, urlencode(parameters)))

    tree = ElementTree.parse(xml)
    error = tree.getroot().find("error")
    if error is not None:
        raise Exception(ElementTree.tostring(error))
    return tree


def search_ohloh_project(project_name):
    """
    Searches for an Ohloh project by name

    Keyword arguments:
    project_name -- The project name to search for
    """
    results = get_ohloh_api_request('https://www.ohloh.net/p.xml', api_key,
                                    {'query': project_name, 'sort': 'relevance'})
    if results.find('result/project/id') is None:
        raise Exception("Could not find project %s on Ohloh" % project_name)

    project = results.find('result/project')
    return {
        'id': project.findtext('id'),
        'name': project.findtext('name'),
        'description': project.findtext('description'),
        'analysis': project.findtext('analysis_id'),
        'tags': [tag.text for tag in project.iterfind('tags/tag')]
    }


def add_ohloh_metadata(project):
    """
    Attempts to find given project on Ohloh and adds metadata about the project

    Keyword arguments:
    project -- The Ohloh project to look for
    """
    if 'ohloh' in project.keys() and 'skip' in project['ohloh'].keys() and project['ohloh']['skip'] == True:
        project['ohloh'] = {'skip': True}
        return

    if 'ohloh' not in project.keys() or 'id' not in project['ohloh'].keys():
        project['ohloh'] = search_ohloh_project(project['name'])

    project_id = project['ohloh']['id']

    if any([e not in project['ohloh'].keys() for e in ['name', 'description', 'analysis', 'tags']]):
        results = get_ohloh_api_request('https://www.ohloh.net/p/%s.xml' % unicode(project_id), api_key)
        result = results.find('result/project')
        project['ohloh'].update({
            'id': result.findtext('id'),
            'name': result.findtext('name'),
            'description': result.findtext('description'),
            'analysis': result.findtext('analysis_id'),
            'tags': [tag.text for tag in result.iterfind('tags/tag')]
        })

    results = get_ohloh_api_request('https://www.ohloh.net/p/%s/analyses/latest.xml' % project_id, api_key)
    analysis = results.find("result/analysis")
    if analysis is None:
        raise Exception("Could not get Ohloh code analysis for project id %s" % project_id)

    project['ohloh'].update({'total_code_lines': int(analysis.findtext('total_code_lines')),
                             'total_commit_count': int(analysis.findtext('total_commit_count')),
                             'total_contributor_count': int(analysis.findtext('total_contributor_count')),
                             'twelve_month_commit_count': int(analysis.findtext('twelve_month_commit_count')),
                             'twelve_month_contributor_count': int(analysis.findtext('twelve_month_contributor_count')),
                             'updated_at': analysis.findtext('updated_at'),
                             'min_month': analysis.findtext('min_month'),
                             'max_month': analysis.findtext('max_month'),
                             'factoids': [f.text.strip() for f in analysis.iterfind('factoids/factoid')],
                             'main_language': analysis.findtext('main_language_name')})


def run_crawler():
    """
    Extracts the projects from the alternative internet page on github and downloads additional data from Ohloh.

    Keyword arguments:
    api_key -- The Ohloh API key to use
    directory -- The directory to store the resulting JSON files in
    """
    projects = get_projects()

    for file_path, project in projects.items():

        logging.info("Processing %s" % file_path)

        if api_key is not None:
            try:
                add_ohloh_metadata(project)
            except:
                logging.warning("Skipping Ohloh metadata for project %s" % project['name'])

        save_project(project, file_path)

    logging.info("Writing to tables")
    write_to_table(projects)
    logging.info("Done!")


def main():
    """
    Main entry point of the application, execution starts here
    """
    global api_key, json_directory, table_file
    logging.getLogger().setLevel(logging.INFO)
    description = 'Crawls the projects on the alternative internet github and adds additional data from Ohloh.'
    parser = ArgumentParser(description=description)

    parser.add_argument('-a', '--api', action='store', dest='api', metavar="APIKEY", default=None, required=False,
                        help='Your Ohloh API key.')

    parser.add_argument('-d', '--directory', action='store', dest='directory', metavar="projects",
                        default='projects', required=False, help='Directory where the JSON files are located.')

    parser.add_argument('-f', '--file', action='store', dest='filename', metavar="README", default='README',
                        required=False, help='File to write the output table to (without the .md extension).')

    args = parser.parse_args()

    api_key = args.api
    json_directory = args.directory
    table_file = args.filename

    run_crawler()


if __name__ == "__main__":
    main()
