VERYSHORT_TEMPLATE = """{PROMPT}"""

SHORT_TEMPLATE = """```python
{PROMPT}"""

H2O_TEMPLATE = """<|prompt|>{PROMPT}<|endoftext|><|answer|>```python
"""
######

ALPACA_PREFIX_TEMPLATE = """Below is an instruction that describes a task. 
Write a response that appropriately completes the request.

### Instruction:
Complete the following Python code: 
Notes: respond with the entire complete function definition
do not add any comments, be as concise in your code as possible
use only built-in libraries, assume no additional imports other than those provided (if any)

code:
{PROMPT}

### Response:
```python
"""

ALPACA_PREFIX_TEMPLATE_MEDIUM = """Below is an instruction that describes a task. 
Write a response that appropriately completes the request.

### Instruction:
Please complete the following code:
{PROMPT}

### Response:
```python
"""

ALPACA_PREFIX_TEMPLATE_MD = """Below is an instruction that describes a task.\n Write a response that appropriately completes the request.

### Instruction:
Complete the following Python code: 
Notes: respond with the entire complete function definition
do not add any comments, be as concise in your code as possible
use only built-in libraries, assume no additional imports other than those provided (if any)

code:
```python
{PROMPT}
```

### Response:
```python
"""

######

QA_TEMPLATE = """Q: Complete the following Python code: 
Notes: respond with the entire complete function definition
do not add any comments, be as concise in your code as possible
use only built-in libraries, assume no additional imports other than those provided (if any)

code:
{PROMPT}

A:
```python
"""

QA_TEMPLATE_MD = """Q: Complete the following Python code: 
Notes: respond with the entire complete function definition
do not add any comments, be as concise in your code as possible
use only built-in libraries, assume no additional imports other than those provided (if any)

code:
```python
{PROMPT}
```

A:
```python
"""

QA_TEMPLATE_MEDIUM = """Q: Please complete the following code:
{PROMPT}

A:
```python
"""

######

FALCON_TEMPLATE = """[|Human|] Complete the following Python code: 
Notes: respond with the entire complete function definition
do not add any comments, be as concise in your code as possible
use only built-in libraries, assume no additional imports other than those provided (if any)

code:
{PROMPT}

[|AI|]
```python
"""

FALCON_TEMPLATE_MEDIUM = """[|Human|] Please complete the following code:
{PROMPT}

[|AI|]
```python
"""

FALCON_TEMPLATE_MD = """[|Human|] Complete the following Python code: 
Notes: respond with the entire complete function definition
do not add any comments, be as concise in your code as possible
use only built-in libraries, assume no additional imports other than those provided (if any)

code:
```python
{PROMPT}
```

[|AI|]
```python
"""

######

OPENASSISTANT_TEMPLATE = """<|prompter|> Complete the following Python code: 
Notes: respond with the entire complete function definition
do not add any comments, be as concise in your code as possible
use only built-in libraries, assume no additional imports other than those provided (if any)

code:
{PROMPT}

<|assistant|>:
```python
"""

OPENASSISTANT_TEMPLATE_MEDIUM = """<|prompter|> Please complete the following code:
{PROMPT}

<|assistant|>:
```python
"""

OPENASSISTANT_TEMPLATE_MD = """<|prompter|> Complete the following Python code: 
Notes: respond with the entire complete function definition
do not add any comments, be as concise in your code as possible
use only built-in libraries, assume no additional imports other than those provided (if any)

code:
```python
{PROMPT}
```

<|assistant|>:
```python
"""

######

VICUNA_TEMPLATE = """A chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the user's questions.

USER: Complete the following Python code: 
Notes: respond with the entire complete function definition
do not add any comments, be as concise in your code as possible
use only built-in libraries, assume no additional imports other than those provided (if any)

code:
{PROMPT}

ASSISTANT:
```python
"""

VICUNA_TEMPLATE_MEDIUM = """A chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the user's questions.

USER: Please complete the following code:
{PROMPT}

ASSISTANT:
```python
"""

VICUNA_TEMPLATE_MD = """A chat between a curious user and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the user's questions.

USER: Complete the following Python code: 
Notes: respond with the entire complete function definition
do not add any comments, be as concise in your code as possible
use only built-in libraries, assume no additional imports other than those provided (if any)

code:
```python
{PROMPT}
```

ASSISTANT:
```python
"""

######

ALPACA_INPUT_TEMPLATE = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
Complete the following Python code: 
Notes: respond with the entire complete function definition
do not add any comments, be as concise in your code as possible
use only built-in libraries, assume no additional imports other than those provided (if any)

### Input:
{PROMPT}

### Response:
```python
"""

ALPACA_INPUT_TEMPLATE_MEDIUM = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
Please complete the following code.

### Input:
{PROMPT}

### Response:
```python
"""

ALPACA_INPUT_TEMPLATE_MD = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
Complete the following Python code: 
Notes: respond with the entire complete function definition
do not add any comments, be as concise in your code as possible
use only built-in libraries, assume no additional imports other than those provided (if any)

### Input:
```python
{PROMPT}
```

### Response:
```python
"""

######

ALPACA_TEMPLATE = """### Instruction:
Complete the following Python code: 
Notes: respond with the entire complete function definition
do not add any comments, be as concise in your code as possible
use only built-in libraries, assume no additional imports other than those provided (if any)

code:
{PROMPT}

### Response:
```python
"""


ALPACA_TEMPLATE_BAD_NL = """
### Instruction:
Complete the following Python code: 
Notes: respond with the entire complete function definition
do not add any comments, be as concise in your code as possible
use only built-in libraries, assume no additional imports other than those provided (if any)

code:
{PROMPT}

### Response:
```python
"""

ALPACA_TEMPLATE_MEDIUM = """### Instruction:
Please complete the following code:
{PROMPT}

### Response:
```python
"""

ALPACA_TEMPLATE_MD = """### Instruction:
Complete the following Python code: 
Notes: respond with the entire complete function definition
do not add any comments, be as concise in your code as possible
use only built-in libraries, assume no additional imports other than those provided (if any)

code:
```python
{PROMPT}
```

### Response:
```python
"""

ALPACA_TEMPLATE_MD_MEDIUM = """### Instruction:
Please complete the following code:
```python
{PROMPT}
```

### Response:
```python
"""

######