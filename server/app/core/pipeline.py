"""Production-oriented data cleaning and feature-engineering pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd

from app.core.constants import (
    CITY_VARIATION_MAP,
    COLUMN_ALIASES,
    DEFAULT_NUMERIC_IMPUTATIONS,
    DEFAULT_STRING_IMPUTATIONS,
    FAILED_STATUSES,
    PATTERN_COLUMNS,
)


@dataclass
class FraudFeatureEngineer:
    """Load a transactional CSV, normalize it, and engineer fraud features."""

    csv_path: str

    def run(self) -> Tuple[pd.DataFrame, Dict[str, Dict[str, int]]]:
        """Execute the full cleaning and feature engineering workflow."""
        dataframe = self._load_dataframe()
        dataframe = self.run_pipeline(dataframe)
        summary = self._build_summary(dataframe)
        self._print_summary(summary)
        return dataframe, summary

    def run_pipeline(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Run the reusable dataframe-to-dataframe pipeline."""
        dataframe = self._normalize_schema(dataframe)
        dataframe = self._clean_core_fields(dataframe)
        dataframe = self._build_user_features(dataframe)
        dataframe = self._build_velocity_features(dataframe)
        dataframe = self._build_sequence_features(dataframe)
        dataframe = self._build_network_features(dataframe)
        dataframe = self._build_risk_features(dataframe)
        dataframe = self._build_advanced_features(dataframe)
        dataframe = self._build_stage_three_features(dataframe)
        dataframe = self._build_pattern_flags(dataframe)
        return dataframe

    def _load_dataframe(self) -> pd.DataFrame:
        """Read the source CSV once with pandas' default engine."""
        return pd.read_csv(self.csv_path, low_memory=False)

    def _normalize_schema(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Project source aliases into a stable backend schema and preserve raw values."""
        dataframe = dataframe.copy()
        dataframe.columns = [str(column).strip().lower() for column in dataframe.columns]
        dataframe = self._coalesce_alias_columns(dataframe)

        for column, default_value in DEFAULT_STRING_IMPUTATIONS.items():
            if column not in dataframe.columns:
                dataframe[column] = default_value

        for column, default_value in DEFAULT_NUMERIC_IMPUTATIONS.items():
            if column not in dataframe.columns:
                dataframe[column] = default_value

        raw_columns = [
            "transaction_id",
            "user_id",
            "device_id",
            "device_type",
            "payment_method",
            "merchant_category",
            "user_location",
            "merchant_location",
            "status",
            "timestamp",
            "transaction_amount",
            "amt",
            "ip_address",
            "account_balance",
            "fraud_label",
            "fraud_reason",
        ]

        for column in raw_columns:
            if column not in dataframe.columns:
                dataframe[column] = ""
            dataframe[f"raw_{column}"] = dataframe[column]

        return dataframe

    def _clean_core_fields(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Standardize raw fields into canonical backend-friendly columns."""
        dataframe["transaction_id"] = self._normalize_identifier(
            dataframe["transaction_id"],
            prefix="txn",
            default_value="txn_unknown",
        )
        dataframe["user_id"] = self._normalize_identifier(
            dataframe["user_id"],
            prefix="usr",
            default_value="usr_unknown",
        )
        dataframe["device_id"] = self._normalize_device_id(dataframe["device_id"])
        dataframe["device_type"] = self._normalize_device_type(dataframe["device_type"])
        dataframe["payment_method"] = self._normalize_payment_method(dataframe["payment_method"])
        dataframe["merchant_category"] = self._normalize_merchant_category(dataframe["merchant_category"])
        dataframe["status"] = self._normalize_status(dataframe["status"])

        dataframe["timestamp"] = self._normalize_placeholder_strings(
            dataframe["timestamp"],
            "1970-01-01 00:00:00",
        )
        dataframe["standardized_timestamp"] = self._parse_timestamp_series(dataframe["timestamp"])

        dataframe["user_location"] = self._normalize_placeholder_strings(dataframe["user_location"], "unknown_city")
        dataframe["merchant_location"] = self._normalize_placeholder_strings(dataframe["merchant_location"], "unknown_city")
        dataframe["canonical_city"] = self._normalize_city_series(dataframe["user_location"])
        dataframe["merchant_canonical_city"] = self._normalize_city_series(dataframe["merchant_location"])

        dataframe["transaction_amount"] = self._normalize_placeholder_strings(dataframe["transaction_amount"], "0")
        dataframe["amt"] = self._normalize_placeholder_strings(dataframe["amt"], "0")
        dataframe["clean_amount"] = self._normalize_amount(dataframe["transaction_amount"], dataframe["amt"])
        dataframe["account_balance"] = self._normalize_numeric_series(dataframe["account_balance"], default_value=0.0)
        dataframe["ip_address"] = self._normalize_ip_address(dataframe["ip_address"])

        dataframe = dataframe.sort_values(["user_id", "standardized_timestamp", "transaction_id"]).reset_index(drop=True)
        return dataframe

    def _build_user_features(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Derive user baseline behavior once the dataset is standardized."""
        dataframe["user_avg_spend"] = dataframe.groupby("user_id")["clean_amount"].transform("mean").fillna(0.0)
        dataframe["spend_deviation"] = np.where(
            dataframe["user_avg_spend"] > 0,
            (dataframe["clean_amount"] - dataframe["user_avg_spend"]) / dataframe["user_avg_spend"],
            0.0,
        )
        dataframe["is_new_device"] = (~dataframe.duplicated(subset=["user_id", "device_id"])).astype(np.int8)
        return dataframe

    def _build_velocity_features(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Measure transaction concentration over short windows."""
        dataframe["txn_count_1min"] = self._rolling_count(dataframe, "user_id", "60s")
        dataframe["txn_count_1h"] = self._rolling_count(dataframe, "user_id", "1h")
        dataframe["time_diff"] = (
            dataframe.groupby("user_id")["standardized_timestamp"].diff().dt.total_seconds().fillna(999999.0)
        )
        return dataframe

    def _build_sequence_features(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Capture prior outcome context and consecutive failures."""
        dataframe["prev_status"] = dataframe.groupby("user_id")["status"].shift(1).fillna("no_previous_status")
        dataframe["consecutive_failures"] = self._compute_consecutive_failures(dataframe["user_id"], dataframe["status"])
        return dataframe

    def _build_network_features(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Track shared infrastructure signals across users."""
        dataframe["device_user_degree"] = dataframe.groupby("device_id")["user_id"].transform("nunique").astype(int)
        dataframe["ip_velocity_all_users"] = self._rolling_count(dataframe, "ip_address", "1h")
        dataframe["ip_user_degree"] = dataframe.groupby("ip_address")["user_id"].transform("nunique").astype(int)
        return dataframe

    def _build_risk_features(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Assemble high-risk spending and behavior indicators."""
        failed_mask = dataframe["status"].isin(FAILED_STATUSES).astype(np.int8)
        dataframe["is_micro_transaction"] = (dataframe["clean_amount"] < 10).astype(np.int8)
        dataframe["failed_to_success_ratio_1h"] = self._rolling_sum(
            dataframe.assign(_failed_flag=failed_mask),
            "user_id",
            "1h",
            "_failed_flag",
        ) / dataframe["txn_count_1h"].replace(0, 1)
        dataframe["payment_method_entropy_10m"] = self._rolling_unique_count(
            dataframe,
            "user_id",
            "10min",
            "payment_method",
        )
        return dataframe

    def _build_advanced_features(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Create balance-sensitive features when balance data is present."""
        dataframe["balance_depletion_ratio"] = np.where(
            dataframe["account_balance"] > 0,
            dataframe["clean_amount"] / dataframe["account_balance"],
            0.0,
        )
        dataframe["post_txn_balance_danger"] = dataframe["account_balance"] - dataframe["clean_amount"]
        dataframe["amount_to_balance_ratio"] = dataframe["balance_depletion_ratio"]
        return dataframe

    def _build_stage_three_features(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Add training-oriented features derived from the cleaned dataset."""
        dataframe["is_cross_city"] = (
            dataframe["canonical_city"].astype(str).str.lower().str.strip()
            != dataframe["merchant_canonical_city"].astype(str).str.lower().str.strip()
        ).astype(np.int8)

        dataframe["hour"] = dataframe["standardized_timestamp"].dt.hour.fillna(12).astype(int)
        dataframe["is_odd_hour"] = dataframe["hour"].between(0, 4, inclusive="both").astype(np.int8)
        dataframe["is_post_failure_success"] = (
            (dataframe["status"] == "success") & (dataframe["consecutive_failures"] >= 3)
        ).astype(np.int8)

        positive_spend_deviation = dataframe["spend_deviation"].clip(lower=0)
        short_burst_signal = (dataframe["txn_count_1min"] / 5.0).clip(lower=0, upper=3)
        hourly_burst_signal = (dataframe["txn_count_1h"] / 20.0).clip(lower=0, upper=3)
        device_signal = ((dataframe["device_user_degree"] - 1) / 3.0).clip(lower=0, upper=3)
        ip_signal = ((dataframe["ip_user_degree"] - 1) / 4.0).clip(lower=0, upper=3)
        failure_signal = dataframe["consecutive_failures"].clip(lower=0, upper=5) / 5.0
        odd_hour_signal = dataframe["is_odd_hour"].astype(float)
        cross_city_signal = dataframe["is_cross_city"].astype(float)
        recovery_signal = dataframe["is_post_failure_success"].astype(float)

        anomaly_components = (
            positive_spend_deviation
            + short_burst_signal
            + hourly_burst_signal
            + device_signal
            + ip_signal
            + failure_signal
            + odd_hour_signal
            + cross_city_signal
            + recovery_signal
        )
        dataframe["anomaly_score"] = (anomaly_components / 9.0).round(4)
        return dataframe

    def _build_pattern_flags(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Translate business-friendly fraud heuristics into binary pattern flags."""
        dataframe["pattern_location_mismatch"] = dataframe["is_cross_city"].astype(np.int8)
        dataframe["pattern_high_amount_vs_balance"] = dataframe["amount_to_balance_ratio"].between(0.9, 1.5).astype(
            np.int8
        )
        dataframe["pattern_unknown_device"] = (
            (dataframe["device_id"] == "UNKNOWN_DEVICE") | (dataframe["is_new_device"] == 1)
        ).astype(np.int8)
        dataframe["pattern_failed_high_value"] = (
            dataframe["status"].isin(FAILED_STATUSES) & (dataframe["clean_amount"] > 5000)
        ).astype(np.int8)
        dataframe["pattern_ip_risk"] = (
            (dataframe["ip_address"] == "0.0.0.0")
            | (dataframe["ip_user_degree"] > 3)
            | (dataframe["ip_velocity_all_users"] > 10)
        ).astype(np.int8)
        dataframe["pattern_velocity"] = (
            (dataframe["txn_count_1min"] > 8)
            | ((dataframe["txn_count_1h"] > 25) & (dataframe["time_diff"] < 5))
        ).astype(np.int8)
        dataframe["pattern_post_failure_success"] = dataframe["is_post_failure_success"].astype(np.int8)
        dataframe["pattern_odd_hour_transaction"] = (
            (dataframe["is_odd_hour"] == 1)
            & (
                (dataframe["clean_amount"] >= 5000)
                | (dataframe["is_cross_city"] == 1)
                | (dataframe["pattern_unknown_device"] == 1)
                | (dataframe["pattern_ip_risk"] == 1)
            )
        ).astype(np.int8)
        dataframe["fraud_label"] = dataframe[PATTERN_COLUMNS].max(axis=1).astype(np.int8)
        dataframe["fraud_reason"] = dataframe[PATTERN_COLUMNS].apply(
            lambda row: "; ".join(column for column, value in row.items() if value),
            axis=1,
        ).replace("", "no_rule_triggered")
        return dataframe

    def _build_summary(self, dataframe: pd.DataFrame) -> Dict[str, Dict[str, int]]:
        """Summarize final fraud labels and active fraud patterns."""
        fraud_counts = dataframe["fraud_label"].value_counts(dropna=False).reindex([0, 1], fill_value=0)
        pattern_counts = {column: int(dataframe[column].sum()) for column in PATTERN_COLUMNS}
        return {
            "fraud_label_counts": {
                "non_fraud": int(fraud_counts.loc[0]),
                "fraud": int(fraud_counts.loc[1]),
            },
            "pattern_counts": pattern_counts,
        }

    def _print_summary(self, summary: Dict[str, Dict[str, int]]) -> None:
        """Print compact job summary lines suitable for backend logs."""
        print("Fraud vs Non-Fraud Counts:")
        print(summary["fraud_label_counts"])
        print("Pattern Counts:")
        print(summary["pattern_counts"])

    @staticmethod
    def _coalesce_alias_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
        """Backfill known alias columns into canonical names used downstream."""
        for target_column, candidates in COLUMN_ALIASES.items():
            available = [column for column in candidates if column in dataframe.columns]
            if not available:
                continue
            dataframe[target_column] = dataframe[available].bfill(axis=1).iloc[:, 0]
        return dataframe

    @staticmethod
    def _normalize_placeholder_strings(series: pd.Series, default_value: str) -> pd.Series:
        """Replace dirty placeholders with a stable default token."""
        normalized = series.fillna(default_value).astype(str).str.strip()
        invalid_tokens = {"", "nan", "none", "null", "n/a", "na", "missing", "unknown"}
        return normalized.mask(normalized.str.lower().isin(invalid_tokens), default_value)

    @staticmethod
    def _normalize_identifier(series: pd.Series, prefix: str, default_value: str) -> pd.Series:
        """Standardize identifier columns while keeping only safe characters."""
        normalized = (
            series.fillna(default_value)
            .astype(str)
            .str.strip()
            .str.lower()
            .str.replace(r"[^a-z0-9\-]", "", regex=True)
            .str.replace(r"-{2,}", "-", regex=True)
            .str.strip("-")
        )
        normalized = normalized.mask(normalized.eq(""), default_value)
        return np.where(
            normalized.str.startswith(prefix),
            normalized,
            f"{prefix}_" + normalized,
        )

    @staticmethod
    def _normalize_device_id(series: pd.Series) -> pd.Series:
        """Standardize device identifiers and collapse malformed values."""
        normalized = (
            series.fillna("unknown_device")
            .astype(str)
            .str.strip()
            .str.upper()
            .str.replace(r"[^A-Z0-9\-]", "", regex=True)
            .str.replace(r"-{2,}", "-", regex=True)
            .str.strip("-")
        )
        valid_pattern = r"^(DEV|ATO|CNP|NEW)-[A-Z0-9]{6,10}$"
        return normalized.where(normalized.str.match(valid_pattern), "UNKNOWN_DEVICE")

    @staticmethod
    def _normalize_device_type(series: pd.Series) -> pd.Series:
        """Map device channels into a small canonical set."""
        normalized = FraudFeatureEngineer._normalize_placeholder_strings(series, "unknown_device_type").str.lower()
        return np.select(
            [
                normalized.str.contains("mobile", regex=False),
                normalized.str.contains("web", regex=False),
                normalized.str.contains("atm", regex=False),
            ],
            ["mobile", "web", "atm"],
            default="unknown_device_type",
        )

    @staticmethod
    def _normalize_payment_method(series: pd.Series) -> pd.Series:
        """Canonicalize payment method drift into a consistent set."""
        normalized = FraudFeatureEngineer._normalize_placeholder_strings(series, "unknown_payment_method").str.lower()
        return np.select(
            [
                normalized.str.contains("upi", regex=False),
                normalized.str.contains("card", regex=False),
                normalized.str.contains("wallet", regex=False),
                normalized.str.contains("net", regex=False),
            ],
            ["upi", "card", "wallet", "netbanking"],
            default="unknown_payment_method",
        )

    @staticmethod
    def _normalize_merchant_category(series: pd.Series) -> pd.Series:
        """Reduce messy category text to a controlled vocabulary."""
        normalized = (
            FraudFeatureEngineer._normalize_placeholder_strings(series, "unknown_merchant_category")
            .str.lower()
            .str.replace(r"[^a-z& ]", "", regex=True)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )

        conditions = [
            normalized.str.contains("elect", regex=False),
            normalized.str.contains("util", regex=False),
            normalized.str.contains("travel", regex=False) | normalized.eq("t"),
            normalized.str.contains("cloth", regex=False) | normalized.eq("cl"),
            normalized.str.contains("groc", regex=False),
            normalized.str.contains("fuel", regex=False) | normalized.eq("fue"),
            normalized.str.contains("enter", regex=False),
            normalized.str.contains("health", regex=False),
            normalized.str.contains("educ", regex=False),
            normalized.str.contains("food", regex=False) | normalized.str.contains("dining", regex=False),
        ]
        choices = [
            "electronics",
            "utilities",
            "travel",
            "clothing",
            "grocery",
            "fuel",
            "entertainment",
            "healthcare",
            "education",
            "food_dining",
        ]
        return pd.Series(
            np.select(conditions, choices, default="unknown_merchant_category"),
            index=series.index,
        )

    @staticmethod
    def _normalize_status(series: pd.Series) -> pd.Series:
        """Map status values into canonical lowercase states."""
        normalized = FraudFeatureEngineer._normalize_placeholder_strings(series, "unknown_status").str.lower()
        return np.select(
            [
                normalized.str.contains("success", regex=False) | normalized.str.contains("approve", regex=False),
                normalized.str.contains("fail", regex=False) | normalized.str.contains("declin", regex=False) | normalized.str.contains("reject", regex=False),
                normalized.str.contains("pending", regex=False),
            ],
            ["success", "failed", "pending"],
            default="unknown_status",
        )

    @staticmethod
    def _normalize_amount(primary_series: pd.Series, secondary_series: pd.Series) -> pd.Series:
        """Merge raw amount columns and strip currency formatting safely."""
        primary = FraudFeatureEngineer._normalize_placeholder_strings(primary_series, "0")
        secondary = FraudFeatureEngineer._normalize_placeholder_strings(secondary_series, "0")
        merged = pd.concat([primary, secondary], axis=1).replace("0", np.nan).bfill(axis=1).iloc[:, 0].fillna("0")
        return (
            merged.astype(str)
            .str.replace(r"[^\d.\-]", "", regex=True)
            .pipe(pd.to_numeric, errors="coerce")
            .fillna(0.0)
        )

    @staticmethod
    def _normalize_numeric_series(series: pd.Series, default_value: float) -> pd.Series:
        """Convert numeric text to floats and impute invalid entries."""
        normalized = (
            FraudFeatureEngineer._normalize_placeholder_strings(series, str(default_value))
            .str.replace(r"[^\d.\-]", "", regex=True)
        )
        return pd.to_numeric(normalized, errors="coerce").fillna(default_value)

    @staticmethod
    def _parse_timestamp_series(series: pd.Series) -> pd.Series:
        """Parse mixed timestamp formats into pandas datetimes."""
        timestamp_series = FraudFeatureEngineer._normalize_placeholder_strings(series, "1970-01-01 00:00:00")
        stripped = timestamp_series.str.strip()

        parsed = pd.to_datetime(stripped, errors="coerce")

        unix_seconds_mask = stripped.str.fullmatch(r"\d{10}")
        if unix_seconds_mask.any():
            parsed.loc[unix_seconds_mask] = pd.to_datetime(
                stripped.loc[unix_seconds_mask].astype("int64"),
                unit="s",
                errors="coerce",
            )

        unix_millis_mask = stripped.str.fullmatch(r"\d{13}")
        if unix_millis_mask.any():
            parsed.loc[unix_millis_mask] = pd.to_datetime(
                stripped.loc[unix_millis_mask].astype("int64"),
                unit="ms",
                errors="coerce",
            )

        compact_mask = stripped.str.fullmatch(r"\d{14}")
        if compact_mask.any():
            parsed.loc[compact_mask] = pd.to_datetime(
                stripped.loc[compact_mask],
                format="%Y%m%d%H%M%S",
                errors="coerce",
            )

        return parsed.fillna(pd.Timestamp("1970-01-01 00:00:00"))

    @staticmethod
    def _normalize_city_series(series: pd.Series) -> pd.Series:
        """Normalize city names and collapse known aliases to canonical tokens."""
        normalized = (
            FraudFeatureEngineer._normalize_placeholder_strings(series, "unknown_city")
            .str.lower()
            .str.replace(r"[^a-z ]", "", regex=True)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
            .replace("", "unknown_city")
        )

        extra_map = {
            "pun": "pune",
            "pu": "pune",
            "j": "jaipur",
            "hyde": "hyderabad",
            "hyderab": "hyderabad",
        }
        return normalized.replace({**CITY_VARIATION_MAP, **extra_map})

    @staticmethod
    def _normalize_ip_address(series: pd.Series) -> pd.Series:
        """Validate IPv4 strings and impute invalid values with a sentinel."""
        normalized = FraudFeatureEngineer._normalize_placeholder_strings(series, "0.0.0.0")
        ipv4_pattern = r"^(?:\d{1,3}\.){3}\d{1,3}$"
        valid_format = normalized.str.match(ipv4_pattern)

        octets = normalized.where(valid_format, "0.0.0.0").str.split(".", expand=True).astype(int)
        valid_octets = octets.le(255).all(axis=1)
        return normalized.where(valid_format & valid_octets, "0.0.0.0")

    @staticmethod
    def _rolling_count(dataframe: pd.DataFrame, group_column: str, window: str) -> pd.Series:
        """Count rows within a trailing time window for each entity."""
        counts = dataframe.groupby(group_column, group_keys=False).apply(
            lambda group: FraudFeatureEngineer._sorted_group_rolling(
                group,
                window,
                "clean_amount",
                "count",
            )
        )
        return counts.fillna(0).astype(int)

    @staticmethod
    def _rolling_sum(dataframe: pd.DataFrame, group_column: str, window: str, value_column: str) -> pd.Series:
        """Sum a numeric flag over a trailing time window."""
        values = dataframe.groupby(group_column, group_keys=False).apply(
            lambda group: FraudFeatureEngineer._sorted_group_rolling(
                group,
                window,
                value_column,
                "sum",
            )
        )
        return values.fillna(0.0)

    @staticmethod
    def _rolling_unique_count(dataframe: pd.DataFrame, group_column: str, window: str, value_column: str) -> pd.Series:
        """Count recent unique categorical values per entity."""
        window_ns = pd.Timedelta(window).value
        output = pd.Series(index=dataframe.index, dtype="int64")

        for _, group in dataframe.groupby(group_column):
            sorted_group = group.sort_values(["standardized_timestamp", "transaction_id"], kind="mergesort")
            timestamps = sorted_group["standardized_timestamp"].astype("int64").to_numpy()
            values = sorted_group[value_column].astype(str).to_numpy()
            result = np.zeros(len(sorted_group), dtype=np.int64)
            active_counts: Dict[str, int] = {}
            left_pointer = 0

            for right_pointer, current_value in enumerate(values):
                active_counts[current_value] = active_counts.get(current_value, 0) + 1

                while timestamps[right_pointer] - timestamps[left_pointer] > window_ns:
                    expired_value = values[left_pointer]
                    active_counts[expired_value] -= 1
                    if active_counts[expired_value] == 0:
                        del active_counts[expired_value]
                    left_pointer += 1

                result[right_pointer] = len(active_counts)

            output.loc[sorted_group.index] = result

        return output.sort_index().fillna(1).astype(int)

    @staticmethod
    def _sorted_group_rolling(group: pd.DataFrame, window: str, value_column: str, operation: str) -> pd.Series:
        """Run a rolling calculation on a timestamp-sorted group and restore original row order."""
        sorted_group = group.sort_values(["standardized_timestamp", "transaction_id"], kind="mergesort")
        rolling_object = sorted_group.rolling(window, on="standardized_timestamp")[value_column]

        if operation == "count":
            values = rolling_object.count()
        elif operation == "sum":
            values = rolling_object.sum()
        else:
            raise ValueError(f"Unsupported rolling operation: {operation}")

        values.index = sorted_group.index
        return values.sort_index()

    @staticmethod
    def _compute_consecutive_failures(user_ids: pd.Series, statuses: pd.Series) -> pd.Series:
        """Count prior consecutive failed attempts for each user."""
        output = np.zeros(len(statuses), dtype=np.int32)

        for _, index_values in user_ids.groupby(user_ids).groups.items():
            running_failures = 0
            for index in index_values:
                output[index] = running_failures
                if statuses.iat[index] in FAILED_STATUSES:
                    running_failures += 1
                else:
                    running_failures = 0

        return pd.Series(output, index=statuses.index)


def run_pipeline(dataframe_or_path: pd.DataFrame | str) -> pd.DataFrame:
    """Convenience wrapper for callers that want dataframe-to-dataframe output."""
    if isinstance(dataframe_or_path, pd.DataFrame):
        dataframe = dataframe_or_path.copy()
        return FraudFeatureEngineer(csv_path="").run_pipeline(dataframe)

    dataframe, _ = FraudFeatureEngineer(csv_path=dataframe_or_path).run()
    return dataframe
