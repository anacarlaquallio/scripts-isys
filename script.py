#!/usr/bin/python3

import csv
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.customization import *

import os.path
import sys


class BibtexFilter(object):

    def __init__(self):
        self.input_bibtex_file = None
        self.output_csv_file = None
        self.fields = dict()
        self.mandatory_fields = set()
        self.default_field_value = dict()
        self.entry_types = set()

    def add_entry_type(self, entry_type):
        self.entry_types.add(entry_type)

    def add_field(self, header_name, fields, default_value, is_mandatory=False):
        if not header_name in self.fields:
            self.fields[header_name] = []
            self.default_field_value[header_name] = default_value
        if fields is not None:
            self.fields[header_name] += fields
        if is_mandatory:
            self.mandatory_fields.add(header_name)

    def set_input_file(self, bibtex_filename):
        self.input_bibtex_file = bibtex_filename

    def set_output_csv_file(self, csv_filename):
        self.output_csv_file = csv_filename

    def run(self):
        parser = BibTexParser(
            common_strings=True,
            ignore_nonstandard_types=False,
            homogenize_fields=False,
            customization=add_plaintext_fields,
            add_missing_from_crossref=True
        )

        with open(self.input_bibtex_file) as bibtex_input_file:
            try:
                raw_database = parser.parse_file(bibtex_input_file)
            except UnicodeDecodeError:
                with open(self.input_bibtex_file, encoding="latin-1") as bibtex_input_file_fallback:
                    raw_database = parser.parse_file(bibtex_input_file_fallback)

        included_csv = self.output_csv_file
        excluded_csv = "excluded_" + self.output_csv_file

        with open(included_csv, 'w', newline='') as incfile, \
             open(excluded_csv, 'w', newline='') as excfile:

            incwriter = csv.writer(incfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            excwriter = csv.writer(excfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

            headers = list(self.fields.keys())
            incwriter.writerow(headers)
            excwriter.writerow(["ID", "ENTRYTYPE", "title", "year", "reason"])

            for entry in raw_database.entries:

                # filtro por tipo
                if self.entry_types and entry["ENTRYTYPE"] not in self.entry_types:
                    excwriter.writerow([
                        entry.get("ID", ""),
                        entry.get("ENTRYTYPE", ""),
                        entry.get("title", ""),
                        entry.get("year", ""),
                        "wrong_entry_type"
                    ])
                    continue

                csv_row = []
                entry_status = True
                reason = ""

                for header, fields in self.fields.items():
                    field_status = False

                    for field in fields:
                        if field in entry and entry[field]:
                            field_status = True
                            if field == 'doi':
                                csv_row.append('https://dx.doi.org/' + entry[field])
                            else:
                                csv_row.append(entry[field])
                            break

                    if not field_status:
                        if header in self.mandatory_fields:
                            entry_status = False
                            reason = f"missing_{header}"
                        csv_row.append(self.default_field_value[header])

                if entry_status:
                    incwriter.writerow(csv_row)
                else:
                    excwriter.writerow([
                        entry.get("ID", ""),
                        entry.get("ENTRYTYPE", ""),
                        entry.get("title", ""),
                        entry.get("year", ""),
                        reason
                    ])


if __name__ == "__main__":
    bibtex_filename = sys.argv[1]
    basename = os.path.basename(bibtex_filename)
    (filename, extension) = os.path.splitext(basename)

    bibtex_filter = BibtexFilter()
    bibtex_filter.set_input_file(bibtex_filename)
    bibtex_filter.set_output_csv_file(filename + '.csv')

    bibtex_filter.add_entry_type('inproceedings')
    bibtex_filter.add_entry_type('article')

    bibtex_filter.add_field('Document Title', ['title'], '', True)
    bibtex_filter.add_field('Abstract', ['abstract'], '')
    bibtex_filter.add_field('Year', ['year'], 0)
    bibtex_filter.add_field('PDF Link', ['doi', 'url'], '')

    bibtex_filter.run()
