#!/usr/bin/env python3
"""
Causal Analysis Agent using OpenAI SDK

This agent supports the following workflow:
1. User asks question
2. Agent identifies potential DAG from DAG library, data from data library and proposes the DAG and test architecture
3. Agent performs EDA using the EDA script, interprets the result and proposes an analysis plan
4. Once user confirms, agent runs causal_analytics and interprets the result and presents it back to the user
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import subprocess
import sys
from datetime import datetime
import logging

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, skip

# OpenAI SDK
from openai import OpenAI

# Local imports
from causal_analysis.dispatch import dispatch_query
from causal_eda import CausalEDA

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WorkflowState(Enum):
    """States of the causal analysis workflow."""
    INITIAL = "initial"
    DAG_PROPOSED = "dag_proposed"
    EDA_COMPLETED = "eda_completed"
    ANALYSIS_PLAN_PROPOSED = "analysis_plan_proposed"
    CAUSAL_ANALYSIS_COMPLETED = "causal_analysis_completed"
    COMPLETED = "completed"


@dataclass
class DAGProposal:
    """Data structure for DAG proposals."""
    dag_file: str
    data_file: str
    treatment_variable: str
    outcome_variable: str
    query_type: str
    confidence_score: float
    reasoning: str


@dataclass
class AnalysisPlan:
    """Data structure for analysis plans."""
    query_type: str
    treatment_variable: str
    outcome_variable: str
    confounders: List[str]
    methodology: str
    expected_challenges: List[str]
    reasoning: str


class CausalAnalysisAgent:
    """
    OpenAI-powered agent for causal analysis workflow.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize the causal analysis agent.
        
        Args:
            openai_api_key: OpenAI API key. If None, will use OPENAI_API_KEY environment variable
            model: OpenAI model to use
        """
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        self.client = OpenAI(api_key=api_key)
        self.model = self._get_available_model(model)
        
        # Workflow state
        self.state = WorkflowState.INITIAL
        self.conversation_history = []
        self.current_dag_proposal = None
        self.current_analysis_plan = None
        self.eda_results = None
        self.causal_results = None
        
        # Initialize file libraries
        self.dag_library = self._load_dag_library()
        self.data_library = self._load_data_library()
        
        logger.info(f"CausalAnalysisAgent initialized successfully with model: {self.model}")
    
    def _get_available_model(self, preferred_model: str) -> str:
        """Get an available model, falling back to alternatives if needed."""
        model_preferences = [
            preferred_model,
            "gpt-3.5-turbo", 
            "gpt-3.5-turbo-0125",
            "gpt-4o-mini",
            "gpt-4"
        ]
        
        for model in model_preferences:
            try:
                # Test if model is available with a minimal request
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=1
                )
                logger.info(f"Successfully verified model: {model}")
                return model
            except Exception as e:
                logger.warning(f"Model {model} not available: {e}")
                continue
        
        # If no models work, return the preferred one and let it fail with a clear message
        logger.error("No models available. Using preferred model and will fail with clear error.")
        return preferred_model
    
    def _load_dag_library(self) -> Dict[str, str]:
        """Load available DAG files from examples directory."""
        dag_library = {}
        
        # Check multiple possible DAG directories
        dag_dirs = [
            Path("data/examples"),
            Path("examples"), 
            Path("causal_analysis/config"),
            Path("backend/causal_analysis/config")
        ]
        
        for dag_dir in dag_dirs:
            if dag_dir.exists():
                for dag_file in dag_dir.glob("*.json"):
                    try:
                        with open(dag_file, 'r') as f:
                            dag_data = json.load(f)
                        
                        # Create a description based on DAG content
                        description = dag_data.get("description", "")
                        if not description:
                            vars_list = list(dag_data.get("variables", {}).keys())
                            description = f"DAG with variables: {', '.join(vars_list)}"
                        
                        dag_library[str(dag_file)] = description
                        
                    except Exception as e:
                        logger.warning(f"Failed to load DAG file {dag_file}: {e}")
        
        return dag_library
    
    def _load_data_library(self) -> Dict[str, str]:
        """Load available data files from sample_data directory."""
        data_library = {}
        
        # Check multiple possible data directories
        data_dirs = [
            Path("data/sample_data"),
            Path("sample_data"), 
            Path("data/examples"), 
            Path("examples"), 
            Path(".")
        ]
        
        for data_dir in data_dirs:
            if data_dir.exists():
                for data_file in data_dir.glob("*.csv"):
                    try:
                        # Read first few rows to understand the data
                        df = pd.read_csv(data_file, nrows=5)
                        description = f"Dataset with {len(df.columns)} columns: {', '.join(df.columns[:5])}"
                        if len(df.columns) > 5:
                            description += "..."
                        
                        data_library[str(data_file)] = description
                        
                    except Exception as e:
                        logger.warning(f"Failed to load data file {data_file}: {e}")
        
        return data_library
    
    def _call_openai(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """Call OpenAI API with error handling."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return f"Error calling OpenAI API: {str(e)}"
    
    def process_user_question(self, question: str) -> str:
        """
        Process user question and manage workflow state.
        
        Args:
            question: User's question or input
            
        Returns:
            Agent's response
        """
        # Add user question to conversation history
        self.conversation_history.append({"role": "user", "content": question})
        
        # Route based on current state
        if self.state == WorkflowState.INITIAL:
            response = self._handle_initial_question(question)
        elif self.state == WorkflowState.DAG_PROPOSED:
            response = self._handle_dag_feedback(question)
        elif self.state == WorkflowState.EDA_COMPLETED:
            response = self._handle_eda_review(question)
        elif self.state == WorkflowState.ANALYSIS_PLAN_PROPOSED:
            response = self._handle_analysis_plan_feedback(question)
        elif self.state == WorkflowState.CAUSAL_ANALYSIS_COMPLETED:
            response = self._handle_final_discussion(question)
        else:
            response = "I'm not sure how to proceed. Could you please clarify what you'd like to do?"
        
        # Add agent response to conversation history
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return response
    
    def _handle_initial_question(self, question: str) -> str:
        """Handle initial user question - identify DAG and data, propose architecture."""
        # Prepare context for OpenAI
        dag_library_str = "\n".join([f"- {path}: {desc}" for path, desc in self.dag_library.items()])
        data_library_str = "\n".join([f"- {path}: {desc}" for path, desc in self.data_library.items()])
        
        system_prompt = f"""
You are a causal analysis expert. Your task is to analyze the user's question and propose the most appropriate DAG, dataset, and analysis architecture.

Available DAGs:
{dag_library_str}

Available Datasets:
{data_library_str}

Based on the user's question, you need to:
1. Identify the most relevant DAG file and dataset
2. Determine the treatment variable, outcome variable, and query type
3. Provide reasoning for your choices
4. Give a confidence score (0-1)

Query types can be: effect_estimation, anomaly_attribution, distribution_shift_attribution, intervention, counterfactual

Return your response in the following JSON format:
{{
    "dag_file": "path/to/dag.json",
    "data_file": "path/to/data.csv", 
    "treatment_variable": "variable_name",
    "outcome_variable": "variable_name",
    "query_type": "effect_estimation",
    "confidence_score": 0.8,
    "reasoning": "Detailed explanation of why this configuration was chosen"
}}
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
        
        response = self._call_openai(messages, temperature=0.3)
        
        # Parse the JSON response
        try:
            # Extract JSON from response if it's wrapped in text
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "{" in response:
                # Find the JSON object in the response
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
            else:
                json_str = response
            
            proposal_data = json.loads(json_str)
            
            # Create DAG proposal
            self.current_dag_proposal = DAGProposal(**proposal_data)
            self.state = WorkflowState.DAG_PROPOSED
            
            # Format response for user
            user_response = f"""
