"""Download and sanitize source records before they enter the analytical database."""
from __future__ import annotations

import hashlib
import logging
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

LOG = logging.getLogger(__name__)
SOURCE_URL = "https://zenodo.org/records/11112645/files/DataCoSupplyChainDataset.csv?download=1"
SOURCE_MD5 = "354eb3cd362619ef120ca2201337ae92"
MAPPING = {
    "Order Item Id": "item_id", "Order Id": "order_id", "Order Customer Id": "customer_id",
    "order date (DateOrders)": "ordered_at", "Shipping Mode": "shipping_mode", "Market": "market",
    "Order Region": "region", "Category Name": "category", "Customer Segment": "customer_segment",
    "Days for shipping (real)": "actual_days", "Days for shipment (scheduled)": "scheduled_days",
    "Late_delivery_risk": "late_flag", "Delivery Status": "delivery_status", "Order Status": "order_status",
    "Sales": "gross_sales", "Order Item Total": "net_sales", "Order Item Quantity": "quantity",
    "Order Profit Per Order": "recorded_profit",
}
NUMERIC = ["item_id", "order_id", "customer_id", "actual_days", "scheduled_days", "late_flag",
           "gross_sales", "net_sales", "quantity", "recorded_profit"]


def fingerprint(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def download(root: Path) -> Path:
    target = root / "data/raw/DataCoSupplyChainDataset.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        with target.open("rb") as handle:
            if hashlib.file_digest(handle, "md5").hexdigest() != SOURCE_MD5:
                raise ValueError("Cached source checksum mismatch; move it aside before retrying")
        return target
    temporary = target.with_suffix(".part")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(SOURCE_URL, timeout=120) as response, temporary.open("wb") as handle:
                while chunk := response.read(1024 * 1024):
                    handle.write(chunk)
            with temporary.open("rb") as handle:
                if hashlib.file_digest(handle, "md5").hexdigest() != SOURCE_MD5:
                    raise ValueError("Downloaded source checksum mismatch")
            temporary.replace(target)
            return target
        except (urllib.error.URLError, TimeoutError, OSError):
            LOG.warning("Source download failed on attempt %s", attempt + 1)
            if attempt == 2:
                raise
            time.sleep(attempt + 1)
    raise RuntimeError("Unreachable download state")


def read(path: Path) -> pd.DataFrame:
    # Whitelist excludes names, emails, passwords, street addresses, precise coordinates.
    return pd.read_csv(path, encoding="latin1", usecols=list(MAPPING)).rename(columns=MAPPING)


def validate(frame: pd.DataFrame) -> pd.DataFrame:
    missing = set(MAPPING.values()) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required fields: {sorted(missing)}")
    frame = frame[list(MAPPING.values())].copy()
    if frame.empty or frame.isna().any().any():
        raise ValueError("Empty input or missing fields")
    for field in NUMERIC:
        frame[field] = pd.to_numeric(frame[field], errors="raise")
    if not np.isfinite(frame[NUMERIC].to_numpy(dtype=float)).all():
        raise ValueError("Nonfinite numeric values")
    for field in ["item_id", "order_id", "customer_id", "quantity", "actual_days", "scheduled_days"]:
        if (frame[field] % 1 != 0).any():
            raise ValueError(f"Noninteger {field}")
        frame[field] = frame[field].astype(int)
    if (frame[["item_id", "order_id", "customer_id", "quantity"]] <= 0).any().any():
        raise ValueError("IDs and quantity must be positive")
    if (frame[["actual_days", "scheduled_days", "gross_sales", "net_sales"]] < 0).any().any():
        raise ValueError("Negative shipping days or sales")
    if not frame.late_flag.isin([0, 1]).all():
        raise ValueError("Late flag must be binary")
    if frame.item_id.duplicated().any():
        raise ValueError("Duplicate order-item IDs; resolve upstream rather than silently dropping")
    for field in ["shipping_mode", "market", "region", "category", "customer_segment",
                  "delivery_status", "order_status"]:
        frame[field] = frame[field].astype(str).str.strip()
        if frame[field].eq("").any():
            raise ValueError(f"Empty {field}")
    frame["ordered_at"] = pd.to_datetime(frame.ordered_at, format="mixed", errors="raise").dt.strftime("%Y-%m-%d %H:%M:%S")
    return frame
