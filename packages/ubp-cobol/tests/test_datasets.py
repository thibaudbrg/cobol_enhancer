from datetime import datetime

import langsmith
from langchain import chat_models, smith
from langchain_openai import ChatOpenAI

from ubp_cobol.common import MODEL_NAME

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
    eval_llm=chat_models.ChatOpenAI(model="gpt-4", temperature=0)
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
        tag="gpt-4-turbo-preview"
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
        tag="gpt-4-turbo-preview"
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
        tag="gpt-4-turbo-preview"
    )


def test_extender():
    client = langsmith.Client()
    chain_results = client.run_on_dataset(
        dataset_name="extender_dataset",
        llm_or_chain_factory=model,
        evaluation=eval_config,
        project_name=f"extender-{date}",
        concurrency_level=5,
        verbose=True,
        tag="gpt-4-turbo-preview"
    )
