"""This file implements the markdown table generate from a csv file"""

import csv
from io import IOBase
import sys

csv.field_size_limit(sys.maxsize)

__version__ = "0.2"


def handle_aligns(aligns):
    """Converts comma delimited string of alignments to tuple

    Arguments:
        aligns: comma delimited string of 'l', 'r', 'c' or empty string
    Returns:
        aligns_tuple: tuple of alignments or None
    """
    if not aligns:
        aligns_tuple = None
    else:
        aligns_tuple = tuple(aligns.lower().replace(" ", "").split(","))
    return aligns_tuple


class MDTable:
    """MDTable

        Arguments:
            filepath: string pointing to input csv file
            aligns: tuple of alignments, must have same number as number of columns
            delimiter: delimiter character in csv
            quotechar: quote character in csv
            escapechar: escape character in csv
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        csv_obj: str | IOBase,
        aligns: tuple = None,
        padding: int = 1,
        delimiter: str = ",",
        quotechar: str = '"',
        escapechar: str = "\\",
    ):
        """MDTable

        Arguments:
            csv: string pointing to input csv file or file-like object to read from
            aligns: tuple of alignments, must have same number as number of columns
            padding: padding to use in raw formatted markdown table
            delimiter: delimiter character in csv
            quotechar: quote character in csv
            escapechar: escape character in csv
        """
        self.csv_ob = csv_obj
        self.aligns = aligns
        self.padding = padding
        self._csv_dict = _read_csv(
             csv_obj, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar
        )
        self._num_cols = len(self._csv_dict.keys())
        if aligns:
            if padding == 0:
                raise ValueError("Cannot use aligns with 0 padding.")
            self._validate_aligns(self.aligns)
        self._word_length_dict = _get_max_word_per_col(self._csv_dict)

    def get_table(self) -> str:
        """Method to return markdown formatted table as string
        """
        header, dashes = self._prep_header()
        table = header + dashes
        for row in self._prep_body():
            table += row
        return table

    def save_table(self, filepath: str, mode: str = "w"):
        """Saves the output to a specified file

        Arguments:
            filepath: string representing filepath to save file
            mode: mode to open file (w, w+, a, a+)
        """
        table = self.get_table()
        with open(filepath, mode=mode) as save_file:
            save_file.write(table)

    def _validate_aligns(self, aligns):
        for align in aligns:
            if not align in ("l", "r", "c"):
                raise ValueError(
                    "Aligns must be a tuple of 'l', 'r' and 'c' for left, right and centre. Found {} instead".format(
                        align
                    )
                )
        if not len(aligns) == self._num_cols:
            raise ValueError(
                "You need to specify the alignment for all columns. There are {} columns, but you provided {} alignments".format(
                    self._num_cols, len(aligns)
                )
            )

    def _prep_header(self) -> str:
        """Returns the header of the file in markdown given a list of column names
        Returns:
            header: a string of markdown formatted header
            dashes: a string of markdown formatted dashes
        """
        word_length_dict = self._word_length_dict
        header = "|"
        dashes = "|"
        for col in range(self._num_cols):
            col_title = self._csv_dict[col][0]
            num_spaces = word_length_dict[col] - len(col_title) + self.padding
            num_dashes = word_length_dict[col]
            header += " " * self.padding + col_title + " " * num_spaces + "|"
            dashes += " " * (self.padding - 1)

            if not self.aligns or self.aligns[col] == "l":
                dashes += " " + "-" * num_dashes + " " * self.padding + "|"
            elif self.aligns[col] == "r":
                dashes += " " + "-" * num_dashes + ":" + " " * (self.padding - 1) + "|"
            elif self.aligns[col] == "c":
                dashes += (
                    ":-" + "-" * (num_dashes - 1) + ":" + " " * (self.padding - 1) + "|"
                )

        return header + "\n", dashes + "\n"

    def _prep_body(self) -> str:
        self._prep_header()
        num_rows = len(self._csv_dict[0])
        word_length_dict = self._word_length_dict
        for row_num in range(1, num_rows):
            row = "|"

            for col in range(self._num_cols):
                word = self._csv_dict[col][row_num]
                num_spaces = word_length_dict[col] - len(word) + self.padding - 1
                row += " " * self.padding + word + " " * num_spaces + " |"
            yield row + "\n"


def _get_max_word_per_col(csv_dict) -> dict:
    """Computes the maximum word lengthin for each column

    Arguments:
        csv_dict: a dictionary whose keys are column numbers and values are column lists

    Returns:
        word_length_dict: a dictionary whose keys are column numbers and whose values are the maximum word length for that column
    """
    word_length_dict = {}
    for key in csv_dict:
        max_word_length = 0
        for val in csv_dict[key]:
            if len(val) > max_word_length:
                max_word_length = len(val)
        word_length_dict[key] = max_word_length
    return word_length_dict


def _read_csv(
    csv_obj: str | IOBase, delimiter: str = ",", quotechar: str = '"', escapechar: str = "\\"
) -> dict:
    """Process a given csv into a python dictionary

    Arguments:
        csv_obj: string pointing to csv file or file-like object
        delimiter: string that denotes what char seperates values in csv_obj, default is ','
        quotechar: string that denotes what char surrounds fields containing delimeter char, default is '"'
        escapechar: string that denotes what char escaptes the delimeter char, default is no escape char.
    Returns:
        csv_dict: dictionary whose keys are column numbers and values are column lists
    """
    csv_file = None
    if isinstance(csv_obj, IOBase):
        csv_reader = csv.reader(
            csv_obj, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar
        )
    else:
        csv_file = open(csv_obj, "r")
        csv_reader = csv.reader(
            csv_file, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar
        )
    csv_dict = {}
    header = next(csv_reader)
    num_cols = len(header)
    for num in range(num_cols):
        csv_dict[num] = [header[num]]
    for row in csv_reader:
        for num in range(num_cols):
            csv_dict[num].append(row[num])
    if csv_file:
        csv_file.close()
    return csv_dict
