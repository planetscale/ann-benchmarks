import subprocess
import sys
import struct

import mysql.connector
from mysql.connector import Error

from ..base.module import BaseANN

BATCH_SIZE=128

class MySQL(BaseANN):
    def __init__(self, metric, method_param):
        self._metric = metric
        self._connection = None
        self._cursor = None

        if metric == "angular":
            self._query = "SELECT id,DISTANCE(embedding,CAST(%s AS CHAR CHARACTER SET BINARY),'COSINE') AS d FROM items ORDER BY d LIMIT %s"
        elif metric == "euclidean":
            self._query = "SELECT id,DISTANCE(embedding,CAST(%s AS CHAR CHARACTER SET BINARY),'L2') AS d FROM items ORDER BY d LIMIT %s"
        else:
            raise RuntimeError(f"unknown metric {metric}")

        if 'fq' in method_param:
            fq = method_param['fq']
            self._quant = f', "fixed_quantization":"{fq}"'
            self._quant_desc = "fq=#{fq}"
        elif 'pq' in method_param:
            pq = method_param['pq']
            self._quant = f', "product_quantization":{{"dimensions":{pq}}}'
            self._quant_desc = "pq=#{pq}"
        else:
            self._quant = ""
            self._quant_desc = "nq"

    def fit(self, X):
        connection = mysql.connector.connect(user='root', password='')
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS ann")
        cursor.execute("USE ann")
        cursor.execute("DROP TABLE IF EXISTS items")
        cursor.execute("CREATE TABLE items (id INT PRIMARY KEY NOT NULL, embedding VECTOR(%d))" % X.shape[1])

        print("copying data...")
        data = []
        for i, embedding in enumerate(X):
            blob = struct.pack(f'{len(embedding)}f', *embedding)
            data.append(i)
            data.append(blob)
            if len(data) == 2*BATCH_SIZE:
                stmt = "INSERT INTO items(id, embedding) VALUES " + ",".join(['(%s,CAST(%s AS CHAR CHARACTER SET BINARY))'] * BATCH_SIZE)
                cursor.execute(stmt, tuple(data))
                data = []
        if len(data) > 0:
            stmt = "INSERT INTO items(id, embedding) VALUES " + ",".join(['(%s,CAST(%s AS CHAR CHARACTER SET BINARY))'] * (len(data)//2))
            cursor.execute(stmt, tuple(data))
            data = []

        if self._metric == "angular":
            stmt = "ALTER TABLE items ADD VECTOR INDEX(embedding) SECONDARY_ENGINE_ATTRIBUTE='{\"type\":\"spann\", \"distance\":\"cosine\"" + self._quant + "}'"
        elif self._metric == "euclidean":
            stmt = "ALTER TABLE items ADD VECTOR INDEX(embedding) SECONDARY_ENGINE_ATTRIBUTE='{\"type\":\"spann\", \"distance\":\"l2\"" + self._quant + "}'"
        else:
            raise RuntimeError(f"unknown metric {self._metric}")
        print(f"creating index: {stmt}")
        cursor.execute(stmt)
        print("done!")
        self._connection = connection
        self._cursor = cursor

    def set_query_arguments(self, oversample):
        self._oversample = oversample
        print(f"Oversampling: {oversample}")

    def query(self, v, n):
        blob = struct.pack(f'{len(v)}f', *v)
        if self._oversample > 1:
            stmt = f'SELECT * FROM ({self._query}) ttt ORDER BY d LIMIT %s;'
            data = (blob, int(n*self._oversample), n)
        else:
            stmt = self._query
            data = (blob, n)
        self._cursor.execute(stmt, data)
        return [row[0] for row in self._cursor.fetchall()]

    def get_memory_usage(self):
        if self._cursor is None:
            return 0
        self._cursor.execute("""
            SELECT
                it.name,
                SUM(its.file_size) as hidden_tables_sum_file_size,
                SUM(its.allocated_size) as hidden_tables_sum_allocated_size
              FROM
                information_schema.innodb_tables it
                JOIN information_schema.innodb_tablespaces its
                ON (
                     its.name LIKE CONCAT(database(), '/fts_', CONVERT(LPAD(HEX(table_id), 16, '0') USING utf8mb3) COLLATE utf8mb3_general_ci, '_%')
                  OR its.name LIKE CONCAT(database(), '/vec_', CONVERT(LPAD(HEX(table_id), 16, '0') USING utf8mb3) COLLATE utf8mb3_general_ci, '_%')
                )
                WHERE
                     its.name LIKE CONCAT(database(), '/fts_%')
                  OR its.name LIKE CONCAT(database(), '/vec_%')
                GROUP BY it.name""")
        size_in_bytes = self._cursor.fetchone()[1]
        return int(size_in_bytes) / 1024

    def __str__(self):
        return f"MySQL(oversample={self._oversample},{self._quant_desc})"
