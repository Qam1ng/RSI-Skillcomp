def pick_object(object_name):
    """
    PRE: The target object is visible in the scene and reachable by the robot.
    EFF: The target object is securely grasped and lifted above the workspace.
    """
    loc = localize_object(object_name, camera_name="agentview")
    if not loc.ok:
        return {"ok": False, "stage": "localize_object"}

    pts = loc.point_cloud.points
    count = len(pts)
    if count == 0:
        return {"ok": False, "stage": "empty_point_cloud"}

    xs = sorted([float(p[0]) for p in pts])
    ys = sorted([float(p[1]) for p in pts])
    zs = sorted([float(p[2]) for p in pts])

    z_top = zs[int(count * 0.98)]
    neck_pts = [p for p in pts if z_top - 0.05 <= p[2] <= z_top]

    if len(neck_pts) >= 8:
        neck_xs = sorted([float(p[0]) for p in neck_pts])
        neck_ys = sorted([float(p[1]) for p in neck_pts])
        grasp_x = neck_xs[len(neck_pts) // 2]
        grasp_y = neck_ys[len(neck_pts) // 2]
    else:
        grasp_x = xs[count // 2]
        grasp_y = ys[count // 2]

    grasp_z = z_top - 0.035

    state = get_robot_state()
    downward = state.end_effector_poses["primary"].quaternion_wxyz

    pregrasp = Pose(
        position=(grasp_x, grasp_y, z_top + 0.12),
        quaternion_wxyz=downward,
        frame="robot_base",
    )
    moved_pregrasp = move_to_pose(pregrasp, tolerance=0.025, max_steps=450)
    if not moved_pregrasp.ok:
        return {"ok": False, "stage": "pregrasp"}

    grasp_pose = Pose(
        position=(grasp_x, grasp_y, grasp_z),
        quaternion_wxyz=downward,
        frame="robot_base",
    )
    moved_grasp = move_to_pose(grasp_pose, tolerance=0.02, max_steps=350)
    if not moved_grasp.ok:
        return {"ok": False, "stage": "grasp"}

    closed = close_gripper()
    if not closed.ok:
        return {"ok": False, "stage": "close_gripper"}

    state_after = get_robot_state()
    gripper_pos = state_after.gripper_positions["primary"]

    state_held = get_robot_state()
    held = state_held.end_effector_poses["primary"]
    lift_pose = Pose(
        position=(held.position[0], held.position[1], held.position[2] + 0.15),
        quaternion_wxyz=held.quaternion_wxyz,
        frame=held.frame,
    )
    lifted = move_to_pose(lift_pose, tolerance=0.02, max_steps=150)
    if not lifted.ok:
        return {"ok": False, "stage": "lift"}

    return {
        "ok": True,
        "grasp_pose": grasp_pose,
        "lift_pose": lift_pose,
        "gripper_position": gripper_pos,
    }
