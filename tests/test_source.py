import pandas as pd
import pytest

from operations.source import MAPPING, read, validate


@pytest.mark.parametrize('field,value', [('item_id', 1.5), ('quantity', 0), ('actual_days', -1),
                                         ('net_sales', -1), ('late_flag', 2),
                                         ('gross_sales', float('inf')), ('market', '')])
def test_invalid_data_fails_closed(lines, field, value):
    if isinstance(value, float):
        lines[field] = lines[field].astype(float)
    lines.loc[0, field] = value
    with pytest.raises(ValueError):
        validate(lines)


def test_duplicate_item_rejected(lines):
    with pytest.raises(ValueError, match='Duplicate'):
        validate(pd.concat([lines, lines.iloc[:1]]))


def test_negative_profit_is_valid(lines):
    assert validate(lines).recorded_profit.sum() == -20


def test_personal_fields_never_loaded(lines, tmp_path):
    frame = lines.rename(columns={v: k for k, v in MAPPING.items()})
    frame['Customer Email'] = 'private@example.test'
    frame['Customer Password'] = 'masked'
    target = tmp_path / 'source.csv'
    frame.to_csv(target, index=False)
    clean = validate(read(target))
    assert set(clean.columns) == set(MAPPING.values())
    assert not any('email' in c.lower() or 'password' in c.lower() for c in clean.columns)


def test_bad_date_rejected(lines):
    lines.loc[0, 'ordered_at'] = 'not-a-date'
    with pytest.raises(ValueError):
        validate(lines)
