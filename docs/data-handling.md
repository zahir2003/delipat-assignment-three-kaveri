# Data Handling

The assignment terms state that contract values, rates and client data must not be sent to external AI services.

Therefore:

- Raw supplied data remains local and is not committed to the public repository.
- Ollama is used locally for execution-log language extraction.
- Deterministic Python code performs all financial calculations.
- ClickUp AI is tested only within the assignment workspace and its results are verified against independently computed figures.
