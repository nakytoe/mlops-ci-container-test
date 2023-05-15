import numpy as np
import pandas as pd
import unittest

from metrics import (
    is_timedelta,
    is_timestamp,
    is_time,
    is_numeric,
    is_bool,
    is_str,
    is_categorical,
    is_object,
    get_dtypename,
    value_dtypename,
)

import datetime as dt

# data type samples
PY_NUMERIC = [[1, 1.0, 1.1], [2, 2.0, 2.2]]

NP_INT64 = np.ones(1).astype("int")
NP_FLOAT64 = NP_INT64.astype("float")
NP_BOOL = np.array([True]).astype("bool")
NP_STR = np.array(["test_string"]).astype("str")
NP_DT = np.array([np.datetime64("2020-10-01")])
NP_TD = np.array([np.timedelta64(1, "D")])

PD_INT64 = pd.DataFrame([1]).astype("int64")
PD_FLOAT64 = pd.DataFrame([1]).astype("float64")
PD_BOOL = pd.DataFrame([True]).astype("bool")
PD_BOOLEAN = pd.DataFrame([True]).astype("boolean")
PD_STR = pd.DataFrame(["string it is"]).astype("str")
PD_STRING = pd.DataFrame(["string it is"]).astype("string")
PD_DT = pd.to_datetime(["2020-10-1"])
PD_TD = pd.to_timedelta(["1d"])
PD_PERIOD = pd.DataFrame([pd.Period("2020Q1")])


class TestTypeChecks(unittest.TestCase):
    def test_dtypename(self):
        # built-in data types
        self.assertEqual(value_dtypename(1), "int")
        self.assertEqual(value_dtypename(1.0), "float")
        self.assertEqual(value_dtypename(True), "bool")
        self.assertEqual(value_dtypename("this is string"), "str")
        self.assertEqual(value_dtypename(dt.datetime.now()), "datetime")
        # numpy
        self.assertEqual(value_dtypename(NP_INT64[0]), "int64")
        self.assertEqual(value_dtypename(NP_FLOAT64[0]), "float64")
        self.assertEqual(value_dtypename(NP_BOOL[0]), "bool")
        self.assertEqual(value_dtypename(NP_STR[0]), "<U11")
        self.assertEqual(value_dtypename(NP_DT[0]), "datetime64[D]")
        self.assertEqual(value_dtypename(NP_TD[0]), "timedelta64[D]")
        # pandas
        self.assertEqual(value_dtypename(PD_INT64.iloc[0]), "int64")
        self.assertEqual(value_dtypename(PD_FLOAT64.iloc[0]), "float64")
        self.assertEqual(value_dtypename(PD_BOOL.iloc[0]), "bool")
        self.assertEqual(value_dtypename(PD_BOOLEAN.iloc[0]), "boolean")
        self.assertEqual(value_dtypename(PD_STR.iloc[0]), "object")
        self.assertEqual(value_dtypename(PD_STRING.iloc[0]), "string")
        self.assertEqual(value_dtypename(PD_DT[0]), "Timestamp")
        self.assertEqual(value_dtypename(PD_TD[0]), "Timedelta")
        self.assertEqual(value_dtypename(PD_PERIOD.iloc[0]), "period[Q-DEC]")

    def test_dtypename_checks(self):
        # built-in data types
        self.assertTrue(is_numeric(value_dtypename(1)))
        self.assertTrue(is_numeric(value_dtypename(1.0)))
        self.assertTrue(is_bool(value_dtypename(True)))
        self.assertTrue(is_str(value_dtypename("this is string")))
        self.assertTrue(is_time(value_dtypename(dt.datetime.now())))
        # numpy
        self.assertTrue(is_numeric(value_dtypename(NP_INT64[0])))
        self.assertTrue(is_numeric(value_dtypename(NP_FLOAT64[0])))
        self.assertTrue(is_bool(value_dtypename(NP_BOOL[0])))
        self.assertTrue(is_str(value_dtypename(NP_STR[0])))
        self.assertTrue(is_timestamp(value_dtypename(NP_DT[0])))
        self.assertTrue(is_timedelta(value_dtypename(NP_TD[0])))
        # pandas
        self.assertTrue(is_numeric(value_dtypename(PD_INT64.iloc[0])))
        self.assertTrue(is_numeric(value_dtypename(PD_FLOAT64.iloc[0])))
        self.assertTrue(is_bool(value_dtypename(PD_BOOL.iloc[0])))
        self.assertTrue(is_bool(value_dtypename(PD_BOOLEAN.iloc[0])))
        self.assertTrue(is_str(value_dtypename(PD_STR.iloc[0])))
        self.assertTrue(is_str(value_dtypename(PD_STRING.iloc[0])))
        self.assertTrue(is_timestamp(value_dtypename(PD_DT[0])))
        self.assertTrue(is_timedelta(value_dtypename(PD_TD[0])))
        self.assertTrue(is_timedelta(value_dtypename(PD_PERIOD.iloc[0])))
        # misc
        self.assertTrue(is_object(value_dtypename({"this": "is a dict"})))
        # negative
        self.assertFalse(is_time(value_dtypename(1)))
        self.assertFalse(is_timedelta(value_dtypename(PD_DT[0])))
        self.assertFalse(is_timestamp(value_dtypename(PD_TD[0])))
        self.assertFalse(is_bool(value_dtypename(1)))
        self.assertFalse(is_numeric(value_dtypename("string")))
        self.assertFalse(is_object(value_dtypename(1)))


