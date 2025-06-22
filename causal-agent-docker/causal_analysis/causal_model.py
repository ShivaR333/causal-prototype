import json
import pandas as pd
import networkx as nx
from pathlib import Path
from typing import Dict, List, Optional, Union
from dowhy import CausalModel as DoWhyCausalModel


class CausalModel:
    """
    Wrapper class for DoWhy's CausalModel that loads DAG from JSON configuration.
    """
    
    def __init__(self, dag_config: Union[str, Path, Dict], data: Optional[pd.DataFrame] = None):
        """
        Initialize CausalModel with DAG configuration and optional data.
        
        Args:
            dag_config: Path to JSON file or dictionary containing DAG configuration
            data: Optional pandas DataFrame to attach to the model
        """
        self.dag_config = self._load_dag_config(dag_config)
        self.data = data
        self.dowhy_model = None
        self.graph = self._build_networkx_graph()
        
        if data is not None:
            self._create_dowhy_model()
    
    def _load_dag_config(self, dag_config: Union[str, Path, Dict]) -> Dict:
        """Load DAG configuration from file or dictionary."""
        if isinstance(dag_config, (str, Path)):
            with open(dag_config, 'r') as f:
                return json.load(f)
        elif isinstance(dag_config, dict):
            return dag_config
        else:
            raise ValueError("dag_config must be a file path or dictionary")
    
    def _build_networkx_graph(self) -> nx.DiGraph:
        """Build NetworkX directed graph from DAG configuration."""
        graph = nx.DiGraph()
        
        # Add nodes with metadata
        for var_name, var_info in self.dag_config["variables"].items():
            graph.add_node(var_name, **var_info)
        
        # Add edges
        for edge in self.dag_config["edges"]:
            graph.add_edge(edge["from"], edge["to"])
        
        return graph
    
    def _create_dowhy_model(self):
        """Create DoWhy CausalModel instance."""
        if self.data is None:
            raise ValueError("Data must be attached before creating DoWhy model")
        
        # Extract treatment and outcome variables
        treatment = self.dag_config.get("treatment_variable")
        outcome = self.dag_config.get("outcome_variable")
        
        if not treatment or not outcome:
            raise ValueError("DAG configuration must specify treatment_variable and outcome_variable")
        
        # Create DoWhy model with simplified approach for DoWhy 0.12+
        try:
            # Use NetworkX graph directly instead of DOT format
            self.dowhy_model = DoWhyCausalModel(
                data=self.data,
                treatment=treatment,
                outcome=outcome,
                graph=self.graph,
                instruments=self.dag_config.get("instruments"),
                common_causes=self.dag_config.get("confounders")
            )
        except Exception as e:
            # Fallback for compatibility issues
            # Shiva: Check how this operates given no graph is provided.
            try:
                self.dowhy_model = DoWhyCausalModel(
                    data=self.data,
                    treatment=treatment,
                    outcome=outcome,
                    common_causes=self.dag_config.get("confounders")
                )
            except Exception as e2:
                raise ValueError(f"DoWhy model creation failed: {e2}")
    
    def _convert_to_dot(self) -> str:
        """Convert NetworkX graph to DOT notation for DoWhy."""
        dot_lines = ["digraph {"]
        
        # Add nodes
        for node in self.graph.nodes():
            dot_lines.append(f'  "{node}";')
        
        # Add edges  
        for edge in self.graph.edges():
            dot_lines.append(f'  "{edge[0]}" -> "{edge[1]}";')
        
        dot_lines.append("}")
        return "\n".join(dot_lines)
    
    def attach_data(self, data: pd.DataFrame):
        """Attach pandas DataFrame to the model."""
        self.data = data
        self._validate_data()
        self._create_dowhy_model()
    
    def _validate_data(self):
        """Validate that data contains all required variables."""
        if self.data is None:
            return
        
        required_vars = set(self.dag_config["variables"].keys())
        data_vars = set(self.data.columns)
        
        missing_vars = required_vars - data_vars
        if missing_vars:
            raise ValueError(f"Data is missing required variables: {missing_vars}")
    
    @property
    def variables(self) -> Dict:
        """Get variable metadata from DAG configuration."""
        return self.dag_config["variables"]
    
    @property
    def edges(self) -> List[Dict]:
        """Get edges from DAG configuration."""
        return self.dag_config["edges"]
    
    @property
    def treatment_variable(self) -> Optional[str]:
        """Get treatment variable name."""
        return self.dag_config.get("treatment_variable")
    
    @property
    def outcome_variable(self) -> Optional[str]:
        """Get outcome variable name."""
        return self.dag_config.get("outcome_variable")
    
    @property
    def confounders(self) -> Optional[List[str]]:
        """Get confounder variable names."""
        return self.dag_config.get("confounders")
    
    def get_parents(self, variable: str) -> List[str]:
        """Get parent variables for a given variable."""
        return list(self.graph.predecessors(variable))
    
    def get_children(self, variable: str) -> List[str]:
        """Get child variables for a given variable."""
        return list(self.graph.successors(variable))
    
    def identify_effect(self, **kwargs):
        """Identify causal effect using DoWhy."""
        if self.dowhy_model is None:
            raise ValueError("DoWhy model not created. Attach data first.")
        return self.dowhy_model.identify_effect(**kwargs)
    
    def estimate_effect(self, identified_estimand, **kwargs):
        """Estimate causal effect using DoWhy."""
        if self.dowhy_model is None:
            raise ValueError("DoWhy model not created. Attach data first.")
        return self.dowhy_model.estimate_effect(identified_estimand, **kwargs)
    
    def refute_estimate(self, estimate, **kwargs):
        """Refute causal estimate using DoWhy."""
        if self.dowhy_model is None:
            raise ValueError("DoWhy model not created. Attach data first.")
        return self.dowhy_model.refute_estimate(estimate, **kwargs)