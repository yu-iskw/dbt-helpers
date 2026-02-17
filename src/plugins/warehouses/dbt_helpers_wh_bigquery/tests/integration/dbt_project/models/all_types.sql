SELECT
    CAST('hello' AS STRING) AS s,
    CAST('world' AS BYTES) AS b,
    CAST(123 AS INT64) AS i,
    CAST(1.23 AS FLOAT64) AS f,
    CAST(TRUE AS BOOL) AS bool_col,
    CAST('2023-01-01 12:00:00 UTC' AS TIMESTAMP) AS ts,
    CAST('2023-01-01' AS DATE) AS d,
    CAST('12:00:00' AS TIME) AS t,
    CAST('2023-01-01 12:00:00' AS DATETIME) AS dt,
    ST_GEOGFROMTEXT('POINT(1 1)') AS geo,
    JSON '{"key": "value"}' AS json_col,
    INTERVAL 1 YEAR AS interval_col,
    -- Parameterized
    CAST('short' AS STRING(10)) AS s10,
    CAST('bytes' AS BYTES(10)) AS b10,
    CAST(123.45 AS NUMERIC(10, 2)) AS num,
    CAST(123.45678 AS BIGNUMERIC(20, 5)) AS bignum,
    -- Complex
    ARRAY['a', 'b', 'c'] AS arr_str,
    STRUCT(1 AS sub_int, 'sub' AS sub_str) AS rec,
    ARRAY[STRUCT(1.1 AS x, 2.2 AS y), STRUCT(3.3 AS x, 4.4 AS y)] AS coords,
    -- Ranges
    RANGE(DATE '2023-01-01', DATE '2023-01-02') AS r_date,
    RANGE(DATETIME '2023-01-01 12:00:00', DATETIME '2023-01-01 13:00:00') AS r_datetime,
    RANGE(TIMESTAMP '2023-01-01 12:00:00 UTC', TIMESTAMP '2023-01-01 13:00:00 UTC') AS r_timestamp
