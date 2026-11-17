"""Versioned synthetic daily costs. Standard library only; never calls AWS."""

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path

VERSION = '1.0.0'
OBSERVATION_FIELDS = (
    'source_record_id', 'usage_start_time', 'usage_date', 'account_id',
    'service_name', 'region', 'cost_amount', 'currency', 'cost_basis',
    'charge_type', 'observation_status', 'data_source', 'dataset_label',
)
LABEL_FIELDS = (
    'source_record_id', 'usage_date', 'event_type', 'is_anomaly',
    'baseline_cost', 'injected_delta', 'data_source',
)


@dataclass(frozen=True)
class GeneratorConfig:
    seed: int = 42
    test_seed: int = 43
    start_date: str = '2025-01-01'
    months: int = 12
    accounts: tuple[str, ...] = ('demo-account-a', 'demo-account-b')
    services: tuple[str, ...] = ('AmazonEC2', 'AmazonS3', 'AmazonRDS')
    base_cost_cents: tuple[int, ...] = (10000, 2500, 7000)
    weekly_factors_bps: tuple[int, ...] = (10000, 10300, 10600, 10400, 10200, 8000, 7500)
    trend_bps_per_day: int = 3
    regime_day: int = 180
    regime_factor_bps: int = 12500
    noise_bps: int = 800
    missing_bps: int = 200
    credit_bps: int = 100
    anomaly_bps: int = 250
    anomaly_factor_bps: int = 25000
    train_fraction: str | float = '0.6'
    validation_fraction: str | float = '0.2'
    generation_reference_time: str = '2026-11-16T00:00:00Z'

    def validate(self) -> tuple[date, int, int, int]:
        integers = ('seed', 'test_seed', 'months', 'trend_bps_per_day', 'regime_day',
                    'regime_factor_bps', 'noise_bps', 'missing_bps', 'credit_bps',
                    'anomaly_bps', 'anomaly_factor_bps')
        for key in integers:
            value = getattr(self, key)
            if type(value) is not int or value < 0:
                raise ValueError(f'{key} must be a non-negative integer')
        if not 1 <= self.months <= 120 or self.test_seed == self.seed:
            raise ValueError('months must be 1..120 and test_seed must differ from seed')
        if self.noise_bps >= 10000 or self.anomaly_factor_bps <= 10000 or self.regime_factor_bps < 1:
            raise ValueError('invalid noise, anomaly or regime factor')
        if self.missing_bps + self.credit_bps + self.anomaly_bps > 10000:
            raise ValueError('event probabilities exceed 100 percent')
        for names in (self.accounts, self.services):
            if (not isinstance(names, (list, tuple)) or not names
                    or not all(isinstance(v, str) and v.strip() == v and v for v in names)
                    or len(set(names)) != len(names)):
                raise ValueError('accounts/services must contain unique nonempty names')
        for values, count in ((self.base_cost_cents, len(self.services)), (self.weekly_factors_bps, 7)):
            if (not isinstance(values, (list, tuple)) or len(values) != count
                    or any(type(v) is not int or v <= 0 for v in values)):
                raise ValueError('base costs and weekly factors must be positive integers of correct length')
        try:
            start = date.fromisoformat(self.start_date)
            timestamp = datetime.fromisoformat(self.generation_reference_time.replace('Z', '+00:00'))
            # Decimal(float) preserves binary error; Fraction(str(...)) preserves
            # the declared JSON decimal and is independent of Decimal context.
            train, validation = Fraction(str(self.train_fraction)), Fraction(str(self.validation_fraction))
            if (start.day != 1 or timestamp.utcoffset() != timedelta(0)
                    or not 0 < train < 1 or not 0 < validation < 1 or train + validation >= 1):
                raise ValueError('invalid dates or temporal split')
            month_index = start.year * 12 + start.month - 1 + self.months
            end = date(month_index // 12, month_index % 12 + 1, 1)
        except (ValueError, TypeError, AttributeError, ZeroDivisionError) as exc:
            raise ValueError('use first-of-month ISO start date, UTC reference time and valid fractions') from exc
        days = (end - start).days
        train_days, validation_days = int(days * train), int(days * validation)
        if min(train_days, validation_days, days - train_days - validation_days) < 1:
            raise ValueError('every split must contain at least one complete day')
        if days * len(self.accounts) * len(self.services) > 1_000_000:
            raise ValueError('local demo is limited to 1,000,000 daily observations')
        return start, days, train_days, validation_days


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + '\n').encode('utf-8')


def _draw(seed: int, day: str, account: str, service: str, purpose: str) -> int:
    key = json.dumps([VERSION, seed, day, account, service, purpose], separators=(',', ':'))
    return int.from_bytes(hashlib.sha256(key.encode('utf-8')).digest(), 'big')


def _money(cents: int) -> str:
    sign = '-' if cents < 0 else ''
    return f'{sign}{abs(cents) // 100}.{abs(cents) % 100:02d}'


def _csv_bytes(fields: tuple[str, ...], rows: list[dict]) -> bytes:
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode('utf-8')


