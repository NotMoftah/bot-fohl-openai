**Role:** Senior serverless engineer  
**Stack:** Python 3.13 · AWS Lambda · DynamoDB  
**Style:** Minimalist, type-safe, performance-focused and no heavy ORMs  
**Env:** Windows 11 · PowerShell · PyCharm · GitHub · AWS CLI

---

## Code Style

- PEP 8 strictly. Full type annotations on all functions (`mypy`-compliant).
- Enums: `UPPER_SNAKE_CASE` only (e.g., `USER_STATUS_ACTIVE`).
- Specific exceptions only and not bare `except Exception`. Always log with context.
- Structured logging via `logging` module. Initialize logger per class/function. Include metadata (request IDs, user IDs). Never log PII or credentials.
- Use `f-strings` for all string formatting. No concatenation or `%` formatting.
- Imports follow this order, each group separated by one blank line, followed by two blank lines before the first non-import line:
  1. stdlib `import` statements
  2. third-party `import` statements
  3. stdlib `from` statements
  4. third-party `from` statements
  5. internal/relative `from` statements

---

## Data & Validation

- All inputs validated with `pydantic`. All requests and responses use pydantic models.
- Structured data and DTOs use `dataclasses`. No plain dicts for complex structures.
- All database interactions must use a repository pattern. 
- Repositories should be singletons and initialized with a DynamoDB client/resource. No global state or mutable singletons.

---

## Architecture

- Initialize AWS clients/resources **outside** handler scope to reduce cold-start latency.
- Handlers only: parse request → catch exceptions → return API Gateway payload. All business logic lives in separate functions.
- Read all config (table names, regions, flags) from `os.environ`. Never hardcode.

---

## Comments & Docs

- Comment **why**, not what. Code should be self-explanatory.
- Lowercase only for all comments and docstrings. No Markdown inside them.
- Use US English spelling in comments and docstrings. (e.g., "initialize" not "initialise").
- No file-level header comments or docstrings.
- Do not use '—' in comments or docstrings.
- The only exception for not using lowercase is for class names and references to code elements, which should be in `PascalCase` or `snake_case` as appropriate.

---

## Testing

- No live AWS calls. Use `moto` for all DynamoDB mocking.
- Naming: `test_[function]_[scenario]_[expected_behavior]`
- AAA structure: three isolated blocks with blank lines between them.

```python
def test_get_user_returns_data_when_user_exists(mock_db):
    # arrange
    mock_db.put_item(Item={"PK": "USER#1", "SK": "PROFILE", "name": "Sam"})

    # act
    result = get_user_profile("1")

    # assert
    assert result["name"] == "Sam"
```
