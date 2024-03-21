from datetime import datetime

import langsmith
from langchain import smith

from langchain_openai import ChatOpenAI
from app.cobol_enhancer.common import MODEL_NAME

date = int(datetime.now().strftime('%Y%m%d%H%M%S'))
model = ChatOpenAI(temperature=0, model=MODEL_NAME, streaming=True)

# Define the evaluators to apply
eval_config = smith.RunEvalConfig(
    evaluators=[
        "cot_qa",
        smith.RunEvalConfig.LabeledCriteria("conciseness"),
        smith.RunEvalConfig.LabeledCriteria("coherence")
    ],
    custom_evaluators=[],
    eval_llm=ChatOpenAI(model="gpt-4", temperature=0)
)


def test_process_next_file():
    client = langsmith.Client()
    chain_results = client.run_on_dataset(
        dataset_name="process_next_file_dataset",
        llm_or_chain_factory=model,
        evaluation=eval_config,
        project_name=f"process_next_file-{date}",
        concurrency_level=5,
        verbose=True,
    )


def test_critic_generation():
    client = langsmith.Client()
    chain_results = client.run_on_dataset(
        dataset_name="critic_generation_dataset",
        llm_or_chain_factory=model,
        evaluation=eval_config,
        project_name=f"critic_generation-{date}",
        concurrency_level=5,
        verbose=True,
    )

def test_critic_generation_2():
    client = langsmith.Client()
    chain_results = client.run_on_dataset(
        dataset_name="critic_generation_dataset_2",
        llm_or_chain_factory=model,
        evaluation=eval_config,
        project_name=f"critic_generation-{date}",
        concurrency_level=5,
        verbose=True,
    )


def test_new_generation():
    client = langsmith.Client()
    chain_results = client.run_on_dataset(
        dataset_name="new_generation_dataset",
        llm_or_chain_factory=model,
        evaluation=eval_config,
        project_name=f"new_generation-{date}",
        concurrency_level=5,
        verbose=True,
    )