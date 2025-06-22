import click
import json
from pathlib import Path
from ..dispatch import dispatch_query

@click.group()
def cli():
    """Causal Analysis CLI Tool"""
    pass

@cli.command()
@click.option('--treatment', required=True, help='Treatment variable name')
@click.option('--outcome', required=True, help='Outcome variable name')
@click.option('--confounders', help='Comma-separated list of confounder variables')
@click.option('--dag-file', default='causal_analysis/config/sample_dag.json', help='Path to DAG configuration file')
@click.option('--data-file', required=True, help='Path to dataset file (CSV)')
@click.option('--treatment-value', type=float, help='Specific treatment value for analysis')
def analyze(treatment, outcome, confounders, dag_file, data_file, treatment_value):
    """Run causal effect estimation analysis."""
    try:
        # Parse confounders
        confounder_list = []
        if confounders:
            confounder_list = [c.strip() for c in confounders.split(',')]
        
        # Create query
        query = {
            "query_type": "effect_estimation",
            "treatment_variable": treatment,
            "outcome_variable": outcome,
            "confounders": confounder_list,
            "treatment_value": treatment_value
        }
        
        # Execute query
        result = dispatch_query(query, dag_file, data_file)
        
        # Display results
        click.echo(json.dumps(result, indent=2))
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)

@cli.command()
@click.option('--query-file', required=True, help='Path to JSON file containing query')
@click.option('--dag-file', default='causal_analysis/config/sample_dag.json', help='Path to DAG configuration file')
@click.option('--data-file', required=True, help='Path to dataset file (CSV)')
def query(query_file, dag_file, data_file):
    """Execute causal query from JSON file."""
    try:
        # Load query from file
        with open(query_file, 'r') as f:
            query_json = json.load(f)
        
        # Execute query
        result = dispatch_query(query_json, dag_file, data_file)
        
        # Display results
        click.echo(json.dumps(result, indent=2))
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)

@cli.command()
@click.option('--outcome', required=True, help='Outcome variable name')
@click.option('--threshold', required=True, type=float, help='Anomaly threshold value')
@click.option('--causes', required=True, help='Comma-separated list of potential causes')
@click.option('--dag-file', default='causal_analysis/config/sample_dag.json', help='Path to DAG configuration file')
@click.option('--data-file', required=True, help='Path to dataset file (CSV)')
def anomaly(outcome, threshold, causes, dag_file, data_file):
    """Run anomaly attribution analysis."""
    try:
        # Parse potential causes
        cause_list = [c.strip() for c in causes.split(',')]
        
        # Create query
        query = {
            "query_type": "anomaly_attribution",
            "outcome_variable": outcome,
            "anomaly_threshold": threshold,
            "potential_causes": cause_list
        }
        
        # Execute query
        result = dispatch_query(query, dag_file, data_file)
        
        # Display results
        click.echo(json.dumps(result, indent=2))
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)

@cli.command()
@click.option('--intervention-var', required=True, help='Variable to intervene on')
@click.option('--intervention-value', required=True, type=float, help='Value to set intervention variable to')
@click.option('--outcomes', required=True, help='Comma-separated list of outcome variables')
@click.option('--dag-file', default='causal_analysis/config/sample_dag.json', help='Path to DAG configuration file')
@click.option('--data-file', required=True, help='Path to dataset file (CSV)')
def intervention(intervention_var, intervention_value, outcomes, dag_file, data_file):
    """Run intervention analysis."""
    try:
        # Parse outcome variables
        outcome_list = [o.strip() for o in outcomes.split(',')]
        
        # Create query
        query = {
            "query_type": "intervention",
            "intervention_variable": intervention_var,
            "intervention_value": intervention_value,
            "outcome_variables": outcome_list
        }
        
        # Execute query
        result = dispatch_query(query, dag_file, data_file)
        
        # Display results
        click.echo(json.dumps(result, indent=2))
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)

if __name__ == '__main__':
    cli()