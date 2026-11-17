"""Behavioral checks for B02; no cloud or third-party dependencies."""

import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from decimal import Decimal, localcontext


class SyntheticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.available = importlib.util.find_spec('data.generators.synthetic')
        except ModuleNotFoundError:
            cls.available = None

    def api(self):
        self.assertIsNotNone(self.available, 'B02 generator is not implemented')
        from data.generators.synthetic import GeneratorConfig, generate
        return GeneratorConfig, generate

    def read(self, folder, name):
        with (folder / name).open(encoding='utf-8', newline='') as stream:
            return list(csv.DictReader(stream))

    def test_reproducible_artifacts_hashes_and_seed_sensitivity(self):
        Config, generate = self.api()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generate(Config(), root/'a')
            generate(Config(), root/'b')
            generate(replace(Config(), seed=99), root/'c')
            for path in (root/'a').iterdir():
                self.assertEqual(path.read_bytes(), (root/'b'/path.name).read_bytes())
            self.assertNotEqual((root/'a/train.csv').read_bytes(), (root/'c/train.csv').read_bytes())
            manifest = json.loads((root/'a/dataset_manifest.json').read_text())
            for name, entry in manifest['files'].items():
                raw = (root/'a'/name).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), entry['sha256'])
                self.assertEqual(len(raw), entry['bytes'])
                self.assertEqual(len(self.read(root/'a',name)), entry['rows'])
            self.assertEqual(manifest['data_source'], 'synthetic')
            self.assertEqual(manifest['external_validation'], 'NOT_AVAILABLE')

    def test_full_calendar_split_and_labels_are_separate(self):
        Config, generate = self.api()
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)/'demo'
            generate(Config(), folder)
            expected = {'train':(1314,'2025-01-01','2025-08-07'),
                        'validation':(438,'2025-08-08','2025-10-19'),
                        'test':(438,'2025-10-20','2025-12-31')}
            seen = set()
            for split,(count,start,end) in expected.items():
                rows = self.read(folder,f'{split}.csv')
                self.assertEqual(len(rows),count)
                dates = [r['usage_date'] for r in rows]
                self.assertEqual(min(dates),start)
                self.assertEqual(max(dates),end)
                self.assertTrue(seen.isdisjoint(dates))
                seen.update(dates)
                self.assertEqual({r['data_source'] for r in rows},{'synthetic'})
                self.assertEqual({r['currency'] for r in rows},{'USD'})
                self.assertEqual(len({r['source_record_id'] for r in rows}),count)
                self.assertNotIn('is_anomaly',rows[0])
                self.assertNotIn('baseline_cost',rows[0])
                labels = self.read(folder,f'{split}_labels.csv')
                self.assertEqual({r['source_record_id'] for r in rows},
                                 {r['source_record_id'] for r in labels})
            self.assertEqual(len(seen),365)

    def test_injections_missing_and_credits_are_traceable(self):
        Config, generate = self.api()
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)/'demo'
            generate(Config(),folder)
            for split in ('train','validation','test'):
                rows = self.read(folder,f'{split}.csv')
                labels = {r['source_record_id']:r for r in self.read(folder,f'{split}_labels.csv')}
                counts = {'missing':0,'credit':0,'spike':0}
                for row in rows:
                    label = labels[row['source_record_id']]
                    kind = label['event_type']
                    if kind in counts:
                        counts[kind] += 1
                    if kind == 'missing':
                        self.assertEqual(row['cost_amount'],'')
                        self.assertEqual(row['observation_status'],'missing')
                        self.assertEqual(label['is_anomaly'],'false')
                    else:
                        self.assertEqual(row['observation_status'],'observed')
                        amount=Decimal(row['cost_amount'])
                        self.assertEqual(amount,Decimal(label['baseline_cost'])+Decimal(label['injected_delta']))
                        self.assertEqual(amount<0,kind=='credit')
                        self.assertEqual(label['is_anomaly']=='true',kind=='spike')
                        if kind=='spike':
                            self.assertGreater(amount,Decimal(label['baseline_cost']))
                self.assertTrue(all(count>0 for count in counts.values()),counts)

    def test_holdout_seed_changes_only_test_observations(self):
        Config,generate=self.api()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            generate(Config(),root/'a')
            generate(replace(Config(),test_seed=9876),root/'b')
            for name in ('train.csv','validation.csv','train_labels.csv','validation_labels.csv'):
                self.assertEqual((root/'a'/name).read_bytes(),(root/'b'/name).read_bytes())
            self.assertNotEqual((root/'a/test.csv').read_bytes(),(root/'b/test.csv').read_bytes())

    def test_leap_year_and_invalid_configuration_preserve_destination(self):
        Config,generate=self.api()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            generate(replace(Config(),start_date='2024-01-01'),root/'leap')
            rows=sum((self.read(root/'leap',f'{s}.csv') for s in ('train','validation','test')),[])
            self.assertEqual(len(rows),2196)
            self.assertEqual(sum(r['usage_date']=='2024-02-29' for r in rows),6)
            invalid = [dict(months=0),dict(months=True),dict(seed=True),dict(test_seed=42),
                       dict(start_date='2025-01-02'),dict(missing_bps=-1),dict(anomaly_bps=10001),
                       dict(missing_bps=9000,credit_bps=9000),dict(noise_bps=10000),
                       dict(accounts=('demo-a','demo-a')),dict(services=()),
                       dict(train_fraction='0.9',validation_fraction='0.2'),
                       dict(generation_reference_time='yesterday')]
            for kwargs in invalid:
                with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):
                    generate(replace(Config(),**kwargs),root/'invalid')
                self.assertFalse((root/'invalid').exists())
            before={p.name:p.read_bytes() for p in (root/'leap').iterdir()}
            with self.assertRaises(FileExistsError):
                generate(Config(),root/'leap')
            self.assertEqual(before,{p.name:p.read_bytes() for p in (root/'leap').iterdir()})

    def test_cli_runs_offline_with_example_config_and_refuses_overwrite(self):
        self.api()
        with tempfile.TemporaryDirectory() as tmp:
            output=str(Path(tmp)/'demo')
            cmd=[sys.executable,'-m','data.generators.synthetic','--config',
                 'data/generators/demo_config.json','--output',output]
            first=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(first.returncode,0,first.stderr)
            self.assertTrue((Path(output)/'dataset_manifest.json').exists())
            again=subprocess.run(cmd,capture_output=True,text=True)
            self.assertNotEqual(again.returncode,0)

    def test_numeric_json_fractions_have_the_same_day_boundaries(self):
        Config,generate=self.api()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            generate(Config(),root/'strings')
            generate(replace(Config(),train_fraction=0.6,validation_fraction=0.2),root/'numbers')
            for name in ('train.csv','validation.csv','test.csv'):
                self.assertEqual((root/'strings'/name).read_bytes(),(root/'numbers'/name).read_bytes())

    def test_ambient_decimal_precision_cannot_change_dataset(self):
        Config,generate=self.api()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            generate(Config(),root/'normal')
            with localcontext() as context:
                context.prec=3
                generate(Config(),root/'low_precision')
            for path in (root/'normal').iterdir():
                self.assertEqual(path.read_bytes(),(root/'low_precision'/path.name).read_bytes())


if __name__ == '__main__':
    unittest.main()
