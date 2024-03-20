from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from .common import MODEL_NAME, GraphState
from .prompts import critic_generation_prompt, new_generation_prompt
from .utils import print_heading, print_info, print_error, sanitize_output, \
    format_copybooks_for_display, print_code_comparator, get_previous_critic_description


def critic_generation(state: GraphState) -> GraphState:
    print_heading("CRITIC GENERATION")

    # Concatenate the base prompt with the detailed sections
    template = critic_generation_prompt(state)

    # Set up the model and the structured output parser
    model = ChatOpenAI(temperature=0, model=MODEL_NAME, streaming=True)

    # Define the Pydantic model for structured output
    class CodeReviewResult(BaseModel):
        description: str = Field(description="The written critique of the code comparison.")
        grade: str = Field(description="Binary score 'good' or 'bad'.")

    # Use the full prompt to call the model with structured output
    chain = ChatPromptTemplate.from_template(template) | model.with_structured_output(CodeReviewResult)

    # Invoke the chain with the filled-out prompt
    try:
        critic_response = chain.invoke({
            "old_code": state["old_code"],
            "previous_iteration_code": state.get("previous_last_gen_code", ""),
            "specific_demands": state.get("specific_demands", ""),
            "previous_critic_description": get_previous_critic_description(state),
            "atlas_answer": state.get("atlas_answer", ""),
            "new_code": state["new_code"],
            "atlas_message_type": (state.get("atlas_message_type") or "").replace('_', ' ').capitalize()
        })

        # Update the state with the critic information
        state["critic"] = critic_response.dict()

        print_info(f"Critic Description: {state['critic']['description']}")
        print_info(f"Critic Grade: {state['critic']['grade']}")
    except Exception as e:
        print_error(f"Error during critic generation: {e}")
        # Provide default values in case of an error
        state["critic"] = {"description": "An error occurred during critique generation.", "grade": "bad"}

    return state


def human_review(state: GraphState) -> GraphState:
    print_heading("HUMAN REVIEW")

    print_code_comparator(state["old_code"], state["new_code"])

    decision_made = False
    specific_demands_provided = False

    while not decision_made:
        human_decision = input("Accept changes? (yes/no): ").strip().lower()
        if human_decision == "yes":
            print_info("Changes accepted. Moving to the next file.")
            state["specific_demands"] = ""
            decision_made = True
            state["human_decision"] = "yes"
        elif human_decision == "no" and not specific_demands_provided:
            print_error("Changes not accepted. Please provide specific demands for regeneration:")
            specific_demands = input("Enter demands: ").strip()
            state["specific_demands"] = specific_demands
            specific_demands_provided = True
            state["human_decision"] = "no"

            # Ask if they want to reconsider their decision
            reconsider = input("Would you like to reconsider accepting the changes? (yes/no): ").strip().lower()
            if reconsider == "yes":
                decision_made = True  # They've reconsidered; exit loop
                state["human_decision"] = "yes"
            elif reconsider == "no":
                print_info("Understood. Keeping the original decision to reject the changes.")
                decision_made = True  # Confirming their decision to reject; exit loop
                state["human_decision"] = "no"
            else:
                print_error("Error: Please enter 'yes' or 'no'.")
        else:
            print_error("Error: Please enter 'yes' or 'no'.")

    return state


def new_generation(state: GraphState) -> GraphState:
    print_heading("NEW GENERATION BASED ON FEEDBACK")

    template = new_generation_prompt(state)

    prompt = ChatPromptTemplate.from_template(template)
    model = ChatOpenAI(temperature=0, model=MODEL_NAME, streaming=True)

    chain = prompt | model | StrOutputParser()

    # Invoke the OpenAI model with the formatted prompt
    result = chain.invoke({
        "filename": state["filename"],
        "critic": state.get("critic", {}).get("description", ""),
        "specific_demands": state.get("specific_demands", ""),
        "metadata": state["metadata"],
        "copybooks": format_copybooks_for_display(state["copybooks"]),
        "old_code": state["old_code"],
        "new_code": state["new_code"],
        "atlas_answer": state.get("atlas_answer", ""),
        "atlas_message_type": (state.get("atlas_message_type") or "").replace('_', ' ').capitalize()
    })

    state["previous_last_gen_code"] = state.get("new_code", "")
    state["new_code"] = sanitize_output(result)

    # Reset atlas-related state information if it was used during this execution
    if "atlas_message_type" in state and state["atlas_message_type"]:
        state["atlas_answer"] = ""
        state["atlas_message_type"] = ""

    return state