Based on your question, I propose the following analysis setup:

**DAG**: {self.current_dag_proposal.dag_file}
**Dataset**: {self.current_dag_proposal.data_file}
**Treatment Variable**: {self.current_dag_proposal.treatment_variable}
**Outcome Variable**: {self.current_dag_proposal.outcome_variable}
**Query Type**: {self.current_dag_proposal.query_type}
**Confidence**: {self.current_dag_proposal.confidence_score:.1%}

**Reasoning**: {self.current_dag_proposal.reasoning}

Does this setup look correct for your analysis? If you'd like me to proceed with this configuration, please say "yes" or "proceed". If you'd like to modify anything, please let me know what changes you'd like.
"""
            
            return user_response
            
        except Exception as e:
            logger.error(f"Failed to parse DAG proposal: {e}")
            return f"I encountered an error while analyzing your question. Could you please rephrase it or provide more specific details about what you want to analyze?"
    
    def _handle_dag_feedback(self, feedback: str) -> str:
        """Handle user feedback on DAG proposal."""
        if any(word in feedback.lower() for word in ["yes", "proceed", "correct", "looks good", "ok"]):
            # User approved - proceed with EDA
            return self._run_eda()
        else:
            # User wants modifications - use AI to understand what to change
            modification_prompt = f"""
