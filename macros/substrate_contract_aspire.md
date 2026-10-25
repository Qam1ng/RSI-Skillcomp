# ASPIRE/cap-harness 底盘契约（实测规则，每次合成自动附带）

每条都有出处；改动需新测量。最后更新 2026-10-19。

## 沙箱语言规则

1. **异常机制可用**：`raise ValueError(...)`、`try/except` 实测正常执行
   （探针 exc_probe 2026-10-19；此前"无异常机制"系我方静态门白名单误伤，已更正）。
2. **`hasattr` 被禁**（NameError，exc_probe 实测）；`import` 被禁；内省类内置名不可假设存在。
3. **禁数组真值判断**：`if not points:` 对数组直接崩——用 `len(points) == 0`。
4. 只用 API 文档里的名字；**不得发明属性**。机器人状态字段：
   `state.end_effector_poses["primary"].position / .quaternion_wxyz / .frame`、
   `state.gripper_positions["primary"]`（标量）。

## 执行语义规则

5. **open_gripper 成功也可能报 ok=False**：松爪后以
   `get_robot_state().gripper_positions["primary"] > 0.03` 判定已释放
   （实测成功释放后读数 0.297），不要因 open_gripper 的 ok 判失败。
6. **成功即截断**：任务判定成功时 episode 截断，收尾撤臂的 move 可能无害地报 ok=False，
   不得影响函数返回值。
7. **几何一律运行时重算**（localize_object 起步），禁止硬编码场景坐标。
8. localize_object 失败时先用 `"the " + name` 重试一次再放弃。

## 抓取路线（底盘自带能力，2026-10-19 从官方 grasp.md 模板核实）

9. 首选学习型抓取建议器：
   `grasps = generate_grasps("agentview", loc.segmentation, backend="contact-graspnet")`
   → `grasp = select_grasp(grasps, strategy="top_down")`，`grasp.pose` 即抓取位姿。
   几何启发式（顶面/瓶颈）只做兜底。扁平物（盘子等）必须走建议器。

## 运维规则（跑批/跑单集）

10. 环境用 `.venv-libero`（直接调 `.venv-libero/bin/cap-harness`）；
    **不要 `uv run`**——它会新建最小 `.venv` 遮蔽真环境。
11. 必须带 `LIBERO_CONFIG_PATH=<repo>/.libero`，否则读到 `~/.libero/config.yaml`
    （外项目遗留，缺 bddl_files）全批报错。
12. 服务就绪探测用 `/openapi.json`，不是 `/health`。

13. **禁止下划线开头的名字**：程序含 `_x` 这类私有名会被整体拒绝
    （"program rejected: private and dunder names are not allowed"，2026-10-25 实测）。
