# openpi/π0.5 底盘契约（实测规则）

每条都有出处（2026-10-25/26 在 ucla 实测）；改动需新测量。
姐妹篇：`macros/substrate_contract_aspire.md`（ASPIRE 侧）。

## 安装与权重

1. **系统 `gsutil` 是同名假货**（不是 Google 的），openpi 下载器调它必炸。
   权重用匿名 gcsfs 拉：`gcsfs.GCSFileSystem(token="anon").get(src, dst, recursive=True)`。
2. **fsspec 递归下载会多嵌套一层目录**（`.../pi05_libero/pi05_libero/params`），
   服务端报 `_METADATA 不存在` 就是它——下载完把内层目录提上来。
3. **LIBERO 首次导入会交互式问路径**（EOFError 卡死后台任务）。
   预写 `$LIBERO_CONFIG_PATH/config.yaml` 绕过，五个字段都指向
   `openpi/third_party/libero/libero/libero`（benchmark_root / bddl_files /
   init_states / datasets / assets）。
4. 评测客户端环境是独立的 python3.8 venv（`examples/libero/.venv`），
   按 openpi README 的 no-docker 路径装；主环境 `uv sync` 与它互不相干。

## 运行拓扑（双 GPU 分工）

5. 服务端：`serve_policy.py policy:checkpoint --policy.config=pi05_libero
   --policy.dir=<ckpt>`，norm stats 自动从 checkpoint 的 assets 里读，
   起在 0.0.0.0:8000；GPU1 实测稳定（~15 GB 显存）。
6. 客户端：MUJOCO_GL=egl + PYOPENGL_PLATFORM=egl + EGL_PLATFORM=device，
   CUDA_VISIBLE_DEVICES 与 MUJOCO_EGL_DEVICE_ID 同指一张卡（GPU2），
   PYTHONPATH 加 third_party/libero，LIBERO_CONFIG_PATH 指向第 3 条的目录。
7. 推理协议：观测字典四键（observation/image、observation/wrist_image
   224×224×3 uint8、observation/state 8 维、prompt 文本），返回
   (10, 7) 动作块。`skillcomp.executors.VLAExecutor` 编码的就是这套。

## Gate 1 对照口径（官方，openpi README）

| 套件 | π0.5@30k 官方 | 我们首片（n=30，seed 7） |
|---|---|---|
| libero_spatial | 98.8 | 未跑 |
| libero_object | 98.2 | 未跑 |
| libero_goal | 98.0 | **96.7（29/30，期望 29.4——吻合）** |
| libero_10 | 92.4 | 未跑 |

全量认证 = 每任务 50 回合复刻整表。评测发射统一走
`skillcomp/vla_eval.py`，不再手敲。
