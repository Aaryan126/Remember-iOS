import importlib.util
from pathlib import Path
import unittest

s=importlib.util.spec_from_file_location('trace',Path(__file__).with_name('run.py'))
r=importlib.util.module_from_spec(s);s.loader.exec_module(r)

class TraceGateTests(unittest.TestCase):
    def value(self,control=False,deadline=False,code='ORBIT-27',passed=True,status='ok'):
        return {'status':status,'result':{'passed':passed,'watchdogControl':control,'deadlineFired':deadline,'code':code}}
    def test_valid_generation(self):r.check_result(self.value(),'generation')
    def test_timeout_cannot_pass(self):
        with self.assertRaises(ValueError):r.check_result(self.value(deadline=True),'generation')
    def test_wrong_code_cannot_pass(self):
        with self.assertRaises(ValueError):r.check_result(self.value(code='wrong'),'generation')
    def test_failed_native_result_stops(self):
        with self.assertRaises(ValueError):r.check_result(self.value(status='error',passed=False),'generation')
    def test_control_requires_actual_deadline(self):
        r.check_result(self.value(control=True,deadline=True,code=None),'watchdog-control')
        with self.assertRaises(ValueError):r.check_result(self.value(control=True),'watchdog-control')
    def test_control_cannot_substitute_for_generation(self):
        with self.assertRaises(ValueError):r.check_result(self.value(control=True,deadline=True),'generation')

if __name__=='__main__':unittest.main()
