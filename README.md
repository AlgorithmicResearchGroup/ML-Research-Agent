# Pretty Good Agent
> A pretty good agent that can perform a variety of tasks in the field of AI/ML.

## TODO:
- [ ] Count the number of tokens used to complete the task
- [X] Report the time taken to complete the task


### Run without Docker
```bash
python3 run.py --task_name mini_smoke_test --benchmark mini_benchmark --provider openai
```


### Build the Docker Image
```bash 
./manage_docker.sh build all-tasks mini_benchmark anthropic
./manage_docker.sh build all-tasks mini_benchmark openai
```

### Run the Agent
```bash


"llm_efficiency", "baby_lm", "mini_pile", "budget_model_training", "budget_inference", "llm_merging", "edge_llm_compression", "edge_llm_training", "math_reasoning_autoformalization", "math_reasoning_autoinformalization", "math_reasoning_autotheorem_generation", "math_reasoning_automated_problem_solving_with_code",  "smoke-test", " mini_llm_efficiency", "mini_baby_lm", "mini_mini_pile", "mini_budget_inference", "mini_llm_merging", "mini_math_reasoning", "mini_smoke_test"


./manage_docker.sh run all-tasks mini_benchmark anthropic 0 llm_efficiency
./manage_docker.sh run all-tasks mini_benchmark anthropic 0 baby_lm
./manage_docker.sh run all-tasks mini_benchmark anthropic 0 mini_pile
./manage_docker.sh run all-tasks mini_benchmark anthropic 0 budget_model_training
./manage_docker.sh run all-tasks mini_benchmark anthropic 0 budget_inference
./manage_docker.sh run all-tasks mini_benchmark anthropic 0 llm_merging
./manage_docker.sh run all-tasks mini_benchmark anthropic 0 math_reasoning_autoformalization
./manage_docker.sh run all-tasks mini_benchmark anthropic 0 math_reasoning_autotheorem_generation
./manage_docker.sh run all-tasks mini_benchmark anthropic 0 math_reasoning_automated_problem_solving_with_code
./manage_docker.sh run all-tasks mini_benchmark anthropic 0 smoke_test

./manage_docker.sh run all-tasks mini_benchmark anthropic 0 mini_llm_efficiency
./manage_docker.sh run all-tasks mini_benchmark anthropic 0 mini_baby_lm
./manage_docker.sh run all-tasks mini_benchmark anthropic 0 mini_mini_pile
./manage_docker.sh run all-tasks mini_benchmark anthropic 0 mini_budget_inference
./manage_docker.sh run all-tasks mini_benchmark anthropic 0 mini_llm_merging
./manage_docker.sh run all-tasks mini_benchmark anthropic 0 mini_math_reasoning
./manage_docker.sh run all-tasks mini_benchmark anthropic 0 mini_smoke_test


docker run -it --name my_container my-gpu-app:all-tasks_mini_benchmark_anthropic /bin/bash

./manage_docker.sh run all-tasks mini_benchmark openai 0 llm_efficiency
./manage_docker.sh run all-tasks mini_benchmark openai 0 baby_lm
./manage_docker.sh run all-tasks mini_benchmark openai 0 mini_pile
./manage_docker.sh run all-tasks mini_benchmark openai 0 budget_model_training
./manage_docker.sh run all-tasks mini_benchmark openai 0 budget_inference
./manage_docker.sh run all-tasks mini_benchmark openai 0 llm_merging
./manage_docker.sh run all-tasks mini_benchmark openai 0 math_reasoning_autoformalization
./manage_docker.sh run all-tasks mini_benchmark openai 0 math_reasoning_autotheorem_generation
./manage_docker.sh run all-tasks mini_benchmark openai 0 math_reasoning_automated_problem_solving_with_code
./manage_docker.sh run all-tasks mini_benchmark openai 0 smoke_test

./manage_docker.sh run all-tasks mini_benchmark openai 0 mini_llm_efficiency
./manage_docker.sh run all-tasks mini_benchmark openai 0 mini_baby_lm
./manage_docker.sh run all-tasks mini_benchmark openai 0 mini_mini_pile
./manage_docker.sh run all-tasks mini_benchmark openai 0 mini_budget_inference
./manage_docker.sh run all-tasks mini_benchmark openai 0 mini_llm_merging
./manage_docker.sh run all-tasks mini_benchmark openai 0 mini_math_reasoning
./manage_docker.sh run all-tasks mini_benchmark openai 0 mini_smoke_test


docker run -it --name my_container my-gpu-app:all-tasks_mini_benchmark_openai /bin/bash