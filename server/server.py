#!/usr/bin/env python3

import sys
import os
parent_dir = os.path.dirname(os.getcwd())
sys.path.insert(0, parent_dir)


import config

import sqlite3
import hashlib
from time import time
from copy import copy
from datetime import datetime
from traceback import print_exc
from multiprocessing import Process, Queue

from flask import Flask, request, jsonify


app = Flask(__name__)


# Used to properly access the DB from its config path
os.chdir(parent_dir)


def md5(input):
    """Return an MD5 hash of the input data."""
    h = hashlib.md5()
    h.update(input.encode('utf-8'))
    return h.digest()


class QueryResult:
    """Implements the fields necessary for query caching."""
    def __init__(self, query_hash, result):
        self.query_hash = query_hash
        self.result = copy(result)
        self.updated = datetime.now()
        if 'query_time_sec' in self.result:
            del self.result['query_time_sec']


class QueryResultsCache:
    """
    Cache SQL query results. If a query is made two or more times within
    `expiry` seconds, the first result will be cached and returned for
    subsequent results.
    """
    def __init__(self, expiry=60):
        self.expiry = expiry
        self._queries = {}

    def query_results(self, query):
        query_hash = md5(query)

        if query_hash not in self._queries:
            r = query_results(query)
            self._queries[query_hash] = QueryResult(query_hash, r)
            return r

        cached = self._queries[query_hash]
        then = cached.updated
        now = datetime.now()

        until_expiry = (now - then).total_seconds()
        if until_expiry < self.expiry:
            return cached.result
        else:
            r = query_results(query)
            self._queries[query_hash] = QueryResult(query_hash, r)
            return r


cache = QueryResultsCache(expiry=config.QUERY_CACHE_EXPIRY_SECS)


def query_processor(conn, query, result_queue):
    """Return results for an SQL query with the time the queries took."""
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


def query_results(query):
    """
    Synchronously return results for an SQL query and return them as a dict to
    be sent back to clients.

    If the query takes too long, kill the query process and return an error
    instead.
    """
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
        return err

    output = result_queue.get()

    if type(output) is sqlite3.OperationalError:
        err = {'error': repr(output)}
        return err

    return output


@app.after_request
def allow_cors(response):
    """Allow CORS on every response this server sends."""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    return response


@app.route('/', methods=['GET'])
def hello():
    """Let curious users know what Narcissa is."""
    return ('Hello. I\'m a Narcissa server. <a href="https://github.com/'
            'mplewis/narcissa">Learn more</a>.')


@app.route('/', methods=['POST'])
def sql_queries():
    """
    Answer a bundle of SQL queries POSTED to the server with a bundle of query
    results.
    """
    try:
        results = {}
        for name, query in request.form.items():
            results[name] = cache.query_results(query)
        return jsonify(results)
    except Exception:
        # It's a little hacky but it lets us get proper tracebacks from the
        # server, even without debug mode
        print_exc()

if __name__ == '__main__':
    app.run()