from metrics import DriftQueue, convert_time_to_seconds, string_is_time


class TestDriftQueue(unittest.TestCase):
    def test_init(self):
        self.assertIsInstance(DriftQueue({"x": int}), DriftQueue)

    def test_put(self):
        fifof = DriftQueue({"x": int})
        fifof.put(np.arange(10))
        self.assertEqual(fifof.df.shape[0], 10)
        self.assertEqual(fifof.df.shape[1], 1)
        # more data
        fifof = DriftQueue({"x": float, "y": float})
        fifof.put(np.random.rand(100, 2))
        self.assertEqual(fifof.df.shape[0], 100)
        self.assertEqual(fifof.df.shape[1], 2)

    def test_put_overwrite(self):
        fifof = DriftQueue({"x": int}, maxsize=1)
        fifof.put(np.arange(2))
        self.assertEqual(fifof.df.iloc[0, 0], 1)
        #
        fifof = DriftQueue({"x": int})
        fifof.put(np.arange(1001))
        self.assertEqual(fifof.df.iloc[0, 0], 1)
        self.assertEqual(fifof.df.iloc[-1, 0], 1000)
        #
        fifof = DriftQueue({"x": str}, maxsize=3)
        fifof.put(["a", "b", "c", "d"])
        self.assertEqual(fifof.df.iloc[0, 0], "b")
        self.assertEqual(fifof.df.iloc[-1, 0], "d")

    def test_flush(self):
        fifof = DriftQueue({"x": int}, maxsize=1)
        ret = fifof.flush()
        self.assertTrue(ret.empty)
        #
        fifof = DriftQueue({"x": int}, maxsize=1)
        fifof.put([1])
        ret = fifof.flush()
        self.assertEqual(ret.iloc[0, 0], 1)
        self.assertEqual(fifof.df.shape[0], 0)
        #
        fifof = DriftQueue({"x": int}, maxsize=10)
        fifof.put(range(11))
        ret = fifof.flush()
        self.assertEqual(ret.iloc[0, 0], 1)
        self.assertEqual(fifof.df.shape[0], 0)

    def test_flush_clear_false(self):
        fifof = DriftQueue({"x": int}, maxsize=1, clear_at_flush=False)
        fifof.put([1])
        ret = fifof.flush()
        self.assertEqual(ret.iloc[0, 0], 1)
        self.assertEqual(fifof.df.shape[0], 1)
        #
        fifof = DriftQueue({"x": int}, maxsize=10, clear_at_flush=False)
        fifof.put(range(11))
        ret = fifof.flush()
        self.assertEqual(ret.iloc[0, 0], 1)
        self.assertEqual(fifof.df.shape[0], 10)
        #
        fifof = DriftQueue({"x": int}, maxsize=1, clear_at_flush=False)
        ret = fifof.flush()
        self.assertTrue(ret.empty)
        self.assertEqual(fifof.df.shape[0], 0)
        #
        fifof = DriftQueue({"x": int}, maxsize=2, clear_at_flush=False)
        fifof.put([1])
        ret = fifof.flush()
        self.assertTrue(ret.empty)
        self.assertEqual(fifof.df.shape[0], 1)

    def test_only_flush_full_false(self):
        fifof = DriftQueue({"x": int}, maxsize=1, only_flush_full=False)
        fifof.put([1])
        ret = fifof.flush()
        self.assertEqual(ret.iloc[0, 0], 1)
        self.assertEqual(fifof.df.shape[0], 0)
        #
        fifof = DriftQueue({"x": int}, maxsize=10, only_flush_full=False)
        fifof.put(range(11))
        ret = fifof.flush()
        self.assertEqual(ret.iloc[0, 0], 1)
        self.assertEqual(fifof.df.shape[0], 0)
        #
        fifof = DriftQueue({"x": int}, maxsize=1, only_flush_full=False)
        ret = fifof.flush()
        self.assertTrue(ret.empty)
        self.assertEqual(fifof.df.shape[0], 0)
        #
        fifof = DriftQueue({"x": int}, maxsize=2, only_flush_full=False)
        fifof.put([1])
        ret = fifof.flush()
        self.assertEqual(ret.iloc[0, 0], 1)
        self.assertEqual(fifof.df.shape[0], 0)

    def test_clear_at_flush_false_only_flush_full_false(self):
        fifof = DriftQueue(
            {"x": int}, maxsize=1, clear_at_flush=False, only_flush_full=False
        )
        fifof.put([1])
        ret = fifof.flush()
        self.assertEqual(ret.iloc[0, 0], 1)
        self.assertEqual(fifof.df.shape[0], 1)
        #
        fifof = DriftQueue(
            {"x": int}, maxsize=10, clear_at_flush=False, only_flush_full=False
        )
        fifof.put(range(11))
        ret = fifof.flush()
        self.assertEqual(ret.iloc[0, 0], 1)
        self.assertEqual(fifof.df.shape[0], 10)
        #
        fifof = DriftQueue(
            {"x": int}, maxsize=1, clear_at_flush=False, only_flush_full=False
        )
        ret = fifof.flush()
        self.assertTrue(ret.empty)
        self.assertEqual(fifof.df.shape[0], 0)
        #
        fifof = DriftQueue(
            {"x": int}, maxsize=2, clear_at_flush=False, only_flush_full=False
        )
        fifof.put([1])
        ret = fifof.flush()
        self.assertEqual(ret.iloc[0, 0], 1)
        self.assertEqual(fifof.df.shape[0], 1)


