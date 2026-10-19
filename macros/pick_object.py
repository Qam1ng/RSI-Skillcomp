def pick_object(object_name):
    """Pick an object by localizing it, descending to a grasp pose, closing the gripper, and lifting.

    PRE: The target object is visible in agentview and reachable by the robot arm.
    EFF: The target object is grasped by the gripper and lifted above its initial position.
    """
    loc = localize_object(object_name, camera_name="agentview")
    if not loc.ok:
        return {"ok": False, "stage": "localize_object"}

    points = loc.point_cloud.points
    if not points:
        return {"ok": False, "stage": "empty_point_cloud"}

    count = len(points)
    xs = sorted([float(p[0]) for p in points])
    ys = sorted([float(p[1]) for p in points])
    zs = sorted([float(p[2]) for p in points])

    cx = xs[count // 2]
    cy = ys[count // 2]
    top_z = zs[int(count * 0.95)]
    bottom_z = zs[int(count * 0.05)]

    state_before = get_robot_state()
    if not state_before.ok:
        return {"ok": False, "stage": "get_robot_state_pregrasp"}

    downward = state_before.end_effector_poses["primary"].quaternion_wxyz

    radii = [((float(p[0]) - cx) ** 2 + (float(p[1]) - cy) ** 2) ** 0.5 for p in points]
    radii.sort()
    rim_r = radii[int(count * 0.80)]

    if rim_r > 0.045:
        qw, qx, qy, qz = downward[0], downward[1], downward[2], downward[3]
        dir_x = 2.0 * (qx * qy - qw * qz)
        dir_y = 1.0 - 2.0 * (qx * qx + qz * qz)
        norm = (dir_x * dir_x + dir_y * dir_y) ** 0.5
        if norm > 1e-4:
            ux = dir_x / norm
            uy = dir_y / norm
        else:
            ux, uy = 0.0, 1.0

        cand1 = (cx + rim_r * ux, cy + rim_r * uy)
        cand2 = (cx - rim_r * ux, cy - rim_r * uy)
        grasp_x, grasp_y = cand1 if cand1[0] <= cand2[0] else cand2
        grasp_z = top_z - 0.015
    else:
        grasp_x = cx
        grasp_y = cy
        grasp_z = max(bottom_z + 0.02, top_z - 0.035)

    pregrasp = Pose(
        position=(grasp_x, grasp_y, max(top_z + 0.12, grasp_z + 0.12)),
        quaternion_wxyz=downward,
        frame="robot_base",
    )
    moved_pregrasp = move_to_pose(pregrasp, tolerance=0.025, max_steps=450)
    if not moved_pregrasp.ok:
        return {"ok": False, "stage": "move_to_pregrasp"}

    grasp_pose = Pose(
        position=(grasp_x, grasp_y, grasp_z),
        quaternion_wxyz=downward,
        frame="robot_base",
    )
    moved_grasp = move_to_pose(grasp_pose, tolerance=0.02, max_steps=350)
    if not moved_grasp.ok:
        return {"ok": False, "stage": "move_to_grasp"}

    closed = close_gripper()
    if not closed.ok:
        return {"ok": False, "stage": "close_gripper"}

    state_closed = get_robot_state()
    if not state_closed.ok:
        return {"ok": False, "stage": "get_robot_state_after_close"}

    state_lift = get_robot_state()
    if not state_lift.ok:
        return {"ok": False, "stage": "get_robot_state_lift"}

    held = state_lift.end_effector_poses["primary"]
    lift_pose = Pose(
        position=(held.position[0], held.position[1], held.position[2] + 0.15),
        quaternion_wxyz=held.quaternion_wxyz,
        frame=held.frame,
    )
    moved_lift = move_to_pose(lift_pose, tolerance=0.02, max_steps=350)
    if not moved_lift.ok:
        return {"ok": False, "stage": "move_to_lift"}

    return {
        "ok": True,
        "object_name": object_name,
        "grasp_pose": grasp_pose,
        "lift_pose": lift_pose,
    }
