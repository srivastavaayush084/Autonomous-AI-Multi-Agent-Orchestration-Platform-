import os
import io
import csv
import logging
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class DataAnalysisService:
    """
    Automated Quantitative & Qualitative Data Analysis Engine.
    Parses CSV and Excel datasets, computes statistical summaries,
    identifies outliers, detects correlations, and outputs clean tabular reports.
    """

    @staticmethod
    def parse_dataframe(data_source: str, is_file_path: bool = False) -> pd.DataFrame:
        """
        Loads a pandas DataFrame from a file path or raw CSV string.
        """
        if is_file_path:
            if not os.path.exists(data_source):
                raise FileNotFoundError(f"Dataset file not found: {data_source}")
            ext = os.path.splitext(data_source)[-1].lower()
            if ext in [".xlsx", ".xls"]:
                return pd.read_excel(data_source)
            else:
                return pd.read_csv(data_source)
        else:
            return pd.read_csv(io.StringIO(data_source.strip()))

    def analyze_dataset(
        self,
        data_source: str,
        is_file_path: bool = False,
        dataset_name: str = "dataset"
    ) -> Dict[str, Any]:
        """
        Performs full quantitative analysis on a dataset.
        Returns a structured dictionary of summary statistics, missing values,
        outliers, correlations, and markdown-formatted report blocks.
        """
        df = self.parse_dataframe(data_source, is_file_path)
        total_rows, total_cols = df.shape

        col_types = {col: str(df[col].dtype) for col in df.columns}
        missing_counts = df.isnull().sum().to_dict()

        # Identify numeric and categorical columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()

        # 1. Numeric statistics
        numeric_summary = {}
        if numeric_cols:
            desc = df[numeric_cols].describe().round(4).to_dict()
            for col in numeric_cols:
                col_stats = {k: desc[col][k] for k in ["count", "mean", "std", "min", "25%", "50%", "75%", "max"] if k in desc.get(col, {})}
                
                # Outlier detection via IQR
                q25 = df[col].quantile(0.25)
                q75 = df[col].quantile(0.75)
                iqr = q75 - q25
                lower_bound = q25 - 1.5 * iqr
                upper_bound = q75 + 1.5 * iqr
                outliers_count = int(((df[col] < lower_bound) | (df[col] > upper_bound)).sum())

                numeric_summary[col] = {
                    "statistics": col_stats,
                    "iqr": round(float(iqr), 4),
                    "outlier_count": outliers_count,
                    "skewness": round(float(df[col].skew()), 4) if len(df[col].dropna()) > 2 else 0.0
                }

        # 2. Categorical statistics
        categorical_summary = {}
        for col in categorical_cols:
            val_counts = df[col].value_counts().head(5).to_dict()
            categorical_summary[col] = {
                "unique_count": int(df[col].nunique()),
                "top_value": str(df[col].mode().iloc[0]) if not df[col].mode().empty else None,
                "top_5_frequencies": {str(k): int(v) for k, v in val_counts.items()}
            }

        # 3. Correlation Matrix (for numeric columns if >= 2)
        correlations = {}
        if len(numeric_cols) >= 2:
            corr_df = df[numeric_cols].corr().round(4)
            correlations = corr_df.to_dict()

        # 4. Generate Markdown Summary Report
        md_lines = [
            f"# Dataset Quantitative Analysis: {dataset_name}",
            f"**Total Records:** {total_rows} rows | **Total Attributes:** {total_cols} columns\n",
            "## 1. Column Overview & Data Quality",
            "| Column Name | Data Type | Missing Count | Missing % |",
            "| :--- | :--- | :--- | :--- |"
        ]
        for col in df.columns:
            m_cnt = missing_counts.get(col, 0)
            m_pct = round((m_cnt / total_rows * 100), 2) if total_rows > 0 else 0
            md_lines.append(f"| `{col}` | {col_types[col]} | {m_cnt} | {m_pct}% |")

        if numeric_cols:
            md_lines.extend([
                "\n## 2. Numerical Distributions & Descriptive Statistics",
                "| Attribute | Mean | Median | Std Dev | Min | Max | Outliers (IQR) |",
                "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
            ])
            for col in numeric_cols:
                st = numeric_summary[col]["statistics"]
                out_cnt = numeric_summary[col]["outlier_count"]
                md_lines.append(
                    f"| `{col}` | {st.get('mean', 'N/A')} | {st.get('50%', 'N/A')} | "
                    f"{st.get('std', 'N/A')} | {st.get('min', 'N/A')} | {st.get('max', 'N/A')} | {out_cnt} |"
                )

        if categorical_cols:
            md_lines.extend([
                "\n## 3. Categorical Variables & High-Frequency Values"
            ])
            for col, cat_info in categorical_summary.items():
                md_lines.append(f"### Attribute: `{col}` (Unique Values: {cat_info['unique_count']})")
                top_items = ", ".join([f"**{k}** ({v})" for k, v in cat_info["top_5_frequencies"].items()])
                md_lines.append(f"- **Top distribution:** {top_items or 'None'}")

        if correlations:
            md_lines.extend([
                "\n## 4. Key Correlation Insights"
            ])
            # Find top pairwise correlations (excluding self-correlation)
            pairs = []
            for i, col1 in enumerate(numeric_cols):
                for j, col2 in enumerate(numeric_cols):
                    if i < j:
                        val = correlations.get(col1, {}).get(col2, 0)
                        pairs.append((col1, col2, val))
            pairs.sort(key=lambda x: abs(x[2]), reverse=True)
            for c1, c2, val in pairs[:5]:
                direction = "Strong Positive" if val > 0.6 else "Moderate Positive" if val > 0.3 else "Strong Negative" if val < -0.6 else "Moderate Negative" if val < -0.3 else "Weak/No"
                md_lines.append(f"- `{c1}` & `{c2}`: **{val}** ({direction} correlation)")

        markdown_report = "\n".join(md_lines)

        return {
            "total_rows": total_rows,
            "total_cols": total_cols,
            "column_types": col_types,
            "missing_counts": missing_counts,
            "numeric_summary": numeric_summary,
            "categorical_summary": categorical_summary,
            "correlations": correlations,
            "markdown_report": markdown_report,
            "df": df
        }

    def export_summary_csv(self, analysis_result: Dict[str, Any], output_path: str) -> str:
        """Exports statistical summary table to a downloadable CSV file."""
        df: pd.DataFrame = analysis_result["df"]
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if not numeric_cols.empty:
            summary_df = df[numeric_cols].describe().round(4).transpose()
            summary_df.index.name = "attribute"
            summary_df.to_csv(output_path)
        else:
            # Categorical value counts export
            cat_data = []
            for col in df.columns:
                cat_data.append({
                    "attribute": col,
                    "dtype": str(df[col].dtype),
                    "unique_values": df[col].nunique(),
                    "missing_values": df[col].isnull().sum(),
                    "top_value": df[col].mode().iloc[0] if not df[col].mode().empty else None
                })
            pd.DataFrame(cat_data).to_csv(output_path, index=False)
        return output_path


data_analysis_service = DataAnalysisService()
