#!/usr/bin/env python3

import sys
import os
parent_dir = os.path.dirname(os.getcwd())
sys.path.insert(0, parent_dir)


import config

import sqlite3
from flask import Flask, request, jsonify


app = Flask(__name__)

os.chdir(parent_dir)
print(os.getcwd())
conn = sqlite3.connect(config.DB_URI_READ_ONLY, uri=True)


@app.route('/', methods=['GET'])
def hello_world():
    return 'Hello World!'


@app.route('/', methods=['POST'])
def sql_query():
    if 'query' not in request.form:
        err = {'error': 'No query provided. Post SQL queries as '
                        'form URL-encoded param "query".'}
        return jsonify(err), 400
    query = request.form['query']

    try:
        results = conn.execute(query)
    except sqlite3.OperationalError as e:
        err = {'error': repr(e)}
        return jsonify(err), 400

    column_names = [n[0] for n in results.description]
    named_results = []
    for row in results:
        named_row = {}
        for num, cell in enumerate(row):
            named_row[column_names[num]] = cell
        named_results.append(named_row)

    output = {'rows': named_results}
    return jsonify(output)


if __name__ == '__main__':
    app.run()