import time
import datetime as dt


class TestConvertTime(unittest.TestCase):
    def test_time(self):
        self.assertIsInstance(convert_time_to_seconds(time.time()), float)

    def test_datetime(self):
        self.assertIsInstance(convert_time_to_seconds(dt.date(1, 1, 1)), float)
        self.assertIsInstance(convert_time_to_seconds(dt.time(1, 1, 1)), float)
        self.assertIsInstance(convert_time_to_seconds(dt.datetime.min), float)
        self.assertIsInstance(
            convert_time_to_seconds(dt.datetime(2022, 1, 1, 12, 4, 4)), float
        )
        self.assertIsInstance(
            convert_time_to_seconds(dt.datetime.max - dt.datetime.min), float
        )
        self.assertEqual(convert_time_to_seconds(dt.timedelta(seconds=1.2)), 1.2)

    def test_numpy(self):
        self.assertIsInstance(
            convert_time_to_seconds(np.datetime64("2022-01-01")), float
        )
        self.assertIsInstance(
            convert_time_to_seconds(
                np.datetime64("2022-01-01") - np.datetime64("2021-01-01")
            ),
            float,
        )
        self.assertEqual(convert_time_to_seconds(np.timedelta64(1, "s")), 1.0)

    def test_pandas(self):
        self.assertIsInstance(
            convert_time_to_seconds(pd.to_datetime("2022-01-01")), float
        )
        self.assertIsInstance(
            convert_time_to_seconds(
                pd.to_datetime("2022-01-01") - pd.to_datetime("2021-01-01")
            ),
            float,
        )
        self.assertIsInstance(convert_time_to_seconds(pd.Period("4Q2005")), float)

    def test_float_integer(self):
        self.assertEqual(convert_time_to_seconds(1), 1.0)
        self.assertEqual(convert_time_to_seconds(1.2), 1.2)

    def test_string_parse(self):
        # timestamp
        self.assertIsInstance(convert_time_to_seconds("2022-01-01"), float)
        self.assertIsInstance(convert_time_to_seconds("2022/01/01"), float)
        self.assertIsInstance(convert_time_to_seconds("01-01-2022"), float)
        self.assertIsInstance(convert_time_to_seconds("01/01/2022"), float)
        self.assertIsInstance(
            convert_time_to_seconds("01/01/2022", pd_str_parse_format="%d/%m/%Y"), float
        )
        # timedelta
        self.assertIsInstance(convert_time_to_seconds("1 days 06:05:01.00003"), float)
        # period
        self.assertIsInstance(convert_time_to_seconds("4Q2005"), float)
        self.assertIsInstance(
            convert_time_to_seconds("01-01-2022", pd_str_parse_format="%d/%m/%Y"), float
        )

    def test_error_handling(self):
        with self.assertRaises(ValueError):
            convert_time_to_seconds("this should raise an error!")
        with self.assertRaises(ValueError):
            convert_time_to_seconds(
                "01-01-2022",
                pd_str_parse_format="%d/%m/%Y",
                pd_infer_datetime_format=False,
            )
        with self.assertRaises(TypeError):
            convert_time_to_seconds(["this should raise an error"])
        with self.assertRaises(TypeError):
            convert_time_to_seconds({"as_should": "this"})

        self.assertIsInstance(
            convert_time_to_seconds({"as_should": "this"}, errors="ignore"), dict
        )
        self.assertTrue(
            np.isnan(convert_time_to_seconds({"as_should": "this"}, errors="coerce"))
        )

    def test_string_is_time(self):
        self.assertTrue(convert_time_to_seconds("2020-01-01"))
        self.assertTrue(convert_time_to_seconds("1d"))
        self.assertTrue(convert_time_to_seconds("2020/01/01"))
        with self.assertRaises(ValueError):
            convert_time_to_seconds("this is not time!")


