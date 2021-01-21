#!/usr/bin/env python
import os
import sys
import time
import json
import unittest
import pandas as pd
from typing import Optional

import requests

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from tests import config  # initialize the test environment
from terra_notebook_utils import table
from terra_notebook_utils import WORKSPACE_NAME, WORKSPACE_GOOGLE_PROJECT


def to_dataframe(table_name: str, max_rows: Optional[int]=None) -> pd.DataFrame:
    if max_rows is None:
        ents = [row.attributes for row in table.list_rows(table_name)]
    else:
        ents = [row.attributes for _, row in zip(range(max_rows), table.list_rows(table_name))]
    return pd.DataFrame(ents)

def to_table(table_name: str, df: pd.DataFrame):
    with table.Writer(table_name) as writer:
        for _, series in df.iterrows():
            attributes = dict()
            for name, val in dict(series).items():
                if not pd.isnull(val):
                    key = "-".join(name) if isinstance(name, tuple) else name
                    attributes[key] = val
            writer.put_row(attributes)

class TestTransformation(unittest.TestCase):
    def test_transformation(self):
        start_time = time.time()
        df = to_dataframe("sequencing", 500)
        # df = pd.read_pickle("df.pickle")
        df = df[df['pfb:sample'].notna()]
        df['sample'] = [series['pfb:sample']['entityName'] for _, series in df.iterrows()]
        del df['pfb:sample']
        wide = df.pivot(index="sample",
                        columns="pfb:data_format",
                        values=["pfb:object_id", "pfb:file_size", "pfb:file_name"])
        to_table("sequencing-wide", wide)
        print("Duration", time.time() - start_time)

    def _doom(self):
        data = dict()
        for row_id, attributes in table.list_rows("sequencing"):
            if "pfb:sample" in attributes:
                sample_id = attributes['pfb:sample']['entityName']
                if sample_id in data:
                    for a, b in zip(attributes.keys(), data[sample_id].keys()):
                        print(a, "--", b)
                    print(attributes['pfb:object_id'], attributes['pfb:ga4gh_drs_uri'])
                    print(data[sample_id]['pfb:object_id'], data[sample_id]['pfb:ga4gh_drs_uri'])
                    break
                else:
                    data[sample_id] = attributes

if __name__ == '__main__':
    unittest.main()
