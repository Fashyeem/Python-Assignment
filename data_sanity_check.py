"""
Data Sanity Check and Cleanup Script
=====================================
Purpose: Perform data quality analysis and cleanup on 4 input Excel files:
    - customer_master.xlsx
    - regional_targets.xlsx
    - sales_transactions.xlsx
    - support_sla.xlsx

Features:
    - Load and inspect data structure
    - Identify missing values, duplicates, invalid formats
    - Detect outliers and data quality issues
    - Generate comprehensive sanity check report
    - Create cleaned data files
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import warnings

warnings.filterwarnings('ignore')


class DataSanityChecker:
    """Class to perform data sanity checks and cleanup operations"""
    
    def __init__(self, input_files):
        """
        Initialize the sanity checker with input file paths
        
        Args:
            input_files (dict): Dictionary mapping file names to file paths
        """
        self.input_files = input_files
        self.data = {}
        self.reports = {}
        self.cleaned_data = {}
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def load_all_files(self):
        """Load all input files into DataFrames"""
        print("\n" + "="*80)
        print("LOADING INPUT FILES")
        print("="*80)
        
        for file_name, file_path in self.input_files.items():
            try:
                if file_path.endswith('.xlsx'):
                    df = pd.read_excel(file_path)
                else:
                    df = pd.read_csv(file_path)
                
                self.data[file_name] = df
                print(f"✓ {file_name}: Loaded successfully ({len(df)} rows, {len(df.columns)} columns)")
            except Exception as e:
                print(f"✗ {file_name}: Error loading file - {str(e)}")
    
    def check_missing_values(self, df, file_name):
        """Check for missing values in the dataset"""
        missing = df.isnull().sum()
        missing_pct = (df.isnull().sum() / len(df) * 100).round(2)
        
        report = {
            'missing_count': missing[missing > 0],
            'missing_percentage': missing_pct[missing_pct > 0]
        }
        
        return report
    
    def check_duplicates(self, df, file_name):
        """Check for duplicate rows"""
        total_duplicates = df.duplicated().sum()
        duplicate_rows = df[df.duplicated(keep=False)].sort_values(by=list(df.columns))
        
        # Check for duplicates by first column (usually ID)
        if len(df.columns) > 0:
            first_col = df.columns[0]
            id_duplicates = df[first_col].duplicated().sum()
        else:
            id_duplicates = 0
        
        return {
            'total_duplicate_rows': total_duplicates,
            'duplicate_count': len(duplicate_rows),
            'id_duplicates': id_duplicates,
            'duplicate_rows': duplicate_rows
        }
    
    def check_data_types(self, df):
        """Check and report data types"""
        return {
            'data_types': df.dtypes,
            'type_summary': df.dtypes.value_counts()
        }
    
    def check_numeric_stats(self, df):
        """Check statistics for numeric columns"""
        numeric_df = df.select_dtypes(include=[np.number])
        
        if numeric_df.empty:
            return {}
        
        stats = {
            'describe': numeric_df.describe(),
            'null_values': numeric_df.isnull().sum()
        }
        
        return stats
    
    def check_categorical_stats(self, df):
        """Check statistics for categorical columns"""
        categorical_df = df.select_dtypes(include=['object'])
        
        stats = {}
        for col in categorical_df.columns:
            stats[col] = {
                'unique_values': df[col].nunique(),
                'most_common': df[col].value_counts().head(5).to_dict(),
                'empty_strings': (df[col] == '').sum(),
                'whitespace_only': (df[col].str.strip() == '').sum()
            }
        
        return stats
    
    def identify_outliers(self, df):
        """Identify potential outliers in numeric columns using IQR method"""
        numeric_df = df.select_dtypes(include=[np.number])
        outliers = {}
        
        for col in numeric_df.columns:
            Q1 = numeric_df[col].quantile(0.25)
            Q3 = numeric_df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outlier_count = len(df[(df[col] < lower_bound) | (df[col] > upper_bound)])
            
            if outlier_count > 0:
                outliers[col] = {
                    'count': outlier_count,
                    'percentage': round(outlier_count / len(df) * 100, 2),
                    'lower_bound': lower_bound,
                    'upper_bound': upper_bound
                }
        
        return outliers
    
    def perform_sanity_check(self):
        """Perform comprehensive sanity checks on all files"""
        print("\n" + "="*80)
        print("PERFORMING SANITY CHECKS")
        print("="*80)
        
        for file_name, df in self.data.items():
            print(f"\n--- Checking {file_name} ---")
            
            report = {
                'file_name': file_name,
                'timestamp': self.timestamp,
                'row_count': len(df),
                'column_count': len(df.columns),
                'columns': list(df.columns),
                'memory_usage': df.memory_usage(deep=True).sum() / 1024 / 1024,  # MB
            }
            
            # Missing values check
            report['missing_values'] = self.check_missing_values(df, file_name)
            
            # Duplicates check
            report['duplicates'] = self.check_duplicates(df, file_name)
            
            # Data types check
            report['data_types'] = self.check_data_types(df)
            
            # Numeric statistics
            report['numeric_stats'] = self.check_numeric_stats(df)
            
            # Categorical statistics
            report['categorical_stats'] = self.check_categorical_stats(df)
            
            # Outliers detection
            report['outliers'] = self.identify_outliers(df)
            
            self.reports[file_name] = report
            
            # Print summary
            print(f"  - Total rows: {report['row_count']}")
            print(f"  - Total columns: {report['column_count']}")
            print(f"  - Missing values: {len(report['missing_values']['missing_count'])} columns with nulls")
            print(f"  - Duplicate rows: {report['duplicates']['total_duplicate_rows']}")
            print(f"  - Outliers detected: {len(report['outliers'])} numeric columns")
    
    def clean_data(self):
        """Clean data and create cleaned versions"""
        print("\n" + "="*80)
        print("CLEANING DATA")
        print("="*80)
        
        for file_name, df in self.data.items():
            print(f"\nCleaning {file_name}...")
            
            df_clean = df.copy()
            
            # Remove complete duplicate rows
            df_clean = df_clean.drop_duplicates()
            
            # Remove rows where all values are null
            df_clean = df_clean.dropna(how='all')
            
            # For numeric columns, fill NaN with median
            numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if df_clean[col].isnull().sum() > 0:
                    df_clean[col].fillna(df_clean[col].median(), inplace=True)
            
            # For categorical columns, fill NaN with 'Unknown'
            categorical_cols = df_clean.select_dtypes(include=['object']).columns
            for col in categorical_cols:
                if df_clean[col].isnull().sum() > 0:
                    df_clean[col].fillna('Unknown', inplace=True)
            
            # Strip whitespace from string columns
            for col in categorical_cols:
                df_clean[col] = df_clean[col].str.strip()
            
            self.cleaned_data[file_name] = df_clean
            
            rows_removed = len(df) - len(df_clean)
            print(f"  ✓ Cleaned: {rows_removed} rows removed")
            print(f"  ✓ Final count: {len(df_clean)} rows")
    
    def generate_report(self):
        """Generate detailed text report"""
        report_text = []
        report_text.append("="*80)
        report_text.append("DATA SANITY CHECK AND CLEANUP REPORT")
        report_text.append("="*80)
        report_text.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        for file_name, report in self.reports.items():
            report_text.append(f"\n{'='*80}")
            report_text.append(f"FILE: {file_name}")
            report_text.append(f"{'='*80}")
            
            report_text.append(f"\nBASIC INFORMATION:")
            report_text.append(f"  - Rows: {report['row_count']}")
            report_text.append(f"  - Columns: {report['column_count']}")
            report_text.append(f"  - Memory Usage: {report['memory_usage']:.2f} MB")
            report_text.append(f"\nCOLUMNS: {', '.join(report['columns'])}")
            
            # Missing Values
            if report['missing_values']['missing_count'].empty:
                report_text.append(f"\nMISSING VALUES: None detected ✓")
            else:
                report_text.append(f"\nMISSING VALUES DETECTED:")
                for col, count in report['missing_values']['missing_count'].items():
                    pct = report['missing_values']['missing_percentage'][col]
                    report_text.append(f"  - {col}: {count} ({pct}%)")
            
            # Duplicates
            report_text.append(f"\nDUPLICATES:")
            report_text.append(f"  - Total duplicate rows: {report['duplicates']['total_duplicate_rows']}")
            report_text.append(f"  - Duplicate IDs: {report['duplicates']['id_duplicates']}")
            
            # Data Types
            report_text.append(f"\nDATA TYPES:")
            for dtype, count in report['data_types']['type_summary'].items():
                report_text.append(f"  - {dtype}: {count} columns")
            
            # Numeric Statistics
            if not report['numeric_stats'].get('describe', pd.DataFrame()).empty:
                report_text.append(f"\nNUMERIC STATISTICS:")
                for col in report['numeric_stats']['describe'].columns:
                    report_text.append(f"  - {col}:")
                    report_text.append(f"      Mean: {report['numeric_stats']['describe'].loc['mean', col]:.2f}")
                    report_text.append(f"      Std Dev: {report['numeric_stats']['describe'].loc['std', col]:.2f}")
                    report_text.append(f"      Min: {report['numeric_stats']['describe'].loc['min', col]:.2f}")
                    report_text.append(f"      Max: {report['numeric_stats']['describe'].loc['max', col]:.2f}")
            
            # Outliers
            if report['outliers']:
                report_text.append(f"\nOUTLIERS DETECTED:")
                for col, outlier_info in report['outliers'].items():
                    report_text.append(f"  - {col}:")
                    report_text.append(f"      Count: {outlier_info['count']} ({outlier_info['percentage']}%)")
                    report_text.append(f"      Range: [{outlier_info['lower_bound']:.2f}, {outlier_info['upper_bound']:.2f}]")
            else:
                report_text.append(f"\nOUTLIERS: None detected ✓")
        
        report_text.append(f"\n{'='*80}")
        report_text.append("END OF REPORT")
        report_text.append(f"{'='*80}\n")
        
        return "\n".join(report_text)
    
    def save_cleaned_files(self, output_dir="cleaned_data"):
        """Save cleaned data to output directory"""
        print("\n" + "="*80)
        print("SAVING CLEANED FILES")
        print("="*80)
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"✓ Created directory: {output_dir}")
        
        for file_name, df in self.cleaned_data.items():
            output_path = os.path.join(output_dir, f"cleaned_{file_name}")
            
            try:
                if file_name.endswith('.xlsx'):
                    df.to_excel(output_path, index=False)
                else:
                    df.to_csv(output_path, index=False)
                
                print(f"✓ Saved: {output_path}")
            except Exception as e:
                print(f"✗ Error saving {file_name}: {str(e)}")
    
    def save_report(self, output_dir="reports"):
        """Save the sanity check report to file"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        report_path = os.path.join(output_dir, f"sanity_check_report_{self.timestamp}.txt")
        
        report_text = self.generate_report()
        
        with open(report_path, 'w') as f:
            f.write(report_text)
        
        print(f"✓ Report saved: {report_path}\n")
        print(report_text)
        
        return report_path
    
    def run_all_checks(self):
        """Run all checks in sequence"""
        self.load_all_files()
        self.perform_sanity_check()
        self.clean_data()
        self.save_cleaned_files()
        self.save_report()


def main():
    """Main execution function"""
    
    # Define input files
    input_files = {
        'customer_master.xlsx': 'customer_master.xlsx',
        'regional_targets.xlsx': 'regional_targets.xlsx',
        'sales_transactions.xlsx': 'sales_transactions.xlsx',
        'support_sla.xlsx': 'support_sla.xlsx'
    }
    
    # Create checker instance and run all checks
    checker = DataSanityChecker(input_files)
    checker.run_all_checks()
    
    print("\n" + "="*80)
    print("DATA SANITY CHECK COMPLETED SUCCESSFULLY!")
    print("="*80)
    print("\nOutput files:")
    print("  - cleaned_data/: Directory containing cleaned Excel files")
    print("  - reports/: Directory containing detailed sanity check reports")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