from metrics import convert_metric_name_to_promql


class TestConvertName(unittest.TestCase):
    def test_illegal_character_removal(self):
        self.assertEqual(convert_metric_name_to_promql("te$st", int), "te_st")
        self.assertEqual(convert_metric_name_to_promql("test%", int), "test")
        self.assertEqual(convert_metric_name_to_promql("&test", int), "test")

    def test_extra_undescore_removal(self):
        self.assertEqual(convert_metric_name_to_promql("te_st", int), "te_st")
        self.assertEqual(convert_metric_name_to_promql("te__st", int), "te_st")
        self.assertEqual(convert_metric_name_to_promql("test_", int), "test")
        self.assertEqual(convert_metric_name_to_promql("test__", int), "test")
        self.assertEqual(convert_metric_name_to_promql("_test", int), "test")
        self.assertEqual(convert_metric_name_to_promql("__test", int), "test")

    def test_prefix(self):
        # normal
        self.assertEqual(
            convert_metric_name_to_promql("page_visit_time", dt.date, prefix="test"),
            "test_page_visit_time_timestamp_seconds",
        )
        # prefixing underscore removal
        self.assertEqual(
            convert_metric_name_to_promql("page_visit_time", dt.date, prefix="_test"),
            "test_page_visit_time_timestamp_seconds",
        )
        # extra underscore removal
        self.assertEqual(
            convert_metric_name_to_promql("page_visit_time", dt.date, prefix="test_"),
            "test_page_visit_time_timestamp_seconds",
        )
        # illegal character removal
        self.assertEqual(
            convert_metric_name_to_promql("page_visit_time", dt.date, prefix="test#"),
            "test_page_visit_time_timestamp_seconds",
        )

    def test_suffix(self):
        # normal
        self.assertEqual(
            convert_metric_name_to_promql("value_generated", int, suffix="euros"),
            "value_generated_euros",
        )
        # illegal character removal
        self.assertEqual(
            convert_metric_name_to_promql("value_generated", int, suffix="euros_€"),
            "value_generated_euros",
        )

    def test_timestamp(self):
        self.assertEqual(
            convert_metric_name_to_promql("page_visit_time", dt.date),
            "page_visit_time_timestamp_seconds",
        )
        self.assertEqual(
            convert_metric_name_to_promql("page_visit_time_timestamp", dt.datetime),
            "page_visit_time_timestamp_seconds",
        )
        self.assertEqual(
            convert_metric_name_to_promql("page_visit_timestamp_time", dt.time),
            "page_visit_time_timestamp_seconds",
        )
        self.assertEqual(
            convert_metric_name_to_promql(
                "page_visit_time_seconds_timestamp",
                value_dtypename(np.datetime64("2020-10-01")),
            ),
            "page_visit_time_timestamp_seconds",
        )

    def test_timedelta(self):
        self.assertEqual(
            convert_metric_name_to_promql("page_visit_duration", dt.timedelta),
            "page_visit_duration_seconds",
        )
        self.assertEqual(
            convert_metric_name_to_promql("page_visit_duration", dt.timedelta),
            "page_visit_duration_seconds",
        )
        self.assertEqual(
            convert_metric_name_to_promql("page_visit_duration", dt.timedelta),
            "page_visit_duration_seconds",
        )

    def test_string(self):
        self.assertEqual(
            convert_metric_name_to_promql("optimization_function", str),
            "optimization_function",
        )

    def test_remove_metric_types(self):
        self.assertEqual(
            convert_metric_name_to_promql("test_map", int), "test_maptypemask"
        )
        self.assertEqual(
            convert_metric_name_to_promql("test_map", int, mask_type_aliases=False),
            "test",
        )

    def test_remove_reserved_suffixes(self):
        convert_metric_name_to_promql("test_count", int)

        self.assertEqual(
            convert_metric_name_to_promql("test_count", int), "test_countsuffixmask"
        )
        self.assertEqual(
            convert_metric_name_to_promql("test_count_count", int),
            "test_count_countsuffixmask",
        )
        self.assertEqual(
            convert_metric_name_to_promql(
                "test_count_count", int, mask_reserved_suffixes=False
            ),
            "test",
        )
        # not removed from beginning or middle
        self.assertEqual(convert_metric_name_to_promql("count_test", int), "count_test")
        self.assertEqual(
            convert_metric_name_to_promql("test_count_test", int), "test_count_test"
        )

    def test_counter_suffix(self):
        self.assertEqual(convert_metric_name_to_promql("test", int), "test")
        self.assertEqual(
            convert_metric_name_to_promql("test_total", int),
            "test_totalsuffixmask",
        )
        self.assertEqual(
            convert_metric_name_to_promql("total_test", int),
            "total_test",
        )


