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
- Simple tasks: ONE vla_act with the full task instruction is usually enough.
  Multi-stage tasks: call vla_act several times with sub-instructions, checking
  result.terminated after each call and stopping as soon as it is True.
- In VLA mode the geometric motion APIs (move_to_pose, plan_motion,
  execute_trajectory, step, move_to_joints) are UNAVAILABLE and will fail.
  Perception and state reads (localize_object, get_robot_state) remain usable
  for checks between vla_act calls.
- Record in `report`: each call's result.terminated and result.steps_executed.