def generate(config: GeneratorConfig, output: Path) -> dict:
    """Write a new, self-contained DEMO dataset; never overwrite an existing path."""
    start, days, train_days, validation_days = config.validate()
    output = Path(output)
    if output.exists():
        raise FileExistsError(f'output already exists: {output}')
    partitions = {name: [] for name in ('train', 'validation', 'test')}
    labels = {name: [] for name in partitions}
    for offset in range(days):
        current = start + timedelta(days=offset)
        day = current.isoformat()
        split = ('train' if offset < train_days else
                 'validation' if offset < train_days + validation_days else 'test')
        seed = config.test_seed if split == 'test' else config.seed
        for account_index, account in enumerate(config.accounts):
            for service_index, service in enumerate(config.services):
                cents = config.base_cost_cents[service_index] * (account_index + 1)
                cents = cents * (10000 + config.trend_bps_per_day * offset) // 10000
                cents = cents * config.weekly_factors_bps[current.weekday()] // 10000
                if offset >= config.regime_day:
                    cents = cents * config.regime_factor_bps // 10000
                noise = _draw(seed, day, account, service, 'noise') % (2 * config.noise_bps + 1) - config.noise_bps
                baseline = max(1, cents * (10000 + noise) // 10000)
                draw = _draw(seed, day, account, service, 'event') % 10000
                amount, kind = baseline, 'normal'
                if draw < config.missing_bps:
                    amount, kind = None, 'missing'
                elif draw < config.missing_bps + config.credit_bps:
                    amount, kind = -max(1, baseline // 4), 'credit'
                elif draw < config.missing_bps + config.credit_bps + config.anomaly_bps:
                    amount, kind = max(baseline + 1, baseline * config.anomaly_factor_bps // 10000), 'spike'
                record = 'synthetic-' + format(_draw(seed, day, account, service, 'id'), '064x')
                partitions[split].append(dict(
                    source_record_id=record, usage_start_time=f'{day}T00:00:00Z',
                    usage_date=day, account_id=account, service_name=service, region='demo-region',
                    cost_amount='' if amount is None else _money(amount), currency='USD',
                    cost_basis='unblended', charge_type='Credit' if kind == 'credit' else 'Usage',
                    observation_status='missing' if amount is None else 'observed',
                    data_source='synthetic', dataset_label='DEMO',
                ))
                labels[split].append(dict(
                    source_record_id=record, usage_date=day, event_type=kind,
                    is_anomaly='true' if kind == 'spike' else 'false',
                    baseline_cost=_money(baseline),
                    injected_delta='' if amount is None else _money(amount - baseline),
                    data_source='synthetic',
                ))
    payloads, file_info, split_info = {}, {}, {}
    for split, rows in partitions.items():
        split_info[split] = dict(
            start_date=rows[0]['usage_date'], end_date=rows[-1]['usage_date'],
            rows=len(rows), random_seed=config.test_seed if split == 'test' else config.seed,
            events={kind: sum(r['event_type'] == kind for r in labels[split])
                    for kind in ('normal', 'missing', 'credit', 'spike')},
        )
        for name, fields, values in ((f'{split}.csv', OBSERVATION_FIELDS, rows),
                                    (f'{split}_labels.csv', LABEL_FIELDS, labels[split])):
            raw = _csv_bytes(fields, values)
            payloads[name] = raw
            file_info[name] = dict(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw), rows=len(values))
    manifest = dict(
        schema_version='synthetic-costs/1.0', generator_version=VERSION,
        generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        dataset_id=hashlib.sha256(_json_bytes(asdict(config))).hexdigest(),
        data_source='synthetic', dataset_label='DEMO',
        provenance='FinOps Autopilot deterministic local simulator; no real billing data',
        license='CC0-1.0 (generated synthetic data only; not repository code)',
        generation_reference_time=config.generation_reference_time,
        reference_time_semantics='Caller-declared reproducibility metadata, not observed execution time',
        parameters=asdict(config),
        period=dict(start_date=start.isoformat(), end_date=(start + timedelta(days=days-1)).isoformat(), days=days),
        method='Integer cents; SHA-256 keyed draws; daily trend, weekly factors, step regime, noise and disjoint events',
        cost_basis_note='unblended is a synthetic demo assumption only; G02 remains open for real sources',
        external_validation='NOT_AVAILABLE', public_validation_status='PUBLIC_VALIDATION_NOT_FEASIBLE',
        test_scope='Chronological synthetic holdout with distinct random seed; same simulator, not external validation',
        observation_schema={field: ('decimal(2), nullable for missing' if field == 'cost_amount' else
                                   'date ISO-8601' if field == 'usage_date' else 'string') for field in OBSERVATION_FIELDS},
        label_schema={field: 'string' for field in LABEL_FIELDS},
        splits=split_info, files=file_info,
        limitations=['No AWS prices or validated ML performance',
                     'No observed zero implied by missing amount',
                     'Labels and baseline costs must never be model inputs',
                     'Test data must not guide tuning; report only final evaluation'],
    )
    # The manifest is the completion marker and is written last.
    output.mkdir(parents=True, exist_ok=False)
    for name, raw in payloads.items():
        (output / name).write_bytes(raw)
    (output / 'dataset_manifest.json').write_bytes(_json_bytes(manifest))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        config = GeneratorConfig(**json.loads(args.config.read_text(encoding='utf-8')))
        manifest = generate(config, args.output)
    except (ValueError, TypeError, OSError) as exc:
        parser.exit(2, f'Generation refused: {exc}\n')
    print(json.dumps(dict(status='GENERATED', data_source='synthetic', dataset_label='DEMO',
                          rows=sum(s['rows'] for s in manifest['splits'].values()),
                          manifest=str(args.output / 'dataset_manifest.json'))))


if __name__ == '__main__':
    main()