from metrics import record_metrics_from_dict

from prometheus_client import Summary, Counter, Gauge, Enum, REGISTRY


def clean_registry():
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        REGISTRY.unregister(collector)


class TestRecordDict(unittest.TestCase):
    metrics = {
        "train_loss": {
            "value": 0.95,
            "description": "training loss (MSE)",
            "type": "numeric",
        },
        "test_loss": {
            "value": 0.96,
            "description": "test loss (MSE)",
            "type": "numeric",
        },
        "optimizer": {
            "value": np.random.choice(["SGD", "RMSProp", "Adagrad"]),
            "description": "ml model optimizer function",
            "type": "category",
            "categories": ["SGD", "RMSProp", "Adagrad", "Adam"],
        },
        "model_build": {
            "description": "dev information",
            "type": "info",
            "value": {
                "origin": "city-of-helsinki@github.com/ml-app",
                "branch": "main",
                "commit": "12345678",
            },
        },
        "model_update_time": {
            "value": dt.datetime.now(),
            "description": "model update workflow finish time",
            "type": "numeric",
        },
    }

    def test_metrics(self):
        clean_registry()
        m = record_metrics_from_dict(metrics=self.metrics)

        self.assertEqual(str(m[0]), "gauge:train_loss")

        self.assertEqual(str(m[2]), "stateset:optimizer")

        self.assertEqual(str(m[3]), "info:model_build")

        self.assertEqual(str(m[4]), "gauge:model_update_time_timestamp_seconds")

    def test_no_promql_convert(self):
        clean_registry()
        m = record_metrics_from_dict(
            metrics=self.metrics, convert_names_to_promql=False
        )

        self.assertEqual(str(m[4]), "gauge:model_update_time")


