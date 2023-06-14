from datetime import datetime

from amocrm.v2.entity.custom_field import BaseCustomField
from amocrm.v2.fields import _DateTimeField


def on_set_date_field(self, value):
    if isinstance(value, datetime):
        return int(value.timestamp())


def _get_raw_field(self, data):
    if data is None:
        return None
    for field in data:
        if self._field_id and field.get("field_id", "") == self._field_id:
            return field
        if field.get("field_name", "error") == self._name:
            return field
        if self._code and field.get("field_code") == self._code:
            return field
    return None


def patch():
    _DateTimeField.on_set = on_set_date_field
    BaseCustomField._get_raw_field = _get_raw_field