The user provided this feedback on the proposed analysis setup: "{feedback}"

Current proposal:
- DAG: {self.current_dag_proposal.dag_file}
- Dataset: {self.current_dag_proposal.data_file}
- Treatment: {self.current_dag_proposal.treatment_variable}
- Outcome: {self.current_dag_proposal.outcome_variable}
- Query Type: {self.current_dag_proposal.query_type}

Available options:
DAGs: {list(self.dag_library.keys())}
Datasets: {list(self.data_library.keys())}
Query types: effect_estimation, anomaly_attribution, distribution_shift_attribution, intervention, counterfactual

Please provide an updated proposal in the same JSON format as before, incorporating the user's feedback.
"""
            
            messages = [
                {"role": "system", "content": modification_prompt},
                {"role": "user", "content": feedback}
            ]
            
            response = self._call_openai(messages, temperature=0.3)
            
            # Parse and update proposal
            try:
                if "```json" in response:
                    json_str = response.split("```json")[1].split("```")[0].strip()
                elif "{" in response:
                    start = response.find("{")
                    end = response.rfind("}") + 1
                    json_str = response[start:end]
                else:
                    json_str = response
                
                proposal_data = json.loads(json_str)
                self.current_dag_proposal = DAGProposal(**proposal_data)
                
                return f"""
I've updated the proposal based on your feedback:

**DAG**: {self.current_dag_proposal.dag_file}
**Dataset**: {self.current_dag_proposal.data_file}
**Treatment Variable**: {self.current_dag_proposal.treatment_variable}
**Outcome Variable**: {self.current_dag_proposal.outcome_variable}
**Query Type**: {self.current_dag_proposal.query_type}
**Confidence**: {self.current_dag_proposal.confidence_score:.1%}

**Reasoning**: {self.current_dag_proposal.reasoning}

Does this updated setup look correct? Please say "yes" or "proceed" if you're ready to continue with the EDA.
"""
            
            except Exception as e:
                logger.error(f"Failed to parse modified proposal: {e}")
                return "I had trouble understanding your requested changes. Could you please be more specific about what you'd like to modify?"
    
    def _run_eda(self) -> str:
        """Run EDA analysis using the proposed configuration."""
        try:
            # Check if files exist
            dag_path = Path(self.current_dag_proposal.dag_file)
            data_path = Path(self.current_dag_proposal.data_file)
            
            if not dag_path.exists():
                return f"Error: DAG file not found at {dag_path}"
            
            if not data_path.exists():
                return f"Error: Data file not found at {data_path}"
            
            # Create output directory for this analysis
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"agent_analysis_{timestamp}"
            
            # Run EDA
            logger.info("Running EDA analysis...")
            eda = CausalEDA(
                data_path=str(data_path),
                dag_path=str(dag_path),
                output_dir=output_dir
            )
            
            self.eda_results = eda.run_full_analysis()
            self.state = WorkflowState.EDA_COMPLETED
            
            # Read the generated report
            report_file = Path(output_dir) / "causal_eda_report.txt"
            if report_file.exists():
                with open(report_file, 'r') as f:
                    report_content = f.read()
            else:
                report_content = "EDA report not generated successfully."
            
            # Use AI to interpret EDA results and create analysis plan
            return self._interpret_eda_and_propose_plan(report_content, output_dir)
            
        except Exception as e:
            logger.error(f"EDA execution failed: {e}")
            return f"I encountered an error while running the EDA analysis: {str(e)}"
    
    def _interpret_eda_and_propose_plan(self, eda_report: str, output_dir: str) -> str:
        """Interpret EDA results and propose analysis plan."""
        interpretation_prompt = f"""
You are a causal analysis expert. I've completed an EDA analysis and need you to:
1. Interpret the key findings from the EDA report
2. Propose a detailed analysis plan for the causal analysis
3. Identify potential challenges or considerations

Current analysis setup:
- Treatment: {self.current_dag_proposal.treatment_variable}
- Outcome: {self.current_dag_proposal.outcome_variable}
- Query Type: {self.current_dag_proposal.query_type}

EDA Report (truncated):
{eda_report[:3000]}...

Please provide your response in the following format:

## EDA Interpretation
[Key findings from the EDA analysis]

## Proposed Analysis Plan
**Methodology**: [Recommended causal inference method]
**Treatment Variable**: {self.current_dag_proposal.treatment_variable}
**Outcome Variable**: {self.current_dag_proposal.outcome_variable}
**Confounders**: [List of confounding variables to include]
**Expected Challenges**: [Potential issues to watch for]

## Reasoning
[Detailed explanation of your recommendations]

The analysis results are saved in: {output_dir}
"""
        
        messages = [
            {"role": "system", "content": interpretation_prompt}
        ]
        
        response = self._call_openai(messages, temperature=0.5)
        
        # Extract confounders and other details for the analysis plan
        confounders = []
        try:
            # Try to load DAG to get confounders
            with open(self.current_dag_proposal.dag_file, 'r') as f:
                dag_data = json.load(f)
            confounders = dag_data.get("confounders", [])
        except:
            pass
        
        # Create analysis plan
        self.current_analysis_plan = AnalysisPlan(
            query_type=self.current_dag_proposal.query_type,
            treatment_variable=self.current_dag_proposal.treatment_variable,
            outcome_variable=self.current_dag_proposal.outcome_variable,
            confounders=confounders,
            methodology="Linear regression with propensity score matching",
            expected_challenges=["Potential unmeasured confounding", "Sample size limitations"],
            reasoning=response
        )
        
        self.state = WorkflowState.ANALYSIS_PLAN_PROPOSED
        
        return f"""{response}

---

Based on this analysis, I'm ready to proceed with the causal analysis. The results and visualizations have been saved to: `{output_dir}/`

Would you like me to proceed with the causal analysis using this plan? Please say "yes" or "proceed" if you're ready, or let me know if you'd like to modify anything.
"""
    
    def _handle_eda_review(self, feedback: str) -> str:
        """Handle user review of EDA results (for backward compatibility)."""
        return self._handle_analysis_plan_feedback(feedback)
    
    def _handle_analysis_plan_feedback(self, feedback: str) -> str:
        """Handle user feedback on analysis plan."""
        if any(word in feedback.lower() for word in ["yes", "proceed", "correct", "looks good", "ok"]):
            # User approved - run causal analysis
            return self._run_causal_analysis()
        else:
            return f"""I understand you'd like to modify the analysis plan. 

Current plan:
- Query Type: {self.current_analysis_plan.query_type}
- Treatment: {self.current_analysis_plan.treatment_variable}
- Outcome: {self.current_analysis_plan.outcome_variable}
- Methodology: {self.current_analysis_plan.methodology}

What specific changes would you like me to make to the analysis plan?"""
    
    def _run_causal_analysis(self) -> str:
        """Run the causal analysis using the dispatch system."""
        try:
            # Create query dictionary for dispatch
            query_dict = {
                "query_type": self.current_analysis_plan.query_type,
                "treatment_variable": self.current_analysis_plan.treatment_variable,
                "outcome_variable": self.current_analysis_plan.outcome_variable,
                "confounders": self.current_analysis_plan.confounders
            }
            
            # Add query-specific parameters
            if self.current_analysis_plan.query_type == "effect_estimation":
                query_dict.update({
                    "treatment_value": 1,
                    "confounders": self.current_analysis_plan.confounders
                })
            
            logger.info("Running causal analysis...")
            
            # Run analysis
            self.causal_results = dispatch_query(
                query_dict,
                self.current_dag_proposal.dag_file,
                self.current_dag_proposal.data_file
            )
            
            self.state = WorkflowState.CAUSAL_ANALYSIS_COMPLETED
            
            # Interpret results with AI
            return self._interpret_causal_results()
            
        except Exception as e:
            logger.error(f"Causal analysis failed: {e}")
            return f"I encountered an error while running the causal analysis: {str(e)}"
    
    def _interpret_causal_results(self) -> str:
        """Interpret causal analysis results using AI."""
        results_str = json.dumps(self.causal_results, indent=2)
        
        interpretation_prompt = f"""
You are a causal analysis expert. Please interpret the following causal analysis results and provide a clear, actionable summary.

Analysis Configuration:
- Treatment: {self.current_analysis_plan.treatment_variable}
- Outcome: {self.current_analysis_plan.outcome_variable}
- Query Type: {self.current_analysis_plan.query_type}

Results:
{results_str}

Please provide:
1. **Main Finding**: The key causal effect estimate and its meaning
2. **Statistical Significance**: Whether the effect is statistically significant
3. **Practical Significance**: What this means in real-world terms
4. **Confidence**: How confident we should be in this result
5. **Limitations**: Important caveats or limitations
6. **Actionable Insights**: What decisions or actions this analysis supports

Format your response clearly with headers and bullet points where appropriate.
"""
        
        messages = [
            {"role": "system", "content": interpretation_prompt}
        ]
        
        interpretation = self._call_openai(messages, temperature=0.3)
        
        return f"""## Causal Analysis Results

{interpretation}

---

**Technical Details:**
```json
{json.dumps(self.causal_results, indent=2)}
```

This completes your causal analysis! Is there anything specific about these results you'd like me to explain further or any follow-up questions you have?
"""
    
    def _handle_final_discussion(self, question: str) -> str:
        """Handle follow-up questions about the completed analysis."""
        context_prompt = f"""
You are discussing the results of a completed causal analysis. Here's the context:

Analysis Setup:
- Treatment: {self.current_analysis_plan.treatment_variable}
- Outcome: {self.current_analysis_plan.outcome_variable}
- Query Type: {self.current_analysis_plan.query_type}

Results Summary:
{json.dumps(self.causal_results, indent=2)}

The user is asking a follow-up question about the analysis. Please provide a helpful response based on the completed analysis.
"""
        
        messages = [
            {"role": "system", "content": context_prompt},
            {"role": "user", "content": question}
        ]
        
        return self._call_openai(messages, temperature=0.5)
    
    def reset(self):
        """Reset the agent to initial state."""
        self.state = WorkflowState.INITIAL
        self.conversation_history = []
        self.current_dag_proposal = None
        self.current_analysis_plan = None
        self.eda_results = None
        self.causal_results = None
        logger.info("Agent reset to initial state")
    
    def get_state_info(self) -> Dict[str, Any]:
        """Get current state information."""
        return {
            "state": self.state.value,
            "has_dag_proposal": self.current_dag_proposal is not None,
            "has_analysis_plan": self.current_analysis_plan is not None,
            "has_eda_results": self.eda_results is not None,
            "has_causal_results": self.causal_results is not None,
            "conversation_length": len(self.conversation_history)
        }


def main():
    """Main function to run the agent interactively."""
    print("🤖 Causal Analysis Agent")
    print("=" * 50)
    print("I'm here to help you with causal analysis!")
    print("Ask me a question about what you'd like to analyze, and I'll guide you through the process.")
    print("Type 'quit' to exit, 'reset' to start over, or 'status' to see current state.")
    print()
    
    # Initialize agent
    try:
        agent = CausalAnalysisAgent()
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        print("Make sure your OPENAI_API_KEY environment variable is set.")
        return
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye!")
                break
            
            if user_input.lower() == 'reset':
                agent.reset()
                print("🔄 Agent reset. You can start a new analysis.")
                continue
            
            if user_input.lower() == 'status':
                state_info = agent.get_state_info()
                print(f"📊 Current State: {state_info}")
                continue
            
            if not user_input:
                continue
            
            print("🤖 Agent: ", end="")
            response = agent.process_user_question(user_input)
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            logger.error(f"Error in main loop: {e}")


if __name__ == "__main__":
    main()