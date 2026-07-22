"""
Data Sanity Check and Cleanup Script with Business Rules
=========================================================
Purpose: Perform data quality analysis and cleanup on 4 input Excel files:
    - customer_master.xlsx
    - regional_targets.xlsx
    - sales_transactions.xlsx
    - support_sla.xlsx

Features:
    - Load and inspect data structure
    - Identify missing values, duplicates, invalid formats
    - Detect outliers and data quality issues
    - Apply business rule validations:
        * Revenue Validation: Exclude if Revenue < 0 or blank
        * Quantity Validation: Exclude if Quantity ≤ 0
        * Discount Processing: Set to NULL if Discount > 100
        * Referential Integrity: Check Customer ID against customer master
        * Ticket Status Integrity: Flag if Status='Closed' AND Resolved Date missing
    - Generate comprehensive sanity check and validation reports
    - Create cleaned data files
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import warnings

warnings.filterwarnings('ignore')


class DataSanityChecker:
    """Class to perform data sanity checks and cleanup operations with business rules"""
    
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
        self.validation_reports = {}
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.customer_ids = set()  # Store valid customer IDs
    
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
    
    def extract_customer_ids(self):
        """Extract valid customer IDs from customer master"""
        if 'customer_master.xlsx' in self.data:
            df = self.data['customer_master.xlsx']
            # Look for common customer ID column names
            customer_id_cols = [col for col in df.columns if 'customer' in col.lower() and 'id' in col.lower()]
            if customer_id_cols:
                self.customer_ids = set(df[customer_id_cols[0]].dropna().unique())
                print(f"\n✓ Extracted {len(self.customer_ids)} unique customer IDs from customer_master.xlsx")
            else:
                # If no standard column name found, use first column as ID
                self.customer_ids = set(df[df.columns[0]].dropna().unique())
                print(f"\n✓ Extracted {len(self.customer_ids)} unique IDs from first column of customer_master.xlsx")
    
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
    
    def validate_revenue(self, df, file_name):
        """
        Revenue Validation: Exclude records if Revenue < 0 or is blank
        """
        validation_report = {
            'rule': 'Revenue Validation',
            'invalid_records': pd.DataFrame(),
            'records_removed': 0
        }
        
        # Find revenue column
        revenue_cols = [col for col in df.columns if 'revenue' in col.lower() or 'amount' in col.lower()]
        
        if not revenue_cols:
            return validation_report
        
        revenue_col = revenue_cols[0]
        df_clean = df.copy()
        
        # Check for negative or blank revenue
        invalid_mask = (df_clean[revenue_col].isnull()) | (df_clean[revenue_col] < 0)
        invalid_records = df_clean[invalid_mask]
        
        if len(invalid_records) > 0:
            validation_report['invalid_records'] = invalid_records
            validation_report['records_removed'] = len(invalid_records)
            df_clean = df_clean[~invalid_mask]
        
        return validation_report, df_clean
    
    def validate_quantity(self, df, file_name):
        """
        Quantity Validation: Exclude records if Quantity ≤ 0
        """
        validation_report = {
            'rule': 'Quantity Validation',
            'invalid_records': pd.DataFrame(),
            'records_removed': 0
        }
        
        # Find quantity column
        quantity_cols = [col for col in df.columns if 'quantity' in col.lower() or 'qty' in col.lower()]
        
        if not quantity_cols:
            return validation_report, df
        
        quantity_col = quantity_cols[0]
        df_clean = df.copy()
        
        # Check for quantity <= 0
        invalid_mask = (df_clean[quantity_col].isnull()) | (df_clean[quantity_col] <= 0)
        invalid_records = df_clean[invalid_mask]
        
        if len(invalid_records) > 0:
            validation_report['invalid_records'] = invalid_records
            validation_report['records_removed'] = len(invalid_records)
            df_clean = df_clean[~invalid_mask]
        
        return validation_report, df_clean
    
    def validate_discount(self, df, file_name):
        """
        Discount Processing: Set to NULL if Discount > 100
        """
        validation_report = {
            'rule': 'Discount Processing',
            'invalid_records': pd.DataFrame(),
            'records_modified': 0
        }
        
        # Find discount column
        discount_cols = [col for col in df.columns if 'discount' in col.lower()]
        
        if not discount_cols:
            return validation_report, df
        
        discount_col = discount_cols[0]
        df_clean = df.copy()
        
        # Check for discount > 100
        invalid_mask = (df_clean[discount_col] > 100)
        invalid_records = df_clean[invalid_mask].copy()
        
        if len(invalid_records) > 0:
            validation_report['invalid_records'] = invalid_records
            validation_report['records_modified'] = len(invalid_records)
            df_clean.loc[invalid_mask, discount_col] = np.nan
        
        return validation_report, df_clean
    
    def validate_referential_integrity(self, df, file_name):
        """
        Referential Integrity: Check Customer ID exists in customer master
        Exclude records where Customer ID is not found
        """
        validation_report = {
            'rule': 'Referential Integrity (Customer ID)',
            'invalid_records': pd.DataFrame(),
            'records_removed': 0,
            'customer_ids_not_found': []
        }
        
        # Find customer ID column
        customer_cols = [col for col in df.columns if 'customer' in col.lower() and 'id' in col.lower()]
        
        if not customer_cols or not self.customer_ids:
            return validation_report, df
        
        customer_col = customer_cols[0]
        df_clean = df.copy()
        
        # Check if customer IDs exist in master
        invalid_mask = ~df_clean[customer_col].isin(self.customer_ids)
        invalid_records = df_clean[invalid_mask]
        
        if len(invalid_records) > 0:
            validation_report['invalid_records'] = invalid_records
            validation_report['records_removed'] = len(invalid_records)
            validation_report['customer_ids_not_found'] = list(invalid_records[customer_col].unique())
            df_clean = df_clean[~invalid_mask]
        
        return validation_report, df_clean
    
    def validate_ticket_status(self, df, file_name):
        """
        Ticket Status Integrity: Flag if Status='Closed' AND Resolved Date is missing
        """
        validation_report = {
            'rule': 'Ticket Status Integrity',
            'invalid_records': pd.DataFrame(),
            'records_flagged': 0
        }
        
        # Find status and resolved date columns
        status_cols = [col for col in df.columns if 'status' in col.lower()]
        resolved_cols = [col for col in df.columns if 'resolved' in col.lower() and 'date' in col.lower()]
        
        if not status_cols or not resolved_cols:
            return validation_report, df
        
        status_col = status_cols[0]
        resolved_col = resolved_cols[0]
        df_clean = df.copy()
        
        # Check for Closed status without resolved date
        closed_mask = df_clean[status_col].str.lower() == 'closed'
        invalid_mask = closed_mask & df_clean[resolved_col].isnull()
        invalid_records = df_clean[invalid_mask]
        
        if len(invalid_records) > 0:
            validation_report['invalid_records'] = invalid_records
            validation_report['records_flagged'] = len(invalid_records)
        
        return validation_report, df_clean
    
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
    
    def apply_business_validations(self):
        """Apply business rule validations to data"""
        print("\n" + "="*80)
        print("APPLYING BUSINESS RULE VALIDATIONS")
        print("="*80)
        
        for file_name, df in self.data.items():
            print(f"\n--- Validating {file_name} ---")
            
            df_validated = df.copy()
            validations = []
            
            # Revenue Validation
            revenue_report, df_validated = self.validate_revenue(df_validated, file_name)
            if revenue_report['records_removed'] > 0:
                validations.append(revenue_report)
                print(f"  ✗ Revenue Validation: {revenue_report['records_removed']} records excluded")
            else:
                print(f"  ✓ Revenue Validation: Passed")
            
            # Quantity Validation
            quantity_report, df_validated = self.validate_quantity(df_validated, file_name)
            if quantity_report['records_removed'] > 0:
                validations.append(quantity_report)
                print(f"  ✗ Quantity Validation: {quantity_report['records_removed']} records excluded")
            else:
                print(f"  ✓ Quantity Validation: Passed")
            
            # Discount Processing
            discount_report, df_validated = self.validate_discount(df_validated, file_name)
            if discount_report['records_modified'] > 0:
                validations.append(discount_report)
                print(f"  ⚠ Discount Processing: {discount_report['records_modified']} records modified (discount set to NULL)")
            else:
                print(f"  ✓ Discount Processing: Passed")
            
            # Referential Integrity (only for sales/transaction files)
            if 'sales' in file_name.lower() or 'transaction' in file_name.lower():
                ref_report, df_validated = self.validate_referential_integrity(df_validated, file_name)
                if ref_report['records_removed'] > 0:
                    validations.append(ref_report)
                    print(f"  ✗ Referential Integrity: {ref_report['records_removed']} records excluded (Customer ID not found)")
                else:
                    print(f"  ✓ Referential Integrity: Passed")
            
            # Ticket Status Integrity (only for support SLA files)
            if 'support' in file_name.lower() or 'sla' in file_name.lower():
                status_report, df_validated = self.validate_ticket_status(df_validated, file_name)
                if status_report['records_flagged'] > 0:
                    validations.append(status_report)
                    print(f"  ⚠ Ticket Status Integrity: {status_report['records_flagged']} records flagged (Closed without Resolved Date)")
                else:
                    print(f"  ✓ Ticket Status Integrity: Passed")
            
            self.validation_reports[file_name] = validations
            self.data[file_name] = df_validated
    
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
                if df_clean[col].dtype == 'object':
                    df_clean[col] = df_clean[col].astype(str).str.strip()
            
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
    
    def generate_validation_report(self):
        """Generate detailed validation report for business rules"""
        report_text = []
        report_text.append("="*80)
        report_text.append("BUSINESS RULE VALIDATION REPORT")
        report_text.append("="*80)
        report_text.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        for file_name, validations in self.validation_reports.items():
            if not validations:
                continue
            
            report_text.append(f"\n{'='*80}")
            report_text.append(f"FILE: {file_name}")
            report_text.append(f"{'='*80}\n")
            
            for validation in validations:
                report_text.append(f"\nValidation Rule: {validation['rule']}")
                report_text.append("-" * 60)
                
                if 'records_removed' in validation:
                    report_text.append(f"  Records Removed: {validation['records_removed']}")
                
                if 'records_modified' in validation:
                    report_text.append(f"  Records Modified: {validation['records_modified']}")
                
                if 'records_flagged' in validation:
                    report_text.append(f"  Records Flagged: {validation['records_flagged']}")
                
                if 'customer_ids_not_found' in validation and validation['customer_ids_not_found']:
                    report_text.append(f"  Invalid Customer IDs Found: {validation['customer_ids_not_found']}")
                
                if not validation['invalid_records'].empty:
                    report_text.append(f"\n  Sample of Invalid Records (first 5):")
                    report_text.append(validation['invalid_records'].head().to_string(index=False))
        
        report_text.append(f"\n\n{'='*80}")
        report_text.append("END OF VALIDATION REPORT")
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
    
    def save_reports(self, output_dir="reports"):
        """Save both sanity check and validation reports to files"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Save sanity check report
        sanity_report_path = os.path.join(output_dir, f"sanity_check_report_{self.timestamp}.txt")
        sanity_report_text = self.generate_report()
        
        with open(sanity_report_path, 'w') as f:
            f.write(sanity_report_text)
        
        print(f"✓ Sanity Check Report saved: {sanity_report_path}\n")
        print(sanity_report_text)
        
        # Save validation report
        validation_report_path = os.path.join(output_dir, f"validation_report_{self.timestamp}.txt")
        validation_report_text = self.generate_validation_report()
        
        with open(validation_report_path, 'w') as f:
            f.write(validation_report_text)
        
        print(f"\n✓ Validation Report saved: {validation_report_path}\n")
        print(validation_report_text)
    
    def run_all_checks(self):
        """Run all checks in sequence"""
        self.load_all_files()
        self.extract_customer_ids()
        self.perform_sanity_check()
        self.apply_business_validations()
        self.clean_data()
        self.save_cleaned_files()
        self.save_reports()


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
    print("DATA SANITY CHECK & VALIDATION COMPLETED SUCCESSFULLY!")
    print("="*80)
    print("\nOutput files:")
    print("  - cleaned_data/: Directory containing cleaned Excel files")
    print("  - reports/sanity_check_report_*.txt: Detailed sanity check report")
    print("  - reports/validation_report_*.txt: Business rule validation report")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
