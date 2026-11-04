=== VLA SKILL (runtime-provided; this episode runs in VLA mode) ===
vla_act(prompt, max_steps=400, replan_steps=5) -> ExecutionResult
- Delegates low-level control to a pretrained manipulation policy.
- prompt: a short imperative English instruction for ONE manipulation subtask,
  e.g. "put the wine bottle in the bowl", "open the top drawer of the cabinet".
- The episode ends automatically when the benchmark judges the TASK complete;
  then result.terminated is True. Treat result.terminated as task success.
  result.ok is False whenever the episode ended (harness convention) - this is
  NOT an error; never retry after result.terminated is True.
- result.steps_executed = control steps consumed.
- RULE (pre-registered, measured): if the task is one the policy can plausibly
  do end-to-end, the correct program is EXACTLY ONE vla_act call carrying the
  VERBATIM task instruction. Never paraphrase or split such a task: the same
  policy scored 29/30 on full instructions vs 2/9 after planner decomposition
  (sub-prompts fall outside its training distribution). Reserve multiple
  vla_act calls for genuinely multi-stage tasks; then check result.terminated
  after each call and stop as soon as it is True.
- In VLA mode the geometric motion APIs (move_to_pose, plan_motion,
  execute_trajectory, step, move_to_joints) are UNAVAILABLE and will fail.
  Perception and state reads (localize_object, get_robot_state) remain usable
  for checks between vla_act calls.
- Record in `report`: each call's result.terminated and result.steps_executed.
