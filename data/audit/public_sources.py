"""Bounded, explicit HTTPS audit of pinned public sources; no cloud SDK/query."""

import argparse
from collections import Counter, defaultdict
import csv
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import urllib.request

FOCUS_COMMIT = 'adbdd17a132984d6e8583c149c236d2199c3f5bc'
MICROSOFT_COMMIT = '3300217dd3b307f8b501aeb37ac5530c072fec3f'
GOOGLE_COMMIT = '48b12446464b0422abcc18e0ec5b0b13e2f3a90c'
MAX_BYTES = 2_000_000


def profile_csv(raw: bytes, *, date_column: str, date_format: str,
                cost_column: str, currency_column: str, service_column: str,
                provider_column: str | None = None) -> dict:
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    fields = reader.fieldnames or []
    if len(fields) != len(set(fields)):
        raise ValueError('duplicate CSV headers')
    required = {date_column, cost_column, currency_column, service_column}
    if provider_column:
        required.add(provider_column)
    if not required.issubset(fields):
        raise ValueError(f'missing required fields: {sorted(required - set(fields))}')
    rows = list(reader)
    if not rows:
        raise ValueError('empty CSV')
    dates, currencies, services = set(), set(), set()
    by_provider = defaultdict(lambda: {'rows': 0, 'days': set()})
    counts = Counter()
    nulls = {'', 'NULL', 'null', 'None'}
    for row in rows:
        if None in row or any(value is None for value in row.values()):
            raise ValueError('malformed CSV row')
        provider = row[provider_column] if provider_column else 'not_provided'
        by_provider[provider]['rows'] += 1
        try:
            day = datetime.strptime(row[date_column], date_format).date()
        except ValueError:
            counts['invalid_date_rows'] += 1
        else:
            dates.add(day)
            by_provider[provider]['days'].add(day)
        raw_cost = row[cost_column].strip()
        if raw_cost in nulls:
            counts['missing_cost_rows'] += 1
        else:
            try:
                cost = Decimal(raw_cost)
                if not cost.is_finite():
                    raise InvalidOperation
            except InvalidOperation:
                counts['invalid_cost_rows'] += 1
            else:
                counts['negative_cost_rows'] += int(cost < 0)
                counts['zero_cost_rows'] += int(cost == 0)
        if row[currency_column].strip() in nulls:
            counts['missing_currency_rows'] += 1
        else:
            currencies.add(row[currency_column])
        if row[service_column].strip() in nulls:
            counts['missing_service_rows'] += 1
        else:
            services.add(row[service_column])
    calendar = (max(dates) - min(dates)).days + 1 if dates else 0
    return dict(
        rows=len(rows), columns=len(fields), field_names=fields,
        duplicate_rows=len(rows) - len({tuple(r.items()) for r in rows}),
        **{name: counts[name] for name in ('invalid_date_rows', 'invalid_cost_rows',
           'missing_cost_rows', 'negative_cost_rows', 'zero_cost_rows',
           'missing_currency_rows', 'missing_service_rows')},
        date_start=min(dates).isoformat() if dates else None,
        date_end=max(dates).isoformat() if dates else None,
        distinct_days=len(dates), calendar_days=calendar,
        absent_day_fraction=(calendar - len(dates)) / calendar if calendar else None,
        coverage_definition='Absent calendar dates between observed min/max, globally; not evidence of complete billing or series coverage',
        currencies=sorted(currencies), service_count=len(services),
        providers={provider: dict(rows=item['rows'], distinct_days=len(item['days']),
                   date_start=min(item['days']).isoformat() if item['days'] else None,
                   date_end=max(item['days']).isoformat() if item['days'] else None)
                   for provider, item in sorted(by_provider.items())},
        null_count_by_column={key: sum(r[key].strip() in nulls for r in rows) for key in fields},
    )


def _fetch(url: str, cache: Path) -> tuple[bytes, dict]:
    # All URLs below are fixed public raw GitHub objects, with no credentials.
    request = urllib.request.Request(url, headers={'User-Agent': 'FinOps-Autopilot-B02-audit'})
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError(f'public source exceeds {MAX_BYTES} byte audit limit: {url}')
    if raw.startswith(b'version https://git-lfs.github.com/spec/'):
        raise ValueError(f'Git LFS pointer is not the dataset: {url}')
    digest = hashlib.sha256(raw).hexdigest()
    cache.mkdir(parents=True, exist_ok=True)
    (cache / digest).write_bytes(raw)
    return raw, dict(url=url, bytes=len(raw), sha256=digest)


