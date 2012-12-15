#!/usr/bin/env python
from __future__ import division

__author__ = "Jai Ram Rideout"
__copyright__ = "Copyright 2012, The QIIME project"
__credits__ = ["Jai Ram Rideout"]
__license__ = "GPL"
__version__ = "1.5.0-dev"
__maintainer__ = "Jai Ram Rideout"
__email__ = "jai.rideout@gmail.com"
__status__ = "Development"

"""Contains functionality to interact with remote services."""

from collections import defaultdict
from csv import writer
from socket import gaierror
from StringIO import StringIO
from gdata.spreadsheet import SpreadsheetsCellsFeedFromString
from gdata.spreadsheet.service import CellQuery
from gdata.spreadsheet.service import SpreadsheetsService

class RemoteMappingFileError(Exception):
    pass

class RemoteMappingFileConnectionError(RemoteMappingFileError):
    pass

# TODO test comments, empty lines/cells, quoted strings, duplicate headers, add
# reference to overview tutorial, fix url parser
def load_google_spreadsheet_mapping_file(spreadsheet_key, worksheet_name=None):
    """Loads a mapping file contained in a Google Spreadsheet.

    Returns a string containing the mapping file contents in QIIME-compatible
    format (e.g. for writing out to a file or parsing using
    qiime.parse.parse_mapping_file).

    Some of this code is based on the following websites, as well as the
    gdata.spreadsheet.text_db module:
        http://www.payne.org/index.php/Reading_Google_Spreadsheets_in_Python
        http://stackoverflow.com/a/12031835

    Arguments:
        spreadsheet_key - the key used to identify the spreadsheet (a string).
            Can either be a key or a URL containing the key
        worksheet_name - the name of the worksheet to load data from (a
            string). If not supplied, will use first worksheet in the
            spreadsheet
    """
    spreadsheet_key = _extract_spreadsheet_key_from_url(spreadsheet_key)
    gd_client = SpreadsheetsService()

    try:
        worksheets_feed = gd_client.GetWorksheetsFeed(spreadsheet_key,
                                                      visibility='public',
                                                      projection='basic')
    except gaierror:
        raise RemoteMappingFileConnectionError("Could not establish "
                                               "connection with server. Do "
                                               "you have an active Internet "
                                               "connection?")

    if len(worksheets_feed.entry) < 1:
        raise RemoteMappingFileError("The Google Spreadsheet with key '%s' "
                                     "does not have any worksheets associated "
                                     "with it." % spreadsheet_key)

    # Find worksheet that will be used as the mapping file. If a name has not
    # been provided, use the first worksheet.
    worksheet = None
    if worksheet_name is not None:
        for sheet in worksheets_feed.entry:
            if sheet.title.text == worksheet_name:
                worksheet = sheet

        if worksheet is None:
            raise RemoteMappingFileError("The worksheet name '%s' could not "
                                         "be found in the Google Spreadsheet "
                                         "with key '%s'."
                                         % (worksheet_name, spreadsheet_key))
    else:
        # Choose the first one.
        worksheet = worksheets_feed.entry[0]

    # Extract the ID of the worksheet.
    worksheet_id = worksheet.id.text.split('/')[-1]

    # Now that we have a spreadsheet key and worksheet ID, we can read the
    # mapping file data. First get the mapping file headers (first row). We
    # need this in order to grab the rest of the actual mapping file data in
    # the correct order (it is returned unordered).
    headers = _get_spreadsheet_headers(gd_client, spreadsheet_key,
                                       worksheet_id)
    if len(headers) < 1:
        raise RemoteMappingFileError("Could not load mapping file header (it "
                                     "appears to be empty). Is your Google "
                                     "Spreadsheet with key '%s' empty?"
                                     % spreadsheet_key)

    # Loop through the rest of the rows and build up a list of data (in the
    # same row/col order found in the original mapping file).
    mapping_lines = _export_mapping_file(gd_client, spreadsheet_key,
                                         worksheet_id, headers)

    out_lines = StringIO()
    tsv_writer = writer(out_lines, delimiter='\t', lineterminator='\n')
    tsv_writer.writerows(mapping_lines)
    return out_lines.getvalue()

def _extract_spreadsheet_key_from_url(url):
    """Extracts a key from a URL in the form '...key=some_key&foo=42...

    If the URL doesn't look valid, assumes the URL is the key and returns it
    unmodified.
    """
    result = url

    if 'key=' in url:
        result = url.split('key=')[-1].split('#')[0].split('&')[0]

    return result

def _get_spreadsheet_headers(client, spreadsheet_key, worksheet_id):
    """Returns a list of headers (the first line of the spreadsheet).

    Will be in the order they appear in the spreadsheet.
    """
    headers = []

    query = CellQuery()
    query.max_row = '1'
    query.min_row = '1'
    feed = client.GetCellsFeed(spreadsheet_key, worksheet_id, query=query,
                               visibility='public', projection='values')

    # Wish python had a do-while...
    while True:
        for entry in feed.entry:
            headers.append(entry.content.text)

        # Get the next set of cells if needed.
        next_link = feed.GetNextLink()

        if next_link:
            feed = client.Get(next_link.href,
                              converter=SpreadsheetsCellsFeedFromString)
        else:
            break

    return headers

def _export_mapping_file(client, spreadsheet_key, worksheet_id, headers):
    """Returns a list of lists containing the entire mapping file.

    This will include the header, any comment lines, and the mapping data.
    Blank cells are represented as None. Data will only be read up to the first
    blank line that is encountered (this is a limitation of the Google
    Spreadsheet API).

    Comments are only supported after the header and before any real data is
    encountered. The lines must start with [optional whitespace] '#' and only
    the first cell is kept in that case (to avoid many empty cells after the
    comment cell, which mimics QIIME's mapping file format).

    Only cell data that falls under the supplied headers will be included.
    """
    # Convert the headers into Google's internal "cleaned" representation.
    # These will be used as lookups to pull out cell data.
    cleaned_headers = _get_cleaned_headers(headers)

    # List feed skips header and returns rows in the order they appear in the
    # spreadsheet.
    mapping_lines = [headers]
    rows_feed = client.GetListFeed(spreadsheet_key, worksheet_id,
                                   visibility='public', projection='values')
    while True:
        found_data = False

        for row in rows_feed.entry:
            line = []

            # Loop through our headers and use the cleaned version to lookup
            # the cell data. In certain cases (if the original header was blank
            # or only contained special characters) we will not be able to map
            # our header, so the best we can do is tell the user to change the
            # name of their header to be something simple/alphanumeric.
            for header_idx, (header, cleaned_header) in \
                    enumerate(zip(headers, cleaned_headers)):
                try:
                    cell_data = row.custom[cleaned_header].text
                except KeyError:
                    raise RemoteMappingFileError("Could not map header '%s' "
                            "to Google Spreadsheet's internal representation "
                            "of the header. We suggest changing the name of "
                            "the header in your Google Spreadsheet to be "
                            "alphanumeric if possible, as this will likely "
                            "solve the issue." % header)

                # Special handling of comments (if it's a comment, only keep
                # that cell to avoid several blank cells following it).
                if not found_data and header_idx == 0 and \
                   cell_data.lstrip().startswith('#'):
                    line.append(cell_data)
                    break
                else:
                    line.append(cell_data)
                    found_data = True

            mapping_lines.append(line)

        # Get the next set of rows if necessary.
        next_link = rows_feed.GetNextLink()

        if next_link:
            rows_feed = client.Get(next_link.href,
                                   converter=SpreadsheetsListFeedFromString)
        else:
            break

    return mapping_lines

def _get_cleaned_headers(headers):
    """Creates a list of "cleaned" headers which spreadsheets accept.

    A Google Spreadsheet converts the header names into a "cleaned" internal
    representation, which must be used to reference a cell at a particular
    header/column. They are all lower case and contain no spaces or special
    characters. If two columns have the same name after being sanitized, the 
    columns further to the right have _2, _3 _4, etc. appended to them.

    If there are column names which consist of all special characters, or if
    the column header is blank, an obfuscated value will be used for a column
    name. This method does not handle blank column names or column names with
    only special characters.

    Taken from gdata.spreadsheet.text_db.ConvertStringsToColumnHeaders and
    modified to handle headers with pound signs, as well as correctly handle
    duplicate cleaned headers.
    """
    cleaned_headers = []
    for header in headers:
        # Probably a more efficient way to do this. Perhaps regex.
        sanitized = header.lower().replace('_', '').replace(':', '').replace(
                ' ', '').replace('#', '')
        cleaned_headers.append(sanitized)

    # When the same sanitized header appears multiple times in the first row
    # of a spreadsheet, _n is appended to the name to make it unique.
    header_count = defaultdict(int)
    results = []

    for header, cleaned_header in zip(headers, cleaned_headers):
        new_header = cleaned_header

        if header_count[cleaned_header] > 0:
            new_header = '%s_%d' % (cleaned_header,
                                    header_count[cleaned_header])

        header_count[cleaned_header] += 1
        results.append(new_header)

    return results
