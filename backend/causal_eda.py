#!/usr/bin/env python3
"""
Comprehensive Exploratory Data Analysis for Causal Analysis

This script provides a structured EDA report for causal analysis datasets.
It automatically detects variable types and roles, and generates visualizations
and summaries for all 10 key areas of causal EDA.

Usage:
    python causal_eda.py --data path/to/data.csv --dag path/to/dag.json [--output output_dir]
    python causal_eda.py --data path/to/data.csv [--treatment col] [--outcome col] [--output output_dir]
"""

import argparse
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import warnings
import sys
from datetime import datetime
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from statsmodels.stats.outliers_influence import variance_inflation_factor
import logging

# Configure warnings and logging
warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set matplotlib backend for environments without display
plt.switch_backend('Agg')
plt.style.use('default')
sns.set_palette("husl")

class CausalEDA:
    """Comprehensive EDA for causal analysis datasets."""
    
    def __init__(self, data_path: str, dag_path: Optional[str] = None, 
                 treatment_col: Optional[str] = None, outcome_col: Optional[str] = None,
                 output_dir: str = "eda_output"):
        """
        Initialize CausalEDA.
        
        Args:
            data_path: Path to the dataset CSV file
            dag_path: Optional path to DAG JSON file
            treatment_col: Treatment variable name (if no DAG provided)
            outcome_col: Outcome variable name (if no DAG provided)
            output_dir: Directory to save outputs
        """
        self.data_path = Path(data_path)
        self.dag_path = Path(dag_path) if dag_path else None
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Load data
        self.data = pd.read_csv(self.data_path)
        logger.info(f"Loaded data with shape: {self.data.shape}")
        
        # Load DAG or use manual specification
        self.dag_info = self._load_dag_info(treatment_col, outcome_col)
        
        # Variable classification
        self.variable_info = self._classify_variables()
        
        # Initialize report
        self.report = []
        self.plots_created = []
        
    def _load_dag_info(self, treatment_col: Optional[str], outcome_col: Optional[str]) -> Dict:
        """Load DAG information or create basic structure."""
        if self.dag_path and self.dag_path.exists():
            with open(self.dag_path, 'r') as f:
                dag = json.load(f)
            return {
                'treatment_variable': dag.get('treatment_variable'),
                'outcome_variable': dag.get('outcome_variable'),
                'confounders': dag.get('confounders', []),
                'mediators': dag.get('mediators', []),
                'instruments': dag.get('instruments', []),
                'colliders': dag.get('colliders', []),
                'variables': dag.get('variables', {}),
                'edges': dag.get('edges', [])
            }
        else:
            # Auto-detect or use manual specification
            return {
                'treatment_variable': treatment_col or self._detect_treatment_variable(),
                'outcome_variable': outcome_col or self._detect_outcome_variable(),
                'confounders': [],
                'mediators': [],
                'instruments': [],
                'colliders': [],
                'variables': {},
                'edges': []
            }
    
    def _detect_treatment_variable(self) -> Optional[str]:
        """Auto-detect likely treatment variable."""
        binary_cols = [col for col in self.data.columns 
                      if self.data[col].nunique() == 2]
        
        # Look for common treatment variable names
        treatment_keywords = ['treatment', 'treat', 'intervention', 'exposed', 'group']
        for col in binary_cols:
            if any(keyword in col.lower() for keyword in treatment_keywords):
                return col
        
        # Return first binary column if no keyword match
        return binary_cols[0] if binary_cols else None
    
    def _detect_outcome_variable(self) -> Optional[str]:
        """Auto-detect likely outcome variable."""
        # Look for common outcome variable names
        outcome_keywords = ['outcome', 'target', 'result', 'score', 'amount', 'response', 'y']
        for col in self.data.columns:
            if any(keyword in col.lower() for keyword in outcome_keywords):
                return col
        
        # Return last column as default
        return self.data.columns[-1]
    
    def _classify_variables(self) -> Dict[str, Dict]:
        """Classify variables by type and role."""
        variable_info = {}
        
        for col in self.data.columns:
            var_info = {
                'type': self._get_variable_type(col),
                'role': self._get_variable_role(col),
                'missing_count': self.data[col].isnull().sum(),
                'missing_pct': self.data[col].isnull().sum() / len(self.data) * 100,
                'unique_values': self.data[col].nunique(),
                'dtype': str(self.data[col].dtype)
            }
            
            # Add type-specific statistics
            if var_info['type'] == 'continuous':
                var_info.update({
                    'mean': self.data[col].mean(),
                    'std': self.data[col].std(),
                    'min': self.data[col].min(),
                    'max': self.data[col].max(),
                    'skewness': stats.skew(self.data[col].dropna()),
                    'kurtosis': stats.kurtosis(self.data[col].dropna())
                })
            elif var_info['type'] in ['binary', 'categorical']:
                var_info['value_counts'] = self.data[col].value_counts().to_dict()
                if var_info['type'] == 'binary':
                    var_info['proportion'] = self.data[col].mean() if self.data[col].dtype in [int, float] else None
            
            variable_info[col] = var_info
            
        return variable_info
    
    def _get_variable_type(self, col: str) -> str:
        """Determine variable type: continuous, binary, or categorical."""
        unique_vals = self.data[col].nunique()
        
        if unique_vals == 2:
            return 'binary'
        elif unique_vals <= 10 or self.data[col].dtype == 'object':
            return 'categorical'
        else:
            return 'continuous'
    
    def _get_variable_role(self, col: str) -> str:
        """Determine variable role in causal analysis."""
        if col == self.dag_info.get('treatment_variable'):
            return 'treatment'
        elif col == self.dag_info.get('outcome_variable'):
            return 'outcome'
        elif col in self.dag_info.get('confounders', []):
            return 'confounder'
        elif col in self.dag_info.get('mediators', []):
            return 'mediator'
        elif col in self.dag_info.get('instruments', []):
            return 'instrument'
        elif col in self.dag_info.get('colliders', []):
            return 'collider'
        else:
            return 'unknown'
    
    def analyze_variable_inventory(self) -> Dict:
        """1. Variable inventory & types analysis."""
        self.report.append("="*80)
        self.report.append("1. VARIABLE INVENTORY & TYPES")
        self.report.append("="*80)
        
        # Summary table
        inventory_data = []
        for col, info in self.variable_info.items():
            inventory_data.append([
                col,
                info['type'],
                info['role'],
                info['unique_values'],
                f"{info['missing_pct']:.1f}%",
                info['dtype']
            ])
        
        # Create and save inventory table
        df_inventory = pd.DataFrame(inventory_data, columns=[
            'Variable', 'Type', 'Role', 'Unique_Values', 'Missing_%', 'Data_Type'
        ])
        
        self.report.append(f"\nDataset Shape: {self.data.shape}")
        self.report.append(f"Total Variables: {len(self.data.columns)}")
        self.report.append(f"\nVariable Types:")
        type_counts = df_inventory['Type'].value_counts()
        for vtype, count in type_counts.items():
            self.report.append(f"  - {vtype.title()}: {count}")
        
        self.report.append(f"\nVariable Roles:")
        role_counts = df_inventory['Role'].value_counts()
        for role, count in role_counts.items():
            self.report.append(f"  - {role.title()}: {count}")
        
        # Check for issues
        issues = []
        high_missing = df_inventory[df_inventory['Missing_%'].str.rstrip('%').astype(float) > 20]
        if not high_missing.empty:
            issues.append(f"High missingness (>20%): {', '.join(high_missing['Variable'].tolist())}")
        
        if issues:
            self.report.append(f"\n⚠️  POTENTIAL ISSUES:")
            for issue in issues:
                self.report.append(f"  - {issue}")
        
        # Save detailed inventory
        df_inventory.to_csv(self.output_dir / "variable_inventory.csv", index=False)
        
        return {'inventory': df_inventory, 'issues': issues}
    
    def analyze_univariate_distributions(self) -> Dict:
        """2. Univariate summaries analysis."""
        self.report.append("\n" + "="*80)
        self.report.append("2. UNIVARIATE DISTRIBUTIONS")
        self.report.append("="*80)
        
        # Create figure for all distributions
        n_vars = len(self.data.columns)
        n_cols = 3
        n_rows = (n_vars + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4*n_rows))
        if n_rows == 1:
            axes = axes.reshape(1, -1)
        axes = axes.flatten()
        
        distributions = {}
        
        for i, col in enumerate(self.data.columns):
            var_info = self.variable_info[col]
            ax = axes[i]
            
            if var_info['type'] == 'continuous':
                # Histogram with KDE
                self.data[col].dropna().hist(ax=ax, bins=30, alpha=0.7, density=True)
                self.data[col].dropna().plot.kde(ax=ax, color='red')
                ax.set_title(f"{col}\n(Continuous, Skew: {var_info['skewness']:.2f})")
                
                distributions[col] = {
                    'type': 'continuous',
                    'mean': var_info['mean'],
                    'std': var_info['std'],
                    'skewness': var_info['skewness'],
                    'normality_test': stats.normaltest(self.data[col].dropna())[1]
                }
                
            else:
                # Bar chart for categorical/binary
                value_counts = self.data[col].value_counts()
                value_counts.plot.bar(ax=ax)
                ax.set_title(f"{col}\n({var_info['type'].title()})")
                ax.tick_params(axis='x', rotation=45)
                
                distributions[col] = {
                    'type': var_info['type'],
                    'value_counts': value_counts.to_dict(),
                    'entropy': stats.entropy(value_counts.values)
                }
        
        # Remove empty subplots
        for i in range(len(self.data.columns), len(axes)):
            fig.delaxes(axes[i])
        
        plt.tight_layout()
        plt.savefig(self.output_dir / "univariate_distributions.png", dpi=300, bbox_inches='tight')
        plt.close()
        self.plots_created.append("univariate_distributions.png")
        
        # Missingness analysis
        missing_data = self.data.isnull().sum()
        missing_data = missing_data[missing_data > 0].sort_values(ascending=False)
        
        if not missing_data.empty:
            self.report.append(f"\n📊 MISSINGNESS PATTERNS:")
            for col, count in missing_data.items():
                pct = count / len(self.data) * 100
                self.report.append(f"  - {col}: {count} ({pct:.1f}%)")
                
            # Missingness pattern plot
            if len(missing_data) > 1:
                fig, ax = plt.subplots(figsize=(10, 6))
                missing_data.plot.bar(ax=ax)
                ax.set_title("Missing Values by Variable")
                ax.set_ylabel("Count")
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.savefig(self.output_dir / "missing_patterns.png", dpi=300, bbox_inches='tight')
                plt.close()
                self.plots_created.append("missing_patterns.png")
        
        return distributions
    
    def analyze_bivariate_relationships(self) -> Dict:
        """3. Bivariate relationships analysis."""
        self.report.append("\n" + "="*80)
        self.report.append("3. BIVARIATE RELATIONSHIPS")
        self.report.append("="*80)
        
        treatment_var = self.dag_info.get('treatment_variable')
        outcome_var = self.dag_info.get('outcome_variable')
        
        relationships = {}
        
        if treatment_var and outcome_var:
            # Treatment-Outcome relationship
            self.report.append(f"\n📈 TREATMENT ({treatment_var}) ↔ OUTCOME ({outcome_var}):")
            
            if self.variable_info[treatment_var]['type'] == 'binary':
                # T-test or Mann-Whitney U test
                treated = self.data[self.data[treatment_var] == 1][outcome_var].dropna()
                control = self.data[self.data[treatment_var] == 0][outcome_var].dropna()
                
                if len(treated) > 0 and len(control) > 0:
                    # Check normality
                    normal_treated = stats.normaltest(treated)[1] > 0.05
                    normal_control = stats.normaltest(control)[1] > 0.05
                    
                    if normal_treated and normal_control:
                        stat, pval = stats.ttest_ind(treated, control)
                        test_name = "T-test"
                    else:
                        stat, pval = stats.mannwhitneyu(treated, control, alternative='two-sided')
                        test_name = "Mann-Whitney U"
                    
                    mean_diff = treated.mean() - control.mean()
                    
                    self.report.append(f"  - Raw difference in means: {mean_diff:.4f}")
                    self.report.append(f"  - {test_name} p-value: {pval:.4f}")
                    self.report.append(f"  - Effect size (Cohen's d): {mean_diff / np.sqrt(((treated.var() + control.var()) / 2)):.4f}")
                    
                    relationships['treatment_outcome'] = {
                        'mean_difference': mean_diff,
                        'test_statistic': stat,
                        'p_value': pval,
                        'test_type': test_name
                    }
            
            # Plot treatment-outcome relationship
            fig, axes = plt.subplots(1, 2, figsize=(12, 5))
            
            if self.variable_info[treatment_var]['type'] == 'binary':
                # Box plot
                sns.boxplot(data=self.data, x=treatment_var, y=outcome_var, ax=axes[0])
                axes[0].set_title(f"{outcome_var} by {treatment_var}")
                
                # Density plot
                for val in self.data[treatment_var].unique():
                    subset = self.data[self.data[treatment_var] == val][outcome_var].dropna()
                    if len(subset) > 1:
                        subset.plot.kde(ax=axes[1], label=f"{treatment_var}={val}")
                axes[1].set_title("Density by Treatment Group")
                axes[1].legend()
            
            plt.tight_layout()
            plt.savefig(self.output_dir / "treatment_outcome_relationship.png", dpi=300, bbox_inches='tight')
            plt.close()
            self.plots_created.append("treatment_outcome_relationship.png")
        
        # Confounders analysis
        confounders = [col for col in self.data.columns 
                      if self.variable_info[col]['role'] == 'confounder'] or \
                     [col for col in self.data.columns 
                      if col not in [treatment_var, outcome_var] and 
                      self.variable_info[col]['type'] in ['continuous', 'binary']][:5]  # Limit to 5
        
        if confounders and treatment_var:
            self.report.append(f"\n📊 TREATMENT ↔ CONFOUNDERS:")
            
            n_conf = len(confounders)
            if n_conf > 0:
                n_cols = min(3, n_conf)
                n_rows = (n_conf + n_cols - 1) // n_cols
                
                fig, axes = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 4*n_rows))
                if n_rows == 1 and n_cols == 1:
                    axes = [axes]
                elif n_rows == 1:
                    axes = axes
                else:
                    axes = axes.flatten()
                
                for i, conf in enumerate(confounders):
                    ax = axes[i] if n_conf > 1 else axes[0]
                    
                    if self.variable_info[conf]['type'] == 'continuous':
                        sns.boxplot(data=self.data, x=treatment_var, y=conf, ax=ax)
                        
                        # Calculate correlation/association
                        if self.variable_info[treatment_var]['type'] == 'binary':
                            treated_vals = self.data[self.data[treatment_var] == 1][conf].dropna()
                            control_vals = self.data[self.data[treatment_var] == 0][conf].dropna()
                            if len(treated_vals) > 0 and len(control_vals) > 0:
                                stat, pval = stats.ttest_ind(treated_vals, control_vals)
                                self.report.append(f"  - {conf}: mean diff = {treated_vals.mean() - control_vals.mean():.3f}, p = {pval:.3f}")
                    else:
                        # Cross-tabulation for categorical
                        ct = pd.crosstab(self.data[treatment_var], self.data[conf])
                        sns.heatmap(ct, annot=True, fmt='d', ax=ax)
                    
                    ax.set_title(f"{treatment_var} vs {conf}")
                
                # Remove empty subplots
                if n_conf < len(axes):
                    for i in range(n_conf, len(axes)):
                        fig.delaxes(axes[i])
                
                plt.tight_layout()
                plt.savefig(self.output_dir / "treatment_confounders.png", dpi=300, bbox_inches='tight')
                plt.close()
                self.plots_created.append("treatment_confounders.png")
        
        return relationships
    
    def analyze_overlap_common_support(self) -> Dict:
        """4. Overlap / common support analysis."""
        self.report.append("\n" + "="*80)
        self.report.append("4. OVERLAP / COMMON SUPPORT")
        self.report.append("="*80)
        
        treatment_var = self.dag_info.get('treatment_variable')
        overlap_analysis = {}
        
        if treatment_var and self.variable_info[treatment_var]['type'] == 'binary':
            # Get potential confounders for propensity score
            confounders = [col for col in self.data.columns 
                          if col != treatment_var and 
                          self.variable_info[col]['type'] in ['continuous', 'binary'] and
                          self.data[col].notna().sum() > 0][:10]  # Limit to avoid overfitting
            
            if confounders:
                try:
                    # Prepare data for propensity score
                    ps_data = self.data[[treatment_var] + confounders].dropna()
                    
                    if len(ps_data) > 10:  # Minimum samples needed
                        X = ps_data[confounders]
                        y = ps_data[treatment_var]
                        
                        # Standardize features
                        scaler = StandardScaler()
                        X_scaled = scaler.fit_transform(X)
                        
                        # Fit logistic regression for propensity scores
                        lr = LogisticRegression(random_state=42, max_iter=1000)
                        lr.fit(X_scaled, y)
                        
                        # Calculate propensity scores
                        ps_scores = lr.predict_proba(X_scaled)[:, 1]
                        ps_data['propensity_score'] = ps_scores
                        
                        # Analyze overlap
                        treated_ps = ps_data[ps_data[treatment_var] == 1]['propensity_score']
                        control_ps = ps_data[ps_data[treatment_var] == 0]['propensity_score']
                        
                        overlap_analysis = {
                            'treated_ps_range': (treated_ps.min(), treated_ps.max()),
                            'control_ps_range': (control_ps.min(), control_ps.max()),
                            'overlap_range': (max(treated_ps.min(), control_ps.min()), 
                                            min(treated_ps.max(), control_ps.max())),
                            'poor_overlap_threshold': 0.1
                        }
                        
                        # Check for poor overlap
                        poor_overlap_treated = (treated_ps < 0.1).sum() + (treated_ps > 0.9).sum()
                        poor_overlap_control = (control_ps < 0.1).sum() + (control_ps > 0.9).sum()
                        
                        self.report.append(f"\n📊 PROPENSITY SCORE ANALYSIS:")
                        self.report.append(f"  - Treated group PS range: [{treated_ps.min():.3f}, {treated_ps.max():.3f}]")
                        self.report.append(f"  - Control group PS range: [{control_ps.min():.3f}, {control_ps.max():.3f}]")
                        self.report.append(f"  - Common support range: [{overlap_analysis['overlap_range'][0]:.3f}, {overlap_analysis['overlap_range'][1]:.3f}]")
                        self.report.append(f"  - Poor overlap (PS < 0.1 or > 0.9): {poor_overlap_treated + poor_overlap_control} observations")
                        
                        if poor_overlap_treated + poor_overlap_control > len(ps_data) * 0.1:
                            self.report.append("  ⚠️  WARNING: Poor overlap detected - consider trimming or matching")
                        
                        # Plot propensity score distributions
                        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
                        
                        # Histogram
                        axes[0].hist(treated_ps, bins=30, alpha=0.7, label='Treated', density=True)
                        axes[0].hist(control_ps, bins=30, alpha=0.7, label='Control', density=True)
                        axes[0].set_xlabel('Propensity Score')
                        axes[0].set_ylabel('Density')
                        axes[0].set_title('Propensity Score Distribution')
                        axes[0].legend()
                        axes[0].axvline(0.1, color='red', linestyle='--', alpha=0.5)
                        axes[0].axvline(0.9, color='red', linestyle='--', alpha=0.5)
                        
                        # Box plot
                        ps_plot_data = pd.DataFrame({
                            'propensity_score': np.concatenate([treated_ps, control_ps]),
                            'group': ['Treated']*len(treated_ps) + ['Control']*len(control_ps)
                        })
                        sns.boxplot(data=ps_plot_data, x='group', y='propensity_score', ax=axes[1])
                        axes[1].set_title('Propensity Score by Group')
                        
                        plt.tight_layout()
                        plt.savefig(self.output_dir / "propensity_score_overlap.png", dpi=300, bbox_inches='tight')
                        plt.close()
                        self.plots_created.append("propensity_score_overlap.png")
                        
                except Exception as e:
                    self.report.append(f"  ⚠️  Could not compute propensity scores: {str(e)}")
                    logger.warning(f"Propensity score calculation failed: {e}")
            else:
                self.report.append("  ⚠️  No suitable confounders found for propensity score analysis")
        else:
            self.report.append("  ⚠️  Treatment variable not binary - skipping propensity score analysis")
        
        return overlap_analysis
    
    def analyze_correlation_multicollinearity(self) -> Dict:
        """5. Correlation & multicollinearity analysis."""
        self.report.append("\n" + "="*80)
        self.report.append("5. CORRELATION & MULTICOLLINEARITY")
        self.report.append("="*80)
        
        # Get numeric variables only
        numeric_vars = [col for col in self.data.columns 
                       if self.variable_info[col]['type'] in ['continuous', 'binary']]
        
        correlation_analysis = {}
        
        if len(numeric_vars) > 1:
            # Correlation matrix
            corr_matrix = self.data[numeric_vars].corr()
            
            # Find high correlations
            high_corr_pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_val = corr_matrix.iloc[i, j]
                    if abs(corr_val) > 0.8:
                        high_corr_pairs.append((
                            corr_matrix.columns[i], 
                            corr_matrix.columns[j], 
                            corr_val
                        ))
            
            self.report.append(f"\n📊 CORRELATION ANALYSIS:")
            self.report.append(f"  - Variables analyzed: {len(numeric_vars)}")
            
            if high_corr_pairs:
                self.report.append(f"  - High correlations (|r| > 0.8): {len(high_corr_pairs)}")
                for var1, var2, corr in high_corr_pairs:
                    self.report.append(f"    • {var1} ↔ {var2}: r = {corr:.3f}")
            else:
                self.report.append("  - No high correlations (|r| > 0.8) detected")
            
            # Plot correlation heatmap
            plt.figure(figsize=(10, 8))
            mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
            sns.heatmap(corr_matrix, mask=mask, annot=True, cmap='RdBu_r', center=0,
                       square=True, fmt='.2f', cbar_kws={"shrink": .8})
            plt.title('Correlation Matrix')
            plt.tight_layout()
            plt.savefig(self.output_dir / "correlation_matrix.png", dpi=300, bbox_inches='tight')
            plt.close()
            self.plots_created.append("correlation_matrix.png")
            
            # VIF analysis (for regression-suitable variables)
            continuous_vars = [col for col in numeric_vars 
                             if self.variable_info[col]['type'] == 'continuous' and 
                             self.data[col].notna().sum() > 0]
            
            if len(continuous_vars) > 2:
                try:
                    vif_data = self.data[continuous_vars].dropna()
                    if len(vif_data) > len(continuous_vars) + 1:  # Need more observations than variables
                        vif_results = []
                        for i, col in enumerate(continuous_vars):
                            vif_val = variance_inflation_factor(vif_data.values, i)
                            vif_results.append((col, vif_val))
                        
                        self.report.append(f"\n📊 VARIANCE INFLATION FACTORS:")
                        high_vif = []
                        for var, vif in vif_results:
                            self.report.append(f"  - {var}: VIF = {vif:.2f}")
                            if vif > 5:
                                high_vif.append((var, vif))
                        
                        if high_vif:
                            self.report.append(f"  ⚠️  High multicollinearity (VIF > 5): {len(high_vif)} variables")
                            for var, vif in high_vif:
                                self.report.append(f"    • {var}: VIF = {vif:.2f}")
                        
                        correlation_analysis['vif_results'] = vif_results
                        correlation_analysis['high_vif'] = high_vif
                        
                except Exception as e:
                    self.report.append(f"  ⚠️  Could not compute VIF: {str(e)}")
            
            correlation_analysis['correlation_matrix'] = corr_matrix
            correlation_analysis['high_correlations'] = high_corr_pairs
        
        return correlation_analysis
    
    def analyze_temporal_patterns(self) -> Dict:
        """6. Temporal patterns analysis."""
        self.report.append("\n" + "="*80)
        self.report.append("6. TEMPORAL PATTERNS")
        self.report.append("="*80)
        
        temporal_analysis = {}
        
        # Look for time-related columns
        time_cols = []
        potential_time_keywords = ['time', 'date', 'year', 'month', 'day', 'period', 'wave', 'step']
        
        for col in self.data.columns:
            if any(keyword in col.lower() for keyword in potential_time_keywords):
                time_cols.append(col)
            elif self.data[col].dtype in ['datetime64[ns]', 'period[D]']:
                time_cols.append(col)
        
        if time_cols:
            self.report.append(f"\n📅 TIME VARIABLES DETECTED: {', '.join(time_cols)}")
            
            outcome_var = self.dag_info.get('outcome_variable')
            treatment_var = self.dag_info.get('treatment_variable')
            
            for time_col in time_cols[:2]:  # Limit to 2 time variables
                try:
                    # Sort by time variable
                    time_sorted = self.data.sort_values(time_col).copy()
                    
                    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
                    
                    # Plot outcome over time
                    if outcome_var and outcome_var in time_sorted.columns:
                        axes[0].plot(time_sorted[time_col], time_sorted[outcome_var], alpha=0.6)
                        axes[0].set_title(f"{outcome_var} over {time_col}")
                        axes[0].set_ylabel(outcome_var)
                        
                        # Add trend line
                        if self.variable_info[time_col]['type'] in ['continuous', 'binary']:
                            z = np.polyfit(time_sorted[time_col].fillna(0), 
                                         time_sorted[outcome_var].fillna(time_sorted[outcome_var].mean()), 1)
                            p = np.poly1d(z)
                            axes[0].plot(time_sorted[time_col], p(time_sorted[time_col]), "r--", alpha=0.8)
                    
                    # Plot treatment over time (if applicable)
                    if treatment_var and treatment_var in time_sorted.columns:
                        if self.variable_info[treatment_var]['type'] == 'binary':
                            # Show treatment proportions over time periods
                            time_groups = pd.cut(time_sorted[time_col], bins=10) if self.variable_info[time_col]['type'] == 'continuous' else time_sorted[time_col]
                            treatment_props = time_sorted.groupby(time_groups)[treatment_var].mean()
                            treatment_props.plot(kind='bar', ax=axes[1], alpha=0.7)
                            axes[1].set_title(f"{treatment_var} proportion over {time_col}")
                            axes[1].set_ylabel(f"{treatment_var} proportion")
                            plt.xticks(rotation=45)
                    
                    plt.tight_layout()
                    plt.savefig(self.output_dir / f"temporal_patterns_{time_col}.png", dpi=300, bbox_inches='tight')
                    plt.close()
                    self.plots_created.append(f"temporal_patterns_{time_col}.png")
                    
                    temporal_analysis[time_col] = {
                        'type': self.variable_info[time_col]['type'],
                        'range': (time_sorted[time_col].min(), time_sorted[time_col].max()),
                        'periods': time_sorted[time_col].nunique()
                    }
                    
                except Exception as e:
                    self.report.append(f"  ⚠️  Could not analyze temporal patterns for {time_col}: {str(e)}")
        
        else:
            self.report.append("  📅 No temporal variables detected")
            # Check if data might represent time series based on structure
            if len(self.data) > 50:
                self.report.append("  💡 If this is time-series data, consider adding explicit time variables")
        
        return temporal_analysis
    
    def analyze_instrument_validity(self) -> Dict:
        """7. Instrument validity analysis."""
        self.report.append("\n" + "="*80)
        self.report.append("7. INSTRUMENT VALIDITY")
        self.report.append("="*80)
        
        instruments = self.dag_info.get('instruments', [])
        treatment_var = self.dag_info.get('treatment_variable')
        
        instrument_analysis = {}
        
        if instruments and treatment_var:
            self.report.append(f"\n🔧 INSTRUMENTS DETECTED: {', '.join(instruments)}")
            
            confounders = [col for col in self.data.columns 
                          if self.variable_info[col]['role'] == 'confounder'] or \
                         [col for col in self.data.columns 
                          if col not in [treatment_var] + instruments and 
                          self.variable_info[col]['type'] in ['continuous', 'binary']][:5]
            
            for instrument in instruments:
                if instrument in self.data.columns:
                    self.report.append(f"\n📊 ANALYZING INSTRUMENT: {instrument}")
                    
                    # Test 1: Instrument-Treatment correlation (should be strong)
                    if (self.variable_info[instrument]['type'] in ['continuous', 'binary'] and 
                        self.variable_info[treatment_var]['type'] in ['continuous', 'binary']):
                        
                        inst_treat_corr = self.data[instrument].corr(self.data[treatment_var])
                        self.report.append(f"  - Instrument ↔ Treatment correlation: {inst_treat_corr:.3f}")
                        
                        if abs(inst_treat_corr) < 0.1:
                            self.report.append(f"    ⚠️  WEAK INSTRUMENT: Correlation < 0.1")
                        elif abs(inst_treat_corr) > 0.3:
                            self.report.append(f"    ✓ STRONG INSTRUMENT: Correlation > 0.3")
                    
                    # Test 2: Instrument-Confounder correlations (should be weak)
                    weak_exogeneity = True
                    for conf in confounders:
                        if conf in self.data.columns:
                            if (self.variable_info[instrument]['type'] in ['continuous', 'binary'] and 
                                self.variable_info[conf]['type'] in ['continuous', 'binary']):
                                
                                inst_conf_corr = self.data[instrument].corr(self.data[conf])
                                self.report.append(f"  - Instrument ↔ {conf} correlation: {inst_conf_corr:.3f}")
                                
                                if abs(inst_conf_corr) > 0.3:
                                    weak_exogeneity = False
                                    self.report.append(f"    ⚠️  POTENTIAL VIOLATION: High correlation with confounder")
                    
                    if weak_exogeneity:
                        self.report.append(f"    ✓ EXOGENEITY: Weak correlations with confounders")
                    
                    instrument_analysis[instrument] = {
                        'treatment_correlation': inst_treat_corr if 'inst_treat_corr' in locals() else None,
                        'weak_exogeneity': weak_exogeneity,
                        'confounder_correlations': {}
                    }
        
        else:
            self.report.append("  🔧 No instruments specified")
            self.report.append("  💡 For IV analysis, specify instrument variables in DAG or consider natural experiments")
            
            # Look for potential instruments (variables correlated with treatment but not outcome)
            treatment_var = self.dag_info.get('treatment_variable')
            outcome_var = self.dag_info.get('outcome_variable')
            
            if treatment_var and outcome_var:
                potential_instruments = []
                for col in self.data.columns:
                    if (col not in [treatment_var, outcome_var] and 
                        self.variable_info[col]['type'] in ['continuous', 'binary']):
                        
                        treat_corr = abs(self.data[col].corr(self.data[treatment_var]))
                        outcome_corr = abs(self.data[col].corr(self.data[outcome_var]))
                        
                        if treat_corr > 0.2 and outcome_corr < 0.1:
                            potential_instruments.append((col, treat_corr, outcome_corr))
                
                if potential_instruments:
                    self.report.append(f"  💡 POTENTIAL INSTRUMENTS DETECTED:")
                    for var, t_corr, o_corr in potential_instruments[:3]:
                        self.report.append(f"    • {var}: r_treatment={t_corr:.3f}, r_outcome={o_corr:.3f}")
        
        return instrument_analysis
    
    def analyze_mediation_paths(self) -> Dict:
        """8. Mediator / path analysis."""
        self.report.append("\n" + "="*80)
        self.report.append("8. MEDIATOR / PATH ANALYSIS")
        self.report.append("="*80)
        
        mediators = self.dag_info.get('mediators', [])
        treatment_var = self.dag_info.get('treatment_variable')
        outcome_var = self.dag_info.get('outcome_variable')
        
        mediation_analysis = {}
        
        if mediators and treatment_var and outcome_var:
            self.report.append(f"\n🔗 MEDIATORS DETECTED: {', '.join(mediators)}")
            
            for mediator in mediators:
                if mediator in self.data.columns:
                    self.report.append(f"\n📊 ANALYZING MEDIATOR: {mediator}")
                    
                    # Path a: Treatment → Mediator
                    if (self.variable_info[treatment_var]['type'] in ['continuous', 'binary'] and 
                        self.variable_info[mediator]['type'] in ['continuous', 'binary']):
                        
                        path_a_corr = self.data[treatment_var].corr(self.data[mediator])
                        self.report.append(f"  - Path a (Treatment → Mediator): r = {path_a_corr:.3f}")
                        
                        # Statistical test
                        if self.variable_info[treatment_var]['type'] == 'binary':
                            treated = self.data[self.data[treatment_var] == 1][mediator].dropna()
                            control = self.data[self.data[treatment_var] == 0][mediator].dropna()
                            if len(treated) > 0 and len(control) > 0:
                                stat, pval = stats.ttest_ind(treated, control)
                                self.report.append(f"    • T-test p-value: {pval:.3f}")
                    
                    # Path b: Mediator → Outcome
                    if (self.variable_info[mediator]['type'] in ['continuous', 'binary'] and 
                        self.variable_info[outcome_var]['type'] in ['continuous', 'binary']):
                        
                        path_b_corr = self.data[mediator].corr(self.data[outcome_var])
                        self.report.append(f"  - Path b (Mediator → Outcome): r = {path_b_corr:.3f}")
                    
                    # Visualize mediation paths
                    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
                    
                    # Treatment → Mediator
                    if self.variable_info[treatment_var]['type'] == 'binary':
                        sns.boxplot(data=self.data, x=treatment_var, y=mediator, ax=axes[0])
                    else:
                        axes[0].scatter(self.data[treatment_var], self.data[mediator], alpha=0.6)
                    axes[0].set_title(f"{treatment_var} → {mediator}")
                    
                    # Mediator → Outcome
                    axes[1].scatter(self.data[mediator], self.data[outcome_var], alpha=0.6)
                    axes[1].set_title(f"{mediator} → {outcome_var}")
                    
                    # Treatment → Outcome (direct effect)
                    if self.variable_info[treatment_var]['type'] == 'binary':
                        sns.boxplot(data=self.data, x=treatment_var, y=outcome_var, ax=axes[2])
                    else:
                        axes[2].scatter(self.data[treatment_var], self.data[outcome_var], alpha=0.6)
                    axes[2].set_title(f"{treatment_var} → {outcome_var}")
                    
                    plt.tight_layout()
                    plt.savefig(self.output_dir / f"mediation_analysis_{mediator}.png", dpi=300, bbox_inches='tight')
                    plt.close()
                    self.plots_created.append(f"mediation_analysis_{mediator}.png")
                    
                    mediation_analysis[mediator] = {
                        'path_a_correlation': path_a_corr if 'path_a_corr' in locals() else None,
                        'path_b_correlation': path_b_corr if 'path_b_corr' in locals() else None
                    }
        
        else:
            self.report.append("  🔗 No mediators specified")
            
            # Look for potential mediators
            if treatment_var and outcome_var:
                potential_mediators = []
                for col in self.data.columns:
                    if (col not in [treatment_var, outcome_var] and 
                        self.variable_info[col]['type'] in ['continuous', 'binary']):
                        
                        treat_corr = abs(self.data[col].corr(self.data[treatment_var]))
                        outcome_corr = abs(self.data[col].corr(self.data[outcome_var]))
                        
                        if treat_corr > 0.2 and outcome_corr > 0.2:
                            potential_mediators.append((col, treat_corr, outcome_corr))
                
                if potential_mediators:
                    self.report.append(f"  💡 POTENTIAL MEDIATORS DETECTED:")
                    for var, t_corr, o_corr in potential_mediators[:3]:
                        self.report.append(f"    • {var}: r_treatment={t_corr:.3f}, r_outcome={o_corr:.3f}")
        
        # Check for colliders
        colliders = self.dag_info.get('colliders', [])
        if colliders:
            self.report.append(f"\n⚠️  COLLIDERS DETECTED: {', '.join(colliders)}")
            self.report.append("  💡 Avoid conditioning on colliders in analysis")
        
        return mediation_analysis
    
    def analyze_potential_biases(self) -> Dict:
        """9. Assessing potential biases analysis."""
        self.report.append("\n" + "="*80)
        self.report.append("9. POTENTIAL BIASES ASSESSMENT")
        self.report.append("="*80)
        
        bias_analysis = {}
        
        # Selection bias analysis
        self.report.append("\n🎯 SELECTION BIAS:")
        
        # Check for systematic missingness
        missing_patterns = {}
        treatment_var = self.dag_info.get('treatment_variable')
        outcome_var = self.dag_info.get('outcome_variable')
        
        for col in self.data.columns:
            missing_count = self.data[col].isnull().sum()
            if missing_count > 0:
                missing_patterns[col] = missing_count / len(self.data)
        
        if missing_patterns:
            self.report.append(f"  - Variables with missing data: {len(missing_patterns)}")
            high_missing = {k: v for k, v in missing_patterns.items() if v > 0.1}
            if high_missing:
                self.report.append(f"  - High missingness (>10%): {list(high_missing.keys())}")
                
                # Check if missingness is related to treatment
                if treatment_var and treatment_var in self.data.columns:
                    for var, miss_rate in high_missing.items():
                        missing_by_treatment = self.data.groupby(treatment_var)[var].apply(lambda x: x.isnull().sum() / len(x))
                        if len(missing_by_treatment) == 2:
                            diff = abs(missing_by_treatment.iloc[0] - missing_by_treatment.iloc[1])
                            if diff > 0.05:  # 5% difference threshold
                                self.report.append(f"    ⚠️  {var}: Differential missingness by treatment ({diff:.2%})")
        
        # Informative censoring/dropout
        if len(self.data) > 100:  # Only for larger datasets
            # Look for patterns in data that suggest censoring
            # Check if outcomes are truncated
            if outcome_var and self.variable_info[outcome_var]['type'] == 'continuous':
                outcome_data = self.data[outcome_var].dropna()
                if len(outcome_data) > 0:
                    # Check for heaping at boundaries
                    q99 = outcome_data.quantile(0.99)
                    q01 = outcome_data.quantile(0.01)
                    
                    upper_heap = (outcome_data >= q99).sum() / len(outcome_data)
                    lower_heap = (outcome_data <= q01).sum() / len(outcome_data)
                    
                    if upper_heap > 0.02 or lower_heap > 0.02:
                        self.report.append(f"  ⚠️  Potential censoring detected in {outcome_var}")
                        self.report.append(f"    • Upper boundary heaping: {upper_heap:.1%}")
                        self.report.append(f"    • Lower boundary heaping: {lower_heap:.1%}")
        
        # Measurement bias indicators
        self.report.append("\n📏 MEASUREMENT BIAS:")
        
        # Check for variables with suspicious distributions
        suspicious_vars = []
        for col in self.data.columns:
            if self.variable_info[col]['type'] == 'continuous':
                var_data = self.data[col].dropna()
                if len(var_data) > 10:
                    # Check for excessive zeros
                    zero_rate = (var_data == 0).sum() / len(var_data)
                    if zero_rate > 0.3:
                        suspicious_vars.append((col, f"High zero rate: {zero_rate:.1%}"))
                    
                    # Check for extreme skewness
                    skew = abs(stats.skew(var_data))
                    if skew > 3:
                        suspicious_vars.append((col, f"Extreme skewness: {skew:.2f}"))
        
        if suspicious_vars:
            self.report.append("  ⚠️  Variables with suspicious distributions:")
            for var, issue in suspicious_vars:
                self.report.append(f"    • {var}: {issue}")
        else:
            self.report.append("  ✓ No obvious measurement issues detected")
        
        # Confounding bias
        self.report.append("\n🔄 CONFOUNDING BIAS:")
        
        if treatment_var and outcome_var:
            # Calculate crude association
            if (self.variable_info[treatment_var]['type'] == 'binary' and 
                self.variable_info[outcome_var]['type'] == 'continuous'):
                
                treated = self.data[self.data[treatment_var] == 1][outcome_var].dropna()
                control = self.data[self.data[treatment_var] == 0][outcome_var].dropna()
                
                if len(treated) > 0 and len(control) > 0:
                    crude_diff = treated.mean() - control.mean()
                    self.report.append(f"  - Crude treatment effect: {crude_diff:.3f}")
                    
                    # Check balance of confounders
                    confounders = [col for col in self.data.columns 
                                  if col not in [treatment_var, outcome_var] and 
                                  self.variable_info[col]['type'] in ['continuous', 'binary']][:5]
                    
                    imbalanced_confounders = []
                    for conf in confounders:
                        conf_treated = self.data[self.data[treatment_var] == 1][conf].dropna()
                        conf_control = self.data[self.data[treatment_var] == 0][conf].dropna()
                        
                        if len(conf_treated) > 0 and len(conf_control) > 0:
                            if self.variable_info[conf]['type'] == 'continuous':
                                std_diff = abs(conf_treated.mean() - conf_control.mean()) / np.sqrt((conf_treated.var() + conf_control.var()) / 2)
                                if std_diff > 0.25:  # Common threshold for imbalance
                                    imbalanced_confounders.append((conf, std_diff))
                    
                    if imbalanced_confounders:
                        self.report.append(f"  ⚠️  Imbalanced confounders (std diff > 0.25):")
                        for conf, std_diff in imbalanced_confounders:
                            self.report.append(f"    • {conf}: {std_diff:.3f}")
                    else:
                        self.report.append("  ✓ Reasonable balance on observed confounders")
        
        bias_analysis = {
            'missing_patterns': missing_patterns,
            'suspicious_variables': suspicious_vars,
            'imbalanced_confounders': imbalanced_confounders if 'imbalanced_confounders' in locals() else []
        }
        
        return bias_analysis
    
    def analyze_feature_engineering(self) -> Dict:
        """10. Feature engineering analysis."""
        self.report.append("\n" + "="*80)
        self.report.append("10. FEATURE ENGINEERING RECOMMENDATIONS")
        self.report.append("="*80)
        
        feature_recommendations = {}
        
        outcome_var = self.dag_info.get('outcome_variable')
        treatment_var = self.dag_info.get('treatment_variable')
        
        # Nonlinear effects analysis
        self.report.append("\n📈 NONLINEAR EFFECTS:")
        
        if outcome_var:
            continuous_vars = [col for col in self.data.columns 
                             if (self.variable_info[col]['type'] == 'continuous' and 
                                 col != outcome_var)][:5]  # Limit to 5
            
            nonlinear_candidates = []
            
            if continuous_vars:
                n_vars = len(continuous_vars)
                n_cols = min(3, n_vars)
                n_rows = (n_vars + n_cols - 1) // n_cols
                
                fig, axes = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 4*n_rows))
                if n_rows == 1 and n_cols == 1:
                    axes = [axes]
                elif n_rows == 1:
                    axes = axes
                else:
                    axes = axes.flatten()
                
                for i, var in enumerate(continuous_vars):
                    ax = axes[i] if n_vars > 1 else axes[0]
                    
                    # Scatter plot with smoothing
                    x_data = self.data[var].dropna()
                    y_data = self.data.loc[x_data.index, outcome_var].dropna()
                    
                    if len(x_data) > 10 and len(y_data) > 10:
                        # Align the data
                        common_idx = x_data.index.intersection(y_data.index)
                        x_aligned = x_data.loc[common_idx]
                        y_aligned = y_data.loc[common_idx]
                        
                        ax.scatter(x_aligned, y_aligned, alpha=0.6)
                        
                        # Linear correlation
                        linear_corr = x_aligned.corr(y_aligned)
                        
                        # Try to fit polynomial to detect nonlinearity
                        try:
                            # Fit quadratic
                            coeffs = np.polyfit(x_aligned, y_aligned, 2)
                            x_smooth = np.linspace(x_aligned.min(), x_aligned.max(), 100)
                            y_smooth = np.polyval(coeffs, x_smooth)
                            ax.plot(x_smooth, y_smooth, 'r-', alpha=0.8)
                            
                            # Check if quadratic term is significant
                            if abs(coeffs[0]) > 0.01:  # Threshold for quadratic coefficient
                                nonlinear_candidates.append((var, linear_corr, abs(coeffs[0])))
                        except:
                            pass
                        
                        ax.set_title(f"{outcome_var} vs {var}\n(r = {linear_corr:.3f})")
                        ax.set_xlabel(var)
                        ax.set_ylabel(outcome_var)
                
                # Remove empty subplots
                if n_vars < len(axes):
                    for i in range(n_vars, len(axes)):
                        fig.delaxes(axes[i])
                
                plt.tight_layout()
                plt.savefig(self.output_dir / "nonlinear_effects.png", dpi=300, bbox_inches='tight')
                plt.close()
                self.plots_created.append("nonlinear_effects.png")
            
            if nonlinear_candidates:
                self.report.append("  💡 Variables potentially needing nonlinear transformation:")
                for var, linear_corr, quad_coeff in nonlinear_candidates:
                    self.report.append(f"    • {var}: Consider splines/polynomials (quad coeff: {quad_coeff:.3f})")
            else:
                self.report.append("  ✓ Linear relationships appear adequate")
        
        # Interaction effects
        self.report.append("\n🔗 INTERACTION EFFECTS:")
        
        if treatment_var:
            # Look for variables that might interact with treatment
            continuous_vars = [col for col in self.data.columns 
                             if (self.variable_info[col]['type'] == 'continuous' and 
                                 col not in [treatment_var, outcome_var])][:3]
            
            interaction_candidates = []
            
            for var in continuous_vars:
                if outcome_var and self.variable_info[treatment_var]['type'] == 'binary':
                    # Check if treatment effect varies by levels of var
                    # Split var into high/low groups
                    median_val = self.data[var].median()
                    
                    # High group
                    high_group = self.data[self.data[var] > median_val]
                    if len(high_group) > 10:
                        high_treated = high_group[high_group[treatment_var] == 1][outcome_var].dropna()
                        high_control = high_group[high_group[treatment_var] == 0][outcome_var].dropna()
                        high_effect = high_treated.mean() - high_control.mean() if len(high_treated) > 0 and len(high_control) > 0 else 0
                    else:
                        high_effect = 0
                    
                    # Low group
                    low_group = self.data[self.data[var] <= median_val]
                    if len(low_group) > 10:
                        low_treated = low_group[low_group[treatment_var] == 1][outcome_var].dropna()
                        low_control = low_group[low_group[treatment_var] == 0][outcome_var].dropna()
                        low_effect = low_treated.mean() - low_control.mean() if len(low_treated) > 0 and len(low_control) > 0 else 0
                    else:
                        low_effect = 0
                    
                    effect_diff = abs(high_effect - low_effect)
                    if effect_diff > 0.2:  # Threshold for meaningful interaction
                        interaction_candidates.append((var, high_effect, low_effect, effect_diff))
            
            if interaction_candidates:
                self.report.append("  💡 Potential treatment interactions:")
                for var, high_eff, low_eff, diff in interaction_candidates:
                    self.report.append(f"    • {treatment_var} × {var}: Effect diff = {diff:.3f}")
                    self.report.append(f"      High {var}: {high_eff:.3f}, Low {var}: {low_eff:.3f}")
            else:
                self.report.append("  ✓ No strong interaction effects detected")
        
        # Transformation recommendations
        self.report.append("\n🔄 TRANSFORMATION RECOMMENDATIONS:")
        
        transform_recommendations = []
        
        for col in self.data.columns:
            if self.variable_info[col]['type'] == 'continuous':
                var_data = self.data[col].dropna()
                if len(var_data) > 10:
                    skew = stats.skew(var_data)
                    
                    if abs(skew) > 2:
                        if skew > 2:
                            transform_recommendations.append((col, "log transformation", "Right-skewed"))
                        else:
                            transform_recommendations.append((col, "square transformation", "Left-skewed"))
                    
                    # Check for outliers
                    q1, q3 = var_data.quantile([0.25, 0.75])
                    iqr = q3 - q1
                    outlier_count = ((var_data < q1 - 1.5*iqr) | (var_data > q3 + 1.5*iqr)).sum()
                    if outlier_count > len(var_data) * 0.05:
                        transform_recommendations.append((col, "winsorization", f"{outlier_count} outliers"))
        
        if transform_recommendations:
            for var, transform, reason in transform_recommendations:
                self.report.append(f"  💡 {var}: Consider {transform} ({reason})")
        else:
            self.report.append("  ✓ Current variable distributions appear suitable")
        
        feature_recommendations = {
            'nonlinear_candidates': nonlinear_candidates if 'nonlinear_candidates' in locals() else [],
            'interaction_candidates': interaction_candidates if 'interaction_candidates' in locals() else [],
            'transformation_recommendations': transform_recommendations
        }
        
        return feature_recommendations
    
    def generate_summary_report(self) -> str:
        """Generate final summary report."""
        summary = []
        summary.append("\n" + "="*80)
        summary.append("CAUSAL EDA SUMMARY & RECOMMENDATIONS")
        summary.append("="*80)
        
        # Data overview
        summary.append(f"\n📊 DATA OVERVIEW:")
        summary.append(f"  - Dataset: {self.data_path.name}")
        summary.append(f"  - Observations: {len(self.data):,}")
        summary.append(f"  - Variables: {len(self.data.columns)}")
        summary.append(f"  - Treatment: {self.dag_info.get('treatment_variable', 'Not specified')}")
        summary.append(f"  - Outcome: {self.dag_info.get('outcome_variable', 'Not specified')}")
        
        # Key findings and recommendations
        summary.append(f"\n🎯 KEY RECOMMENDATIONS:")
        
        # Missing data
        missing_vars = [col for col, info in self.variable_info.items() if info['missing_pct'] > 10]
        if missing_vars:
            summary.append(f"  📍 ADDRESS MISSING DATA: {len(missing_vars)} variables with >10% missing")
            summary.append(f"    Consider imputation or sensitivity analysis")
        
        # Balance
        treatment_var = self.dag_info.get('treatment_variable')
        if treatment_var and self.variable_info.get(treatment_var, {}).get('type') == 'binary':
            treated_prop = self.data[treatment_var].mean()
            if treated_prop < 0.2 or treated_prop > 0.8:
                summary.append(f"  ⚖️  IMBALANCED TREATMENT: {treated_prop:.1%} treated")
                summary.append(f"    Consider matching, weighting, or stratification")
        
        # Analysis readiness
        summary.append(f"\n🚦 ANALYSIS READINESS:")
        issues = 0
        
        if not self.dag_info.get('treatment_variable'):
            summary.append(f"  ❌ No treatment variable specified")
            issues += 1
        
        if not self.dag_info.get('outcome_variable'):
            summary.append(f"  ❌ No outcome variable specified") 
            issues += 1
        
        high_missing = sum(1 for info in self.variable_info.values() if info['missing_pct'] > 20)
        if high_missing > 0:
            summary.append(f"  ⚠️  {high_missing} variables with >20% missing data")
            issues += 1
        
        if issues == 0:
            summary.append(f"  ✅ Dataset appears ready for causal analysis")
        elif issues <= 2:
            summary.append(f"  ⚠️  Minor issues detected - proceed with caution")
        else:
            summary.append(f"  ❌ Major issues detected - address before analysis")
        
        # Files generated
        summary.append(f"\n📁 FILES GENERATED:")
        summary.append(f"  - Report: {self.output_dir}/causal_eda_report.txt")
        summary.append(f"  - Variable inventory: {self.output_dir}/variable_inventory.csv")
        for plot in self.plots_created:
            summary.append(f"  - Plot: {self.output_dir}/{plot}")
        
        return "\n".join(summary)
    
    def run_full_analysis(self) -> Dict:
        """Run complete EDA analysis."""
        logger.info("Starting comprehensive causal EDA analysis...")
        
        results = {}
        
        try:
            # Run all 10 analysis components
            results['variable_inventory'] = self.analyze_variable_inventory()
            results['univariate_distributions'] = self.analyze_univariate_distributions()
            results['bivariate_relationships'] = self.analyze_bivariate_relationships()
            results['overlap_common_support'] = self.analyze_overlap_common_support()
            results['correlation_multicollinearity'] = self.analyze_correlation_multicollinearity()
            results['temporal_patterns'] = self.analyze_temporal_patterns()
            results['instrument_validity'] = self.analyze_instrument_validity()
            results['mediation_paths'] = self.analyze_mediation_paths()
            results['potential_biases'] = self.analyze_potential_biases()
            results['feature_engineering'] = self.analyze_feature_engineering()
            
            # Generate summary
            summary = self.generate_summary_report()
            self.report.append(summary)
            
            # Save complete report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            full_report = "\n".join(self.report)
            
            report_file = self.output_dir / "causal_eda_report.txt"
            with open(report_file, 'w') as f:
                f.write(f"Causal EDA Report - Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*80 + "\n\n")
                f.write(full_report)
            
            # Save timestamped version
            timestamped_report = self.output_dir / f"causal_eda_report_{timestamp}.txt"
            with open(timestamped_report, 'w') as f:
                f.write(f"Causal EDA Report - Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*80 + "\n\n")
                f.write(full_report)
            
            # Save analysis results as JSON
            results_file = self.output_dir / "eda_results.json"
            with open(results_file, 'w') as f:
                json.dump(results, f, default=str, indent=2)
            
            logger.info(f"Analysis complete. Report saved to: {report_file}")
            logger.info(f"Generated {len(self.plots_created)} visualization plots")
            
            print(full_report)
            
            return results
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise


def main():
    """Main function to run causal EDA."""
    parser = argparse.ArgumentParser(description="Comprehensive Causal Analysis EDA")
    parser.add_argument("--data", required=True, help="Path to dataset CSV file")
    parser.add_argument("--dag", help="Path to DAG JSON file (optional)")
    parser.add_argument("--treatment", help="Treatment variable name (if no DAG)")
    parser.add_argument("--outcome", help="Outcome variable name (if no DAG)")
    parser.add_argument("--output", default="eda_output", help="Output directory")
    
    args = parser.parse_args()
    
    # Validate inputs
    if not Path(args.data).exists():
        print(f"❌ Error: Data file not found: {args.data}")
        return 1
    
    if args.dag and not Path(args.dag).exists():
        print(f"❌ Error: DAG file not found: {args.dag}")
        return 1
    
    try:
        # Run EDA
        eda = CausalEDA(
            data_path=args.data,
            dag_path=args.dag,
            treatment_col=args.treatment,
            outcome_col=args.outcome,
            output_dir=args.output
        )
        
        results = eda.run_full_analysis()
        
        print(f"\n✅ Causal EDA completed successfully!")
        print(f"📊 Results saved to: {Path(args.output).absolute()}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        logger.error(f"Analysis failed with error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())