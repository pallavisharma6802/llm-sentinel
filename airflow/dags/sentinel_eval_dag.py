"""
Sentinel Eval DAG - Tests hallucination detection patterns
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.http.operators.http import SimpleHttpOperator
import json
import random


default_args = {
    'owner': 'llm-sentinel',
    'start_date': datetime(2026, 2, 28),
    'retries': 1,
}

# Test prompts covering different hallucination patterns
EVAL_PROMPTS = [
    "What AI papers did Anthropic publish this month?",  # Recent events - likely hallucinated
    "What is the capital of France?",  # Well-known fact - should be grounded
    "How many parameters does GPT-4 have?",  # Undisclosed number - may hallucinate
    "Explain the NeuroSync architecture from MIT's 2025 NeurIPS paper.",  # Fabricated - should detect
    "Who is the current CEO of OpenAI?",  # Current state - should search
]


def select_eval_prompt(**context):
    """Select a random test prompt"""
    prompt = random.choice(EVAL_PROMPTS)
    execution_date = context['execution_date']
    session_id = f"eval_{execution_date.strftime('%Y%m%d_%H%M%S')}"
    
    payload = {"prompt": prompt, "session_id": session_id}
    context['ti'].xcom_push(key='prompt', value=prompt)
    
    print(f"\n📝 Testing: {prompt}\n")
    return json.dumps(payload)


def analyze_results(**context):
    """Log the hallucination detection results"""
    ti = context['ti']
    response = ti.xcom_pull(task_ids='run_eval_query')
    prompt = ti.xcom_pull(key='prompt')
    
    if not response:
        return
    
    if isinstance(response, str):
        response = json.loads(response)
    
    is_hallucinated = response.get('is_hallucinated', False)
    sources = response.get('sources_count', 0)
    
    print(f"\n{'='*50}")
    print(f"❓ Prompt: {prompt}")
    print(f"🚨 Hallucinated: {'YES ❌' if is_hallucinated else 'NO ✅'}")
    print(f"📊 Sources: {sources}")
    print(f"{'='*50}\n")


with DAG(
    'sentinel_eval',
    default_args=default_args,
    description='LLM hallucination detection testing',
    schedule_interval='@hourly',
    catchup=False,
    tags=['sentinel', 'eval'],
) as dag:
    
    select_prompt = PythonOperator(
        task_id='select_eval_prompt',
        python_callable=select_eval_prompt,
    )
    
    run_eval_query = SimpleHttpOperator(
        task_id='run_eval_query',
        http_conn_id='agent_control_room_api',
        endpoint='/query',
        method='POST',
        data="{{ ti.xcom_pull(task_ids='select_eval_prompt') }}",
        headers={"Content-Type": "application/json"},
        response_check=lambda response: response.status_code == 200,
    )
    
    analyze_results_task = PythonOperator(
        task_id='analyze_results',
        python_callable=analyze_results,
    )
    
    select_prompt >> run_eval_query >> analyze_results_task
