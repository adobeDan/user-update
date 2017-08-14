# Copyright (c) 2016-2017 Adobe Systems Incorporated.  All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import csv
import os
import sys

import six


def is_py2():
    return sys.version_info.major == 2


def normalize_string(string_value):
    """
    Normalize a unicode or regular string
    :param string_value: either a unicode or regular string or None
    :return: the same type that came in
    """
    return string_value.strip().lower() if string_value is not None else None


class CSVAdapter:
    """
    Read and write CSV files to and from lists of dictionaries
    """
    @staticmethod
    def open_csv_file(name, mode, encoding=None):
        """
        :type name: str
        :type mode: str
        :type encoding: str, but ignored in py2
        :rtype file
        """
        try:
            if mode == 'r':
                if is_py2():
                    return open(str(name), 'rb', buffering=1)
                else:
                    kwargs = dict(buffering=1, newline='', encoding=encoding)
                    return open(str(name), 'r', **kwargs)
            elif mode == 'w':
                if is_py2():
                    return open(str(name), 'wb')
                else:
                    kwargs = dict(newline='')
                    return open(str(name), 'w', **kwargs)
            else:
                raise ValueError("File mode (%s) must be 'r' or 'w'" % mode)
        except IOError as e:
            raise Exception("Can't open file '%s': %s" % (name, e.message))

    @staticmethod
    def guess_delimiter_from_filename(filename):
        """
        :type filename
        :rtype str
        """
        _base_name, extension = os.path.splitext(filename)
        normalized_extension = normalize_string(extension)
        if normalized_extension == '.csv':
            return ','
        if normalized_extension == '.tsv':
            return '\t'
        return '\t'

    @classmethod
    def read_csv_rows(cls, file_path, recognized_column_names=None, logger=None, encoding='utf8', delimiter=None):
        """
        :type file_path: str
        :type recognized_column_names: list(str)
        :type logger: logging.Logger
        :type encoding: str
        :type delimiter: str
        """
        if is_py2():
            # in py2, we need to encode the column names, because the file is read as bytes
            encoded_names = []
            for name in recognized_column_names:
                encoded_names.append(name.encode(encoding, 'strict'))
            recognized_column_names = encoded_names
        with cls.open_csv_file(file_path, 'r', encoding) as input_file:
            if delimiter is None:
                delimiter = cls.guess_delimiter_from_filename(file_path)
            try:
                reader = csv.DictReader(input_file, delimiter=delimiter)
                if recognized_column_names is not None:
                    unrecognized_column_names = [column_name for column_name in reader.fieldnames
                                                 if column_name not in recognized_column_names]
                    if len(unrecognized_column_names) > 0 and logger is not None:
                        logger.warn("In file '%s': unrecognized column names: %s", file_path, unrecognized_column_names)
                for row in reader:
                    if is_py2():
                        # in py2, we need to decode both the column names *and* the values
                        newrow = {}
                        for key, val in six.iteritems(row):
                            newrow[key.decode(encoding, 'strict')] = val.decode(encoding, 'strict') if val else None
                        row = newrow
                    yield row
            except UnicodeError as e:
                raise Exception("Encoding error in file '%s': %s" % (file_path, e.message))

    @classmethod
    def write_csv_rows(cls, file_path, field_names, rows, encoding='utf8', delimiter=None):
        """
        :type file_path: str
        :type field_names: list(str)
        :type rows: list(dict)
        :type encoding: str
        :type delimiter: str
        """
        with cls.open_csv_file(file_path, 'w', encoding=encoding) as output_file:
            if delimiter is None:
                delimiter = cls.guess_delimiter_from_filename(file_path)
            writer = csv.DictWriter(output_file, fieldnames=field_names, delimiter=delimiter)
            if is_py2():
                # in py2, we need to encode the field names in the header, because the file is written as bytes
                header_row = {}
                for name in field_names:
                    header_row[name] = name.encode(encoding, 'strict')
                writer.writerow(header_row)
            else:
                writer.writeheader()
            for row in rows:
                if is_py2():
                    # in py2, we have to encode the field values, because the file is written as bytes
                    for name, val in six.iteritems(row):
                        row[name] = val.encode(encoding, 'strict')
                writer.writerow(row)