import json
import shutil
from pathlib import Path

from operations.pipeline import run
from operations.source import MAPPING


def test_end_to_end_replay_produces_same_business_totals(lines, tmp_path):
    (tmp_path / 'sql').mkdir()
    (tmp_path / 'dashboard').mkdir()
    shutil.copy(Path(__file__).resolve().parents[1] / 'sql/marts.sql', tmp_path / 'sql/marts.sql')
    source = tmp_path / 'source.csv'
    lines.rename(columns={v: k for k, v in MAPPING.items()}).to_csv(source, index=False)
    first = run(tmp_path, source_path=source, as_of='2017-01-20')
    second = run(tmp_path, source_path=source, as_of='2017-01-20')
    assert first['ingestion']['status'] == 'loaded'
    assert second['ingestion']['status'] == 'already_loaded'
    assert first['orders'] == second['orders'] == 3
    assert all(check['passed'] for check in second['checks'])
    payload = json.loads((tmp_path / 'dashboard/data.js').read_text().removeprefix('window.OPERATIONS = ').removesuffix(';'))
    assert payload['summary']['net_sales'] == 360
    assert not payload['report']['window']['label_mature']
    assert all(r['future_inactive_rate'] is None for r in payload['retention'])
