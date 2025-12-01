import json
import unittest

from django.test.runner import DiscoverRunner


class JsonTestResult:
    def __init__(self):
        self.results = []

    def add_test(self, test, outcome):
        method = getattr(test, test._testMethodName, None)

        case_id = getattr(method, "test_case_id", None)

        self.results.append({
            "test_case_id": case_id,
            "test_name": test._testMethodName,
            "test_class": test.__class__.__name__,
            "outcome": outcome,
        })


class JsonTestRunner(DiscoverRunner):
    def run_suite(self, suite, **kwargs):
        self.json_result = JsonTestResult()
        return super().run_suite(suite, **kwargs)

    def get_resultclass(self):
        parent = super().get_resultclass()
        base = parent or unittest.TextTestResult

        runner = self

        class Result(base):
            def addSuccess(self, test):
                super().addSuccess(test)
                runner.json_result.add_test(test, "success")

            def addFailure(self, test, err):
                super().addFailure(test, err)
                runner.json_result.add_test(test, "failure")

            def addError(self, test, err):
                super().addError(test, err)
                runner.json_result.add_test(test, "error")

            def addSkip(self, test, reason):
                super().addSkip(test, reason)
                runner.json_result.add_test(test, "skipped")

        return Result

    def teardown_test_environment(self, **kwargs):
        super().teardown_test_environment(**kwargs)

        with open("result_test_auto.json", "w", encoding="utf-8") as f:
            json.dump(self.json_result.results, f, indent=2, ensure_ascii=False)