from metrics import SummaryStatisticsMetrics, is_numeric


class TestSummaryStatistics(unittest.TestCase):
    """
    Here it becomes a bit impractical to attempt through testing.
    These are sort of 'should not crash' tests, should be complemented by testing
    in use with real examples.
    """

    values1 = [
        [
            0.1,
            1,
            True,
            pd.Timestamp("2020-01-01"),
            pd.Series(["a", "b", "c", "a"], dtype="category").iloc[0],
            "string",
        ]
    ]
    df1 = pd.DataFrame(values1)
    df1[df1.columns[4]] = df1[df1.columns[4]].astype("category")

    # TODO: test using pandas util.testing.makeMizedDataFrame https://www.statology.org/pandas-sample-datasets/

    def test_init(self):
        clean_registry()
        ssm = SummaryStatisticsMetrics().calculate(self.df1).set_metrics()
        # print(self.df1.dtypes)
        # print([get_dtypename(tp) for tp in self.df1.dtypes])
        # print(ssm.get_sumstat().dtypes)
        ssm.get_metrics().keys()
        for key in ssm.get_metrics().keys():
            self.assertTrue(key in ssm.metrics.keys())

    def test_calculate_and_set(self):
        clean_registry()
        ssm = SummaryStatisticsMetrics()
        ssm.calculate(self.df1).set_metrics()
        # reset
        ssm.set_metrics()

    def test_non_equal_columns(self):
        clean_registry()
        # transform summary statistics so that columns do not match. Category information is lost
        ssm = SummaryStatisticsMetrics(summary_statistics_function=lambda x: x.T)
        ssm.calculate(self.df1).set_metrics()
        # reset
        ssm.set_metrics()

    def test_raw(self):
        # raw input instead of summary statistics. This should not be done in practice.
        clean_registry()
        ssm = SummaryStatisticsMetrics(summary_statistics_function=lambda x: x)
        ssm.calculate(self.df1).set_metrics()
        # reset
        ssm.set_metrics()


from metrics import DriftMonitor


class TestDriftMonitor(unittest.TestCase):
    def test_init(self):
        DriftMonitor(columns={"testcolumn": int})

    def test_update_metrics(self):
        clean_registry()
        monitor = DriftMonitor(columns={"testcolumn": int}, maxsize=1)
        monitor.put([[1]])
        monitor.update_metrics()

    def test_update_metrics_decorator(self):
        clean_registry()
        monitor = DriftMonitor(columns={"testcolumn": int}, maxsize=1)
        monitor.put([[1]])

        @monitor.update_metrics_decorator()
        def foo(param1: int):
            return "bar"

        self.assertEqual(foo(1), "bar")


from metrics import RequestMonitor


class TestRequestMonitor(unittest.TestCase):
    def test_init(self):
        RequestMonitor()

    def test_update_metrics_decorator(self):
        pass  # difficult to unit test
