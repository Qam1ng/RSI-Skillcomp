def place_into(target_name, held_below_m=0.25):
    """
    PRE: The robot is holding an object and needs to place it into the specified target.
    EFF: The held object is released inside or on top of the target, and the gripper has retreated upwards.
    """
    target = localize_object(target_name, camera_name="agentview")
    if not target.ok:
        target = localize_object("the " + target_name, camera_name="agentview")
    if not target.ok:
        return {"ok": False, "stage": "localize_target"}

    pts = target.point_cloud.points
    if len(pts) == 0:
        return {"ok": False, "stage": "target_empty_points"}

    xs = sorted([float(p[0]) for p in pts])
    ys = sorted([float(p[1]) for p in pts])
    zs = sorted([float(p[2]) for p in pts])
    count = len(pts)

    target_center_x = xs[count // 2]
    target_center_y = ys[count // 2]
    target_top_z = zs[int(count * 0.95)]

    state = get_robot_state()
    held = state.end_effector_poses["primary"]
    above_z = target_top_z + held_below_m + 0.15
    if above_z < held.position[2]:
        above_z = held.position[2]

    above_pose = Pose(
        position=(target_center_x, target_center_y, above_z),
        quaternion_wxyz=held.quaternion_wxyz,
        frame=held.frame,
    )
    moved_above = move_to_pose(above_pose, tolerance=0.03, max_steps=450)
    if not moved_above.ok:
        return {"ok": False, "stage": "moved_above"}

    state = get_robot_state()
    held = state.end_effector_poses["primary"]
    place_z = target_top_z + held_below_m + 0.03
    if place_z > held.position[2]:
        place_z = held.position[2]

    place_pose = Pose(
        position=(target_center_x, target_center_y, place_z),
        quaternion_wxyz=held.quaternion_wxyz,
        frame=held.frame,
    )
    moved_place = move_to_pose(place_pose, tolerance=0.03, max_steps=350)
    if not moved_place.ok:
        return {"ok": False, "stage": "moved_place"}

    open_gripper()
    state = get_robot_state()
    gripper_width = state.gripper_positions["primary"]
    if gripper_width <= 0.03:
        return {"ok": False, "stage": "release_failed"}

    state = get_robot_state()
    current_ee = state.end_effector_poses["primary"]
    retreat_pose = Pose(
        position=(current_ee.position[0], current_ee.position[1], current_ee.position[2] + 0.12),
        quaternion_wxyz=current_ee.quaternion_wxyz,
        frame=current_ee.frame,
    )
    move_to_pose(retreat_pose, tolerance=0.03, max_steps=250)

    return {"ok": True, "target_top_z": target_top_z, "place_z": place_z}
