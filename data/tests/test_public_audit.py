import importlib.util
import unittest


class PublicProfileTests(unittest.TestCase):
    def profile(self, raw):
        try:
            available = importlib.util.find_spec('data.audit.public_sources')
        except ModuleNotFoundError:
            available = None
        self.assertIsNotNone(available, 'Public profiler is not implemented')
        from data.audit.public_sources import profile_csv
        return profile_csv(raw, date_column='Date', date_format='%Y-%m-%d',
                           cost_column='Cost', currency_column='Currency',
                           service_column='Service', provider_column='Provider')

    def test_profile_preserves_credits_detects_gaps_nulls_and_duplicates(self):
        result = self.profile(b'Date,Cost,Currency,Service,Provider\n'
                              b'2024-01-01,10.25,USD,Compute,A\n'
                              b'2024-01-03,-2.00,USD,Compute,A\n'
                              b'2024-01-03,-2.00,USD,Compute,A\n'
                              b'2024-01-03,NULL,EUR,Storage,B\n')
        self.assertEqual(result['rows'],4)
        self.assertEqual(result['duplicate_rows'],1)
        self.assertEqual(result['negative_cost_rows'],2)
        self.assertEqual(result['missing_cost_rows'],1)
        self.assertEqual(result['currencies'],['EUR','USD'])
        self.assertEqual(result['date_start'],'2024-01-01')
        self.assertEqual(result['date_end'],'2024-01-03')
        self.assertEqual(result['distinct_days'],2)
        self.assertEqual(result['calendar_days'],3)
        self.assertAlmostEqual(result['absent_day_fraction'],1/3)
        self.assertEqual(result['providers']['A']['rows'],3)
        self.assertEqual(result['providers']['B']['distinct_days'],1)

    def test_invalid_dates_and_costs_are_reported_not_silently_imputed(self):
        result = self.profile(b'Date,Cost,Currency,Service,Provider\n'
                              b'not-a-date,NaN,USD,Compute,A\n'
                              b'2024-02-29,broken,,Compute,A\n')
        self.assertEqual(result['invalid_date_rows'],1)
        self.assertEqual(result['invalid_cost_rows'],2)
        self.assertEqual(result['missing_currency_rows'],1)
        self.assertEqual(result['distinct_days'],1)

    def test_empty_or_missing_schema_is_rejected(self):
        # The initial presence check is outside assertRaises: absent code must FAIL.
        self.profile(b'Date,Cost,Currency,Service,Provider\n2024-01-01,1,USD,A,A\n')
        for raw in (b'Date,Cost\n2024-01-01,1\n', b'Date,Cost,Currency,Service,Provider\n'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.profile(raw)

    def test_duplicate_headers_are_rejected_before_values_can_be_lost(self):
        self.profile(b'Date,Cost,Currency,Service,Provider\n2024-01-01,1,USD,A,A\n')
        with self.assertRaises(ValueError):
            self.profile(b'Date,Cost,Cost,Currency,Service,Provider\n'
                         b'2024-01-01,broken,10,USD,A,A\n')


if __name__ == '__main__':
    unittest.main()
