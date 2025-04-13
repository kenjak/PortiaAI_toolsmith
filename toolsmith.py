from dotenv import load_dotenv
from portia import Config, Portia, PortiaToolRegistry
from portia.cli import CLIExecutionHooks
import os

load_dotenv(override=True)

# --- Step 1: Initialize Portia ---
from pydantic import SecretStr
from portia.config import Config

config = Config.from_default()
portia = Portia(
    config=config,
    tools=PortiaToolRegistry(config),

    execution_hooks=CLIExecutionHooks()
)

# --- Step 2: Ask User for Tool Description ---
tool_name = input("Name of your tool:\n")
tool_purpose = input("What should it do?\n")
tool_inputs = input("What are the inputs? (e.g., 'text: str, count: int'):\n")
tool_output = input("What is the expected output? (e.g., 'List[str]'):\n")

# --- Step 3: Ask Portia to Generate a Plan ---


def tool_prompt(original_code=None, feedback=None):
    if feedback and original_code:
        return f"""
You previously created a Python function based on a user request.

Here is the original function code:
{original_code}

Here is the feedback from a code reviewer:
{feedback}

Please revise and improve the function accordingly. Keep the same structure, inputs, and purpose. Do not remove any existing logic unless it's incorrect. Only make improvements based on the review.

Return only the improved Python function code. Do not include any explanation, description, or markdown syntax.
"""


    else:

        return f"""
You are a coding assistant. Write a complete Python function called `{tool_name}`.

📌 Purpose:
{tool_purpose}

🔢 Inputs:
{tool_inputs}

🎯 Expected Output:
{tool_output}

✅ Requirements:
- Use full Python syntax with type hints.
- Include a detailed docstring describing the function's purpose, parameters, and return value.
- Return actual, working Python code (not a description or summary).
- Output only the code. Do not explain anything or include text before/after the function.

{"🔁 Revision feedback: " + feedback if feedback else ""}
"""

# Step 1: Plan the task
plan = portia.plan(tool_prompt())
print("\n🧠 Generated Plan Steps:")
for step in plan.steps:
    print(step.model_dump_json(indent=2))

# Step 2: Run the plan
print("\n🚀 Running the plan to generate code...")
plan_run = portia.run_plan(plan)

# Step 3: Extract the result

#print("\n--- RAW OUTPUTS ---")
#print(type(plan_run.outputs))
#print(dir(plan_run.outputs))  # See its methods/fields
print("\n--- What is step_outputs? ---")
print(type(plan_run.outputs))
print(dir(plan_run.outputs))

# Now try this more cautiously
step_outputs = getattr(plan_run.outputs, "step_outputs", None)

if step_outputs is None:
    print("❌ step_outputs is missing!")
else:
    print(f"✅ step_outputs is a {type(step_outputs)}")
    print("🔍 Contents:", step_outputs)

# Grab the dictionary
step_outputs = plan_run.outputs.step_outputs

# Grab the first key (we assume only one tool output for now)
output_key = list(step_outputs.keys())[0]

# Get the actual code string
generated_code = step_outputs[output_key].value.strip()

print(f"\n🧩 Output Key: {output_key}")
print("\n🔧 Final Generated Code:\n")
print(generated_code)





filename = f"{tool_name}.py"
with open(filename, "w") as f:
    f.write(generated_code)
print(f"✅ Saved to {filename}")

import os
print(f"🔎 Absolute file path: {os.path.abspath(filename)}")
print(f"📂 File exists? {os.path.exists(filename)}")


from review_tool import review_tool

# Step 1: Run the review
review = review_tool(generated_code)
print("\n🧠 Review of Initial Tool:\n")
print(review)

# Step 2: Ask user if they want to regenerate with feedback
use_feedback = input("\nWould you like to improve the tool using this feedback? (y/n): ").strip().lower()

if use_feedback == "y":
    #improved_plan = portia.plan(tool_prompt(feedback=review))
    improved_plan = portia.plan(tool_prompt(original_code=generated_code, feedback=review))

    improved_run = portia.run_plan(improved_plan)

    # Extract improved code
    improved_outputs = improved_run.outputs.step_outputs
    improved_key = list(improved_outputs.keys())[0]
    improved_code = improved_outputs[improved_key].value.strip()

    print("\n✨ Improved Tool Code:\n")
    print(improved_code)

    # Save improved version
    improved_filename = f"{tool_name}_improved.py"


    # Clean out markdown fences like ```python ... ``` before saving
    cleaned_code = (
        improved_code.replace("```python", "")
        .replace("```", "")
        .strip()
    )

    with open(improved_filename, "w") as f:
        f.write(cleaned_code)







    print(f"✅ Improved tool saved to {improved_filename}")
    print(f"🔎 Path: {os.path.abspath(improved_filename)}")
    print(f"📂 File exists? {os.path.exists(improved_filename)}")

else:
    print("✅ Keeping original version only.")

exit()
