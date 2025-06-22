import numpy as np
import pandas as pd
import json
import networkx as nx
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path

class SyntheticDataGenerator:
    """
    Generates synthetic datasets based on DAG structure with known causal relationships.
    """
    
    def __init__(self, dag_config: Union[str, Dict], seed: Optional[int] = 42):
        """
        Initialize the synthetic data generator.
        
        Args:
            dag_config: Path to DAG JSON file or dictionary containing DAG configuration
            seed: Random seed for reproducibility
        """
        self.seed = seed
        # Set the seed for numpy random number generator
        np.random.seed(seed)
        
        if isinstance(dag_config, str):
            with open(dag_config, 'r') as f:
                self.dag_config = json.load(f)
        else:
            self.dag_config = dag_config
            
        self.variables = self.dag_config.get('variables', {})
        self.edges = self.dag_config.get('edges', [])
        self.graph = self._build_graph()
        self.topological_order = list(nx.topological_sort(self.graph))
        
    def _build_graph(self) -> nx.DiGraph:
        """Build NetworkX graph from DAG configuration."""
        G = nx.DiGraph()
        
        # Add nodes
        for var_name in self.variables.keys():
            G.add_node(var_name)
            
        # Add edges
        for edge in self.edges:
            G.add_edge(edge['from'], edge['to'])
            
        if not nx.is_directed_acyclic_graph(G):
            raise ValueError("The provided graph is not a DAG")
            
        return G
    
    def generate_data(self, 
                     n_samples: int = 1000,
                     treatment_effect: float = 2.0,
                     noise_std: float = 0.5,
                     confounder_strength: float = 1.0) -> pd.DataFrame:
        """
        Generate synthetic dataset with known causal relationships.
        
        Args:
            n_samples: Number of samples to generate
            treatment_effect: True causal effect of treatment on outcome
            noise_std: Standard deviation of noise terms
            confounder_strength: Strength of confounding relationships
            
        Returns:
            DataFrame with synthetic data
        """
        data = {}
        
        # Generate variables in topological order
        for var_name in self.topological_order:
            var_config = self.variables[var_name]
            var_type = var_config.get('type', 'continuous')
            
            # Get parents of this variable
            parents = list(self.graph.predecessors(var_name))
            
            if var_type == 'binary':
                data[var_name] = self._generate_binary_variable(
                    n_samples, var_name, parents, data, treatment_effect, 
                    noise_std, confounder_strength
                )
            elif var_type == 'continuous':
                data[var_name] = self._generate_continuous_variable(
                    n_samples, var_name, parents, data, treatment_effect,
                    noise_std, confounder_strength
                )
            elif var_type == 'categorical':
                data[var_name] = self._generate_categorical_variable(
                    n_samples, var_name, parents, data, treatment_effect,
                    noise_std, confounder_strength
                )
                
        return pd.DataFrame(data)
    
    def _generate_continuous_variable(self, n_samples: int, var_name: str, 
                                    parents: List[str], data: Dict,
                                    treatment_effect: float, noise_std: float,
                                    confounder_strength: float) -> np.ndarray:
        """Generate continuous variable based on its parents."""
        if not parents:
            # Root node - generate from normal distribution
            return np.random.normal(0, 1, n_samples)
        
        # Linear combination of parents with noise
        values = np.random.normal(0, noise_std, n_samples)
        
        for parent in parents:
            parent_values = data[parent]
            
            # Define relationship strength based on variable roles
            if self._is_treatment_outcome_relationship(parent, var_name):
                # This is the causal effect we want to estimate
                coeff = treatment_effect
            elif self._is_confounder_relationship(parent, var_name):
                # Confounding relationship
                coeff = confounder_strength
            else:
                # Default relationship strength
                coeff = 0.5
                
            values += coeff * parent_values
            
        return values
    
    def _generate_binary_variable(self, n_samples: int, var_name: str,
                                parents: List[str], data: Dict,
                                treatment_effect: float, noise_std: float,
                                confounder_strength: float) -> np.ndarray:
        """Generate binary variable using logistic function."""
        if not parents:
            # Root node - generate from Bernoulli with p=0.5
            return np.random.binomial(1, 0.5, n_samples)
        
        # Linear combination of parents
        linear_combination = np.zeros(n_samples)
        
        for parent in parents:
            parent_values = data[parent]
            
            if self._is_treatment_outcome_relationship(parent, var_name):
                coeff = treatment_effect
            elif self._is_confounder_relationship(parent, var_name):
                coeff = confounder_strength
            else:
                coeff = 0.5
                
            linear_combination += coeff * parent_values
        
        # Apply logistic function to get probabilities
        probabilities = 1 / (1 + np.exp(-linear_combination))
        
        # Generate binary outcomes
        return np.random.binomial(1, probabilities, n_samples)
    
    def _generate_categorical_variable(self, n_samples: int, var_name: str,
                                     parents: List[str], data: Dict,
                                     treatment_effect: float, noise_std: float,
                                     confounder_strength: float) -> np.ndarray:
        """Generate categorical variable (simplified as 3-category)."""
        if not parents:
            # Root node - generate from uniform categorical
            return np.random.choice([0, 1, 2], n_samples)
        
        # Use multinomial logistic for simplicity
        # For now, collapse to binary then expand
        binary_version = self._generate_binary_variable(
            n_samples, var_name, parents, data, treatment_effect,
            noise_std, confounder_strength
        )
        
        # Convert binary to 3-category with some randomness
        categorical = np.where(
            binary_version == 1,
            np.random.choice([1, 2], n_samples, p=[0.7, 0.3]),
            0
        )
        
        return categorical
    
    def _is_treatment_outcome_relationship(self, parent: str, child: str) -> bool:
        """Check if this is the main treatment-outcome relationship."""
        treatment_var = self.dag_config.get('treatment_variable', '')
        outcome_var = self.dag_config.get('outcome_variable', '')
        return parent == treatment_var and child == outcome_var
    
    def _is_confounder_relationship(self, parent: str, child: str) -> bool:
        """Check if parent is a confounder affecting child."""
        confounders = self.dag_config.get('confounders', [])
        treatment_var = self.dag_config.get('treatment_variable', '')
        outcome_var = self.dag_config.get('outcome_variable', '')
        
        return (parent in confounders and 
                (child == treatment_var or child == outcome_var))
    
    def generate_multiple_datasets(self, 
                                 n_datasets: int = 5,
                                 n_samples: int = 1000,
                                 treatment_effects: Optional[List[float]] = None,
                                 **kwargs) -> List[Tuple[pd.DataFrame, float]]:
        """
        Generate multiple datasets with different treatment effects.
        
        Returns:
            List of tuples (dataframe, true_treatment_effect)
        """
        if treatment_effects is None:
            treatment_effects = np.linspace(0.5, 3.0, n_datasets)
        
        datasets = []
        
        for i, effect in enumerate(treatment_effects):
            # Use different seed for each dataset
            np.random.seed(self.seed + i)
            
            df = self.generate_data(
                n_samples=n_samples,
                treatment_effect=effect,
                **kwargs
            )
            
            datasets.append((df, effect))
            
        return datasets
    
    def save_data(self, data: pd.DataFrame, filepath: str) -> None:
        """Save generated data to CSV file."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        data.to_csv(filepath, index=False)
        
    def get_data_summary(self, data: pd.DataFrame) -> Dict:
        """Get summary statistics of generated data."""
        summary = {
            'n_samples': len(data),
            'n_variables': len(data.columns),
            'variables': {}
        }
        
        for col in data.columns:
            col_data = data[col]
            var_summary = {
                'type': str(col_data.dtype),
                'mean': float(col_data.mean()),
                'std': float(col_data.std()),
                'min': float(col_data.min()),
                'max': float(col_data.max()),
                'unique_values': int(col_data.nunique())
            }
            
            if col_data.nunique() <= 10:  # Likely categorical
                var_summary['value_counts'] = col_data.value_counts().to_dict()
                
            summary['variables'][col] = var_summary
            
        return summary