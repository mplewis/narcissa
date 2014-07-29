#!/usr/bin/env python3

import sys
import os
parent_dir = os.path.dirname(os.getcwd())
sys.path.insert(0, parent_dir)


import config

import sqlite3
from time import time
from traceback import print_exc
from multiprocessing import Process, Queue
from flask import Flask, request, jsonify


app = Flask(__name__)


os.chdir(parent_dir)
print(os.getcwd())


def query_processor(conn, query, result_queue):
    try:
        start_time = time()
        results = conn.execute(query)
        query_time = time() - start_time
    except sqlite3.OperationalError as e:
        result_queue.put(e)
        return

    column_names = [n[0] for n in results.description]
    named_results = []
    for row in results:
        named_row = {}
        for num, cell in enumerate(row):
            named_row[column_names[num]] = cell
        named_results.append(named_row)

    output = {'results': named_results, 'query_time_sec': query_time}
    result_queue.put(output)


@app.after_request
def allow_cors(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    return response


@app.route('/', methods=['GET'])
def hello_world():
    return 'Hello World!'


@app.route('/', methods=['POST'])
def sql_query():
    try:
        if 'query' not in request.form:
            err = {'error': 'No query provided. Post SQL queries as '
                            'form URL-encoded param "query".'}
            return jsonify(err), 400
        query = request.form['query']

        conn = sqlite3.connect(config.DB_URI_READ_ONLY, uri=True)
        result_queue = Queue()

        query_process = Process(target=query_processor,
                                args=(conn, query, result_queue))
        query_process.start()
        query_process.join(config.QUERY_TIMEOUT_SECS)

        if query_process.is_alive():
            query_process.terminate()
            err = {'error': 'Query took too long; max time %s seconds' %
                            config.QUERY_TIMEOUT_SECS}
            return jsonify(err), 400

        output = result_queue.get()

        if type(output) is sqlite3.OperationalError:
            err = {'error': repr(output)}
            return jsonify(err), 400

        return jsonify(output)

    except Exception:
        # It's a little hacky but it lets us get proper tracebacks from the
        # server, even without debug mode
        print_exc()

if __name__ == '__main__':
    app.run()