def audit(cache: Path, audit_date: str) -> dict:
    date.fromisoformat(audit_date)
    bases = {
        'focus': f'https://raw.githubusercontent.com/FinOps-Open-Cost-and-Usage-Spec/FOCUS-Sample-Data/{FOCUS_COMMIT}/',
        'microsoft': f'https://raw.githubusercontent.com/microsoft/finops-toolkit/{MICROSOFT_COMMIT}/',
        'google': f'https://raw.githubusercontent.com/google/cluster-data/{GOOGLE_COMMIT}/',
    }
    candidates = []
    specs = [
        ('focus', 'FOCUS-1.0/focus_sample.csv', 'license.md', 'Creative Commons Attribution 4.0',
         'CC-BY-4.0', FOCUS_COMMIT, dict(date_column='ChargePeriodStart', date_format='%Y-%m-%d %H:%M:%S',
          cost_column='BilledCost', currency_column='BillingCurrency', service_column='ServiceName', provider_column='ProviderName')),
        ('microsoft', 'src/powershell/Tests/Unit/assets/EA_ActualCost_Small.csv', 'LICENSE', 'MIT License',
         'MIT', MICROSOFT_COMMIT, dict(date_column='Date', date_format='%m/%d/%Y',
          cost_column='Cost', currency_column='BillingCurrency', service_column='ConsumedService')),
    ]
    for name, path, license_path, marker, license_id, commit, fields in specs:
        license_raw, license_receipt = _fetch(bases[name] + license_path, cache)
        if marker not in license_raw.decode('utf-8-sig'):
            raise ValueError(f'license changed or not recognized: {name}')
        raw, data_receipt = _fetch(bases[name] + path, cache)
        profile = profile_csv(raw, **fields)
        candidates.append(dict(
            candidate=name, commit=commit, license=license_id, license_receipt=license_receipt,
            license_verified=True, content_verified=True, data_receipt=data_receipt,
            profile=profile, verdict='LIMITED',
            verdict_scope='Schema/edge-case exploration only; not accepted for forecast training or independent real-world validation',
            access_cost='Public HTTPS reads, no authenticated or paid API used',
        ))
    readme_raw, readme = _fetch(bases['google'] + 'README.md', cache)
    doc_raw, description = _fetch(bases['google'] + 'ClusterData2019.md', cache)
    schema_raw, schema = _fetch(bases['google'] + 'clusterdata_trace_format_v3.proto', cache)
    if b'creativecommons.org/licenses/by/4.0/' not in readme_raw + doc_raw:
        raise ValueError('Google CC-BY-4.0 license reference not found')
    candidates.append(dict(
        candidate='google_borg_2019', commit=GOOGLE_COMMIT, license='CC-BY-4.0',
        license_verified=True, content_verified=False, schema_verified=True,
        documents=[readme, description, schema], verdict='REJECTED',
        verdict_scope='Billed AWS cost forecasting; resource usage is not a monetary bill',
        documented_period='2019-05', documented_size='about 2.4 TiB compressed',
        observed_row_count=None, observed_missing_fraction=None,
        access_cost='Documentation fetched free over HTTPS; no BigQuery access or query executed; free full analysis not established',
        fields_note='Schema describes resource requests/usage; no AWS billed cost, currency or AWS service mapping established',
    ))
    return dict(
        audit_date=audit_date, audit_version='1.0',
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        source_policy='Pinned read-only HTTPS, maximum 2 MB per object; downloads cached outside tracked deliverables',
        candidates=candidates, external_validation='NOT_AVAILABLE',
        public_validation_status='PUBLIC_VALIDATION_NOT_FEASIBLE',
        conclusion_scope='Only the inspected candidates and samples; not a claim that no suitable public dataset exists',
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=Path('.cache/public-audit'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--audit-date', required=True)
    args = parser.parse_args()
    result = audit(args.cache, args.audit_date)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(dict(status='AUDITED', candidates=len(result['candidates']), output=str(args.output))))


if __name__ == '__main__':
    main()
