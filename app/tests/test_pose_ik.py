"""Hands and feet moved directly: two-bone IK back to the pose angles."""
import random
import sys
import unittest
from pathlib import Path

import numpy as np

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))


class ReachTests(unittest.TestCase):
    def setUp(self):
        from storyboard import pose
        self.pose = pose

    def joint(self, item, angles, name):
        return self.pose.world_joints(dict(item, poseAngles=angles), 0.0)[self.pose.JOINTS.index(name)]

    def test_reaches_what_the_pose_can_do(self):
        """Any wrist or ankle position a pose can produce is found again, whatever the character's
        place, turn, size, lean and twist (the solver goes through world -> body -> limb frames)."""
        pose = self.pose
        rng = random.Random(3)
        errors = []
        for _ in range(300):
            item = {'shape': rng.choice(['mannequin', 'capsule']), 'role': 'character',
                    'position': [rng.uniform(-3, 3), rng.uniform(0, 1), rng.uniform(-3, 3)],
                    'rotation': [0, rng.uniform(-180, 180), 0], 'scale': [0.5, rng.uniform(0.8, 1.9), 0.5]}
            base = dict(pose.params(rng.choice(['standing', 'pointing', 'arms raised'])),
                        twist=rng.uniform(-40, 40), lean=rng.uniform(-10, 30))
            joint = rng.choice(list(pose.REACHABLE))
            limb = pose.REACHABLE[joint]
            limits = pose.LIMITS[limb.split('_')[1]]
            goal = dict(base, **{limb: tuple(rng.uniform(lo + 5, hi - 5) for lo, hi in limits[:3]) + (0.0,)})
            target = self.joint(item, goal, joint)
            solved = pose.reach(item, base, joint, target)
            errors.append(np.linalg.norm(self.joint(item, solved, joint) - target))
            for other in pose.LIMBS_KEYS:
                if other != limb:
                    self.assertEqual(tuple(solved[other]), tuple(pose.clean_angles(base)[other]), 'one limb only')
        self.assertLess(max(errors), 1e-3)

    def test_out_of_reach_and_limits(self):
        pose = self.pose
        item = {'shape': 'mannequin', 'role': 'character', 'position': [0, 0, 0], 'rotation': [0, 0, 0],
                'scale': [1, 1, 1]}
        standing = pose.params('standing')
        shoulder = self.joint(item, standing, 'l_shoulder')
        far = shoulder + np.array([3.0, 0.0, 0.0])
        solved = pose.reach(item, standing, 'l_wrist', far)
        wrist = self.joint(item, solved, 'l_wrist')
        self.assertGreater(wrist[0], shoulder[0] + 0.5, 'stretched towards the point')
        self.assertLess(solved['l_arm'][2], 5.0, 'arm straight')
        behind = pose.reach(item, standing, 'r_wrist', self.joint(item, standing, 'r_shoulder') + [0, -0.2, -0.5])
        for value, (low, high) in zip(behind['r_arm'], pose.LIMITS['arm']):
            self.assertTrue(low <= value <= high)
        with self.assertRaises(ValueError):
            pose.reach(item, standing, 'nose', [0, 2, 0])

    def test_reach_keeps_the_turn_of_the_limb(self):
        pose = self.pose
        rng = random.Random(5)
        item = {'shape': 'mannequin', 'role': 'character', 'position': [1, 0, -2], 'rotation': [0, 35, 0],
                'scale': [1, 1, 1]}
        errors = []
        for _ in range(200):
            joint = rng.choice(list(pose.REACHABLE))
            limb = pose.REACHABLE[joint]
            limits = pose.LIMITS[limb.split('_')[1]]
            turn = rng.uniform(limits[3][0] + 5, limits[3][1] - 5)
            base = dict(pose.params('standing'), **{limb: (10.0, 20.0, 30.0, turn)})
            goal = dict(base, **{limb: tuple(rng.uniform(lo + 5, hi - 5) for lo, hi in limits[:3]) + (turn,)})
            target = self.joint(item, goal, joint)
            solved = pose.reach(item, base, joint, target)
            self.assertAlmostEqual(solved[limb][3], turn, places=6)
            errors.append(np.linalg.norm(self.joint(item, solved, joint) - target))
        self.assertLess(max(errors), 1e-3)

    def test_swivel_moves_the_elbow_and_keeps_the_hand(self):
        """Dragging an elbow or a knee turns the limb about the root-end line: the hand or the foot
        stays put and the elbow or knee lands where a pose with that turn would put it."""
        pose = self.pose
        rng = random.Random(7)
        worst_end, worst_middle = 0.0, 0.0
        tested = []
        for _ in range(200):
            item = {'shape': 'mannequin', 'role': 'character', 'position': [rng.uniform(-2, 2), 0, 0],
                    'rotation': [0, rng.uniform(-180, 180), 0], 'scale': [1, rng.uniform(0.8, 1.2), 1]}
            joint = rng.choice(['r_elbow', 'l_elbow', 'r_knee', 'l_knee'])
            limb = pose.HANDLES[joint][1]
            end = joint.replace('elbow', 'wrist').replace('knee', 'ankle')
            limits = pose.LIMITS[limb.split('_')[1]]
            angles = [rng.uniform(lo + 5, hi - 5) for lo, hi in limits]
            angles[0] = rng.uniform(0, 60)            # away from the straight-up singularity
            angles[2] = rng.uniform(40, 100)          # a bent limb: a straight one has no swivel
            goal = dict(pose.params('standing'), **{limb: tuple(angles)})
            before = self.joint(item, goal, end)
            # the same hand or foot, reached with the limb not turned about itself
            base = pose.reach(item, dict(goal, **{limb: tuple(angles[:3]) + (0.0,)}), end, before)
            if np.linalg.norm(self.joint(item, base, end) - before) > 1e-5:
                continue
            tested.append(joint)
            wanted = self.joint(item, goal, joint)
            solved = pose.swivel(item, base, joint, wanted)
            worst_end = max(worst_end, np.linalg.norm(self.joint(item, solved, end) - before))
            worst_middle = max(worst_middle, np.linalg.norm(self.joint(item, solved, joint) - wanted))
        standing = pose.params('standing')
        item = {'shape': 'mannequin', 'role': 'character', 'position': [0, 0, 0], 'rotation': [0, 0, 0],
                'scale': [1, 1, 1]}
        bent = dict(standing, r_arm=(20.0, 10.0, 90.0, 0.0))
        wrist = self.joint(item, bent, 'r_wrist')
        out = pose.swivel(item, bent, 'r_elbow', self.joint(item, bent, 'r_elbow') + [-1.0, 0, 0])
        self.assertLess(np.linalg.norm(self.joint(item, out, 'r_wrist') - wrist), 1e-3, 'hand kept')
        self.assertLess(self.joint(item, out, 'r_elbow')[0], self.joint(item, bent, 'r_elbow')[0], 'elbow out')
        with self.assertRaises(ValueError):
            pose.swivel(item, bent, 'r_wrist', [0, 1, 0])
        self.assertGreater(len(tested), 100)
        self.assertLess(worst_end, 1e-3)
        self.assertLess(worst_middle, 1e-3)

    def test_look(self):
        pose = self.pose
        item = {'shape': 'mannequin', 'role': 'character', 'position': [2, 0, 1], 'rotation': [0, 90, 0],
                'scale': [1, 1, 1]}
        standing = dict(pose.params('standing'), twist=20.0)
        for turn, tilt in ((0, 0), (30, 10), (-50, -20), (60, 25)):
            goal = dict(standing, head=(turn, tilt))
            point = pose.look_point(item, goal)
            solved = pose.look(item, standing, point)
            self.assertAlmostEqual(solved['head'][0], turn, places=3)
            self.assertAlmostEqual(solved['head'][1], tilt, places=3)
        behind = pose.look(item, standing, self.joint(item, standing, 'neck') + [-5.0, 0, 0])
        for value, (low, high) in zip(behind['head'], pose.LIMITS['head']):
            self.assertTrue(low <= value <= high)

    def test_three_angle_limbs_still_load(self):
        pose = self.pose
        old = dict(pose.params('standing'), r_arm=(10, 20, 30), l_leg=[5, 0, 10])
        clean = pose.clean_angles(old)
        self.assertEqual(clean['r_arm'], (10, 20, 30, 0.0))
        self.assertEqual(len(pose.blend(old, pose.params('pointing'), 0.5)['l_leg']), 4)
        a = pose.skeleton(clean)
        b = pose.skeleton(dict(clean, r_arm=(10, 20, 30, 0.0)))
        self.assertTrue(np.allclose(a, b))

    def test_shoulder_leans_the_upper_body(self):
        """Any shoulder position the upper body can take (lean, twist, side bend) is found again;
        the legs do not move."""
        pose = self.pose
        rng = random.Random(11)
        errors = []
        for _ in range(200):
            item = {'shape': 'mannequin', 'role': 'character', 'position': [rng.uniform(-2, 2), 0, rng.uniform(-2, 2)],
                    'rotation': [0, rng.uniform(-180, 180), 0], 'scale': [1, rng.uniform(0.8, 1.2), 1]}
            base = pose.params(rng.choice(['standing', 'sitting', 'pointing']))
            goal = dict(base, lean=rng.uniform(-30, 60), twist=rng.uniform(-60, 60), bend=rng.uniform(-30, 30))
            joint = rng.choice(['r_shoulder', 'l_shoulder'])
            target = self.joint(item, goal, joint)
            solved = pose.lean_to(item, base, joint, target)
            errors.append(np.linalg.norm(self.joint(item, solved, joint) - target))
            for limb in pose.LIMBS_KEYS:
                self.assertEqual(tuple(solved[limb]), tuple(base[limb]))
            for key in ('lean', 'twist', 'bend'):
                low, high = pose.LIMITS[key]
                self.assertTrue(low <= solved[key] <= high)
        self.assertLess(max(errors), 1e-3)
        item = {'shape': 'mannequin', 'role': 'character', 'position': [0, 0, 0], 'rotation': [0, 0, 0],
                'scale': [1, 1, 1]}
        standing = pose.params('standing')
        lower = pose.lean_to(item, standing, 'l_shoulder', self.joint(item, standing, 'l_shoulder') + [0, -0.12, 0])
        self.assertGreater(lower['bend'], 5, 'dropping the left shoulder bends the body to its left')
        with self.assertRaises(ValueError):
            pose.lean_to(item, standing, 'r_hip', [0, 1, 0])

    def test_hip_moves_the_pelvis_over_planted_feet(self):
        pose = self.pose
        rng = random.Random(13)
        worst_feet, worst_hip = 0.0, 0.0
        for _ in range(150):
            item = {'shape': 'mannequin', 'role': 'character', 'position': [rng.uniform(-2, 2), 0, rng.uniform(-2, 2)],
                    'rotation': [0, rng.uniform(-180, 180), 0], 'scale': [1, 1, 1]}
            base = dict(pose.params('standing'), r_leg=(10.0, 5.0, 20.0, 0.0), l_leg=(-5.0, 5.0, 15.0, 0.0))
            joint = 'pelvis'
            feet = [self.joint(item, base, a) for a in ('r_ankle', 'l_ankle')]
            hip = pose.handle_point(pose.world_joints(dict(item, poseAngles=base)), joint)
            target = hip + np.array([rng.uniform(-0.15, 0.15), rng.uniform(-0.25, 0.1), rng.uniform(-0.15, 0.15)])
            solved, shift = pose.shift_pelvis(item, base, target, joint)
            self.assertAlmostEqual(shift[1], 0.0)
            moved = dict(item, position=list(np.asarray(item['position'], float) + shift))
            for foot, name in zip(feet, ('r_ankle', 'l_ankle')):
                worst_feet = max(worst_feet, np.linalg.norm(self.joint(moved, solved, name) - foot))
            reached = pose.handle_point(pose.world_joints(dict(moved, poseAngles=solved)), joint)
            worst_hip = max(worst_hip, np.linalg.norm((reached - target)[[0, 2]]))
            self.assertLess(reached[1], target[1] + 1e-3, 'never above the handle')
        self.assertLess(worst_feet, 1e-3, 'the feet stay planted')
        self.assertLess(worst_hip, 1e-3, 'the hip follows the handle across')
        item = {'shape': 'mannequin', 'role': 'character', 'position': [0, 0, 0], 'rotation': [0, 0, 0],
                'scale': [1, 1, 1]}
        crouch, shift = pose.shift_pelvis(item, pose.params('standing'),
                                          self.joint(item, pose.params('standing'), 'l_hip') + [0, -0.2, 0], 'pelvis')
        self.assertAlmostEqual(self.joint(item, crouch, 'l_hip')[1],
                               self.joint(item, pose.params('standing'), 'l_hip')[1] - 0.2, places=4)
        self.assertGreater(crouch['r_leg'][2], 30, 'the knees bend')
        sitting = pose.params('sitting')
        higher, shift = pose.shift_pelvis(item, sitting, pose.handle_point(pose.world_joints(dict(item, poseAngles=sitting)), 'pelvis') + [0, 0.1, 0])
        self.assertAlmostEqual(higher['seat'], sitting['seat'] + 0.1, places=6)
        self.assertLess(np.linalg.norm(shift), 1e-9)

    def test_bend_is_optional_in_saved_poses(self):
        pose = self.pose
        old = {k: v for k, v in pose.params('standing').items() if k != 'bend'}
        self.assertEqual(pose.clean_angles(old)['bend'], 0.0)
        self.assertTrue(np.allclose(pose.skeleton(pose.clean_angles(old)), pose.skeleton(pose.params('standing'))))

    def test_neck_leans_without_turning(self):
        pose = self.pose
        rng = random.Random(17)
        errors = []
        for _ in range(200):
            item = {'shape': rng.choice(['mannequin', 'capsule']), 'role': 'character',
                    'position': [rng.uniform(-2, 2), 0.9, rng.uniform(-2, 2)],
                    'rotation': [0, rng.uniform(-180, 180), 0], 'scale': [1, rng.uniform(0.8, 1.9), 1]}
            base = dict(pose.params(rng.choice(['standing', 'sitting'])), twist=rng.uniform(-50, 50))
            goal = dict(base, lean=rng.uniform(-30, 70), bend=rng.uniform(-35, 35))
            target = self.joint(item, goal, 'neck')
            solved = pose.lean_to(item, base, 'neck', target)
            self.assertEqual(solved['twist'], base['twist'], 'the neck does not turn the body')
            errors.append(np.linalg.norm(self.joint(item, solved, 'neck') - target))
        self.assertLess(max(errors), 1e-3)

    def test_pelvis_handle_sits_between_the_hips(self):
        pose = self.pose
        item = {'shape': 'mannequin', 'role': 'character', 'position': [1, 0, 2], 'rotation': [0, 60, 0],
                'scale': [1, 1, 1]}
        standing = pose.params('standing')
        points = pose.world_joints(dict(item, poseAngles=standing))
        centre = pose.handle_point(points, 'pelvis')
        self.assertTrue(np.allclose(centre, (points[pose.JOINTS.index('r_hip')] + points[pose.JOINTS.index('l_hip')]) / 2))
        feet = [points[pose.JOINTS.index(a)] for a in ('r_ankle', 'l_ankle')]
        solved, shift = pose.shift_pelvis(item, standing, centre + [0.05, -0.15, 0.03], 'pelvis')
        moved = dict(item, position=list(np.asarray(item['position'], float) + shift))
        after = pose.world_joints(dict(moved, poseAngles=solved))
        for foot, name in zip(feet, ('r_ankle', 'l_ankle')):
            self.assertLess(np.linalg.norm(after[pose.JOINTS.index(name)] - foot), 1e-3)
        self.assertLess(np.linalg.norm(pose.handle_point(after, 'pelvis') - (centre + [0.05, -0.15, 0.03])), 1e-3)
        with self.assertRaises(ValueError):
            pose.shift_pelvis(item, standing, centre, 'neck')

    def test_hip_tilts_the_pelvis(self):
        """A hip handle tilts the pelvis about the other hip; the legs hang from it and are
        re-solved so that the feet stay put; the upper body keeps its angles (it may only move up
        or down with the pelvis)."""
        pose = self.pose
        rng = random.Random(19)
        worst_feet, worst_slope, count = 0.0, 0.0, 0
        for _ in range(150):
            item = {'shape': 'mannequin', 'role': 'character', 'position': [rng.uniform(-2, 2), 0, rng.uniform(-2, 2)],
                    'rotation': [0, 0, 0], 'scale': [1, rng.uniform(0.8, 1.2), 1]}
            base = dict(pose.params(rng.choice(['standing', 'sitting'])), tilt=rng.uniform(-5, 5))
            if base['seat'] is None and rng.random() < 0.5:
                base.update(r_leg=(5.0, 3.0, 25.0, 0.0), l_leg=(-5.0, 3.0, 25.0, 0.0))
            joint = rng.choice(['r_hip', 'l_hip'])
            other = 'l_hip' if joint == 'r_hip' else 'r_hip'
            target = self.joint(item, base, joint) + [0, rng.uniform(-0.03, 0.03), 0]
            feet = [self.joint(item, base, a) for a in ('r_ankle', 'l_ankle')]
            upper = [self.joint(item, base, a) for a in ('neck', 'r_shoulder', 'nose')]
            solved = pose.tilt_pelvis(item, base, joint, target)
            for foot, name in zip(feet, ('r_ankle', 'l_ankle')):
                worst_feet = max(worst_feet, np.linalg.norm(self.joint(item, solved, name) - foot))
            moves = [self.joint(item, solved, name) - point for point, name in zip(upper, ('neck', 'r_shoulder', 'nose'))]
            for move in moves:
                self.assertLess(np.linalg.norm(move[[0, 2]]), 1e-3, 'the upper body does not tilt')
                self.assertLess(np.linalg.norm(move - moves[0]), 1e-3)
            if abs(solved['tilt']) < pose.LIMITS['tilt'][1] - 1e-6:
                # the pelvis line points from the other hip towards the handle
                a, b = self.joint(item, solved, other), self.joint(item, solved, joint)
                wanted = target - self.joint(item, base, other)
                worst_slope = max(worst_slope, abs((b - a)[1] / (b - a)[0] - wanted[1] / wanted[0]))
                count += 1
        self.assertLess(worst_feet, 1e-3)
        self.assertLess(worst_slope, 1e-3)
        self.assertGreater(count, 100)
        item = {'shape': 'mannequin', 'role': 'character', 'position': [0, 0, 0], 'rotation': [0, 0, 0],
                'scale': [1, 1, 1]}
        standing = pose.params('standing')     # straight legs: raising a hip bends the other knee
        hiked = pose.tilt_pelvis(item, standing, 'r_hip', self.joint(item, standing, 'r_hip') + [0, 0.04, 0])
        self.assertLess(hiked['tilt'], -5)
        self.assertGreater(hiked['l_leg'][2], 5, 'the other knee bends')
        self.assertLess(self.joint(item, hiked, 'l_hip')[1], self.joint(item, standing, 'l_hip')[1] - 0.02)
        for name in ('r_ankle', 'l_ankle'):
            self.assertLess(np.linalg.norm(self.joint(item, hiked, name) - self.joint(item, standing, name)), 1e-3)
        bent = dict(standing, r_leg=(0.0, 0.0, 30.0, 0.0), l_leg=(0.0, 0.0, 30.0, 0.0))
        up = pose.tilt_pelvis(item, bent, 'l_hip', self.joint(item, bent, 'l_hip') + [0, 0.03, 0])
        self.assertGreater(up['tilt'], 5, 'raising the left hip tilts the pelvis to lift it')
        self.assertAlmostEqual(self.joint(item, up, 'r_hip')[1], self.joint(item, bent, 'r_hip')[1], places=3)
        self.assertGreater(self.joint(item, up, 'l_hip')[1], self.joint(item, bent, 'l_hip')[1] + 0.025)
        sitting = pose.params('sitting')
        seated = pose.tilt_pelvis(item, sitting, 'l_hip', self.joint(item, sitting, 'l_hip') + [0, 0.03, 0])
        self.assertGreater(seated['seat'], sitting['seat'], 'seated: the seat follows')
        extreme = pose.tilt_pelvis(item, bent, 'l_hip', self.joint(item, bent, 'l_hip') + [0, 2.0, 0])
        self.assertEqual(extreme['tilt'], pose.LIMITS['tilt'][1])
        with self.assertRaises(ValueError):
            pose.tilt_pelvis(item, bent, 'pelvis', [0, 1, 0])
        old = {k: v for k, v in pose.params('standing').items() if k != 'tilt'}
        self.assertEqual(pose.clean_angles(old)['tilt'], 0.0)

class HandTests(unittest.TestCase):
    def setUp(self):
        from storyboard import pose
        self.pose = pose
        self.item = {'shape': 'mannequin', 'role': 'character', 'position': [0.5, 0, -1], 'rotation': [0, 30, 0],
                     'scale': [1, 1, 1]}

    def tip(self, angles, side, finger):
        return self.pose.world_hands(dict(self.item, poseAngles=angles))[side][4 + 4 * self.pose.FINGERS.index(finger)]

    def test_hand_shape(self):
        pose = self.pose
        standing = pose.params('standing')
        _, hands = pose.skeleton(standing, 1.8, hands=True)
        self.assertEqual(hands['r'].shape, (21, 3))
        joints = pose.skeleton(standing)
        for side in 'rl':
            wrist = joints[pose.JOINTS.index(f'{side}_wrist')]
            self.assertTrue(np.allclose(hands[side][0], wrist))
            self.assertAlmostEqual(float(np.linalg.norm(hands[side][12] - wrist)), 0.19, delta=0.02, msg='hand length')
            self.assertLess(hands[side][12][1], wrist[1], 'hanging: the fingers point down')
        self.assertTrue(np.allclose(hands['l'][:, 0], -hands['r'][:, 0]) and np.allclose(hands['l'][:, 1:], hands['r'][:, 1:]),
                        'the hands mirror each other')
        fist = dict(standing, l_hand=(100.0, 100.0, 100.0, 100.0, 100.0, 0.0))
        _, closed = pose.skeleton(fist, 1.8, hands=True)
        wrist = closed['l'][0]
        for finger in range(1, 5):
            tip, base = closed['l'][4 + 4 * finger], closed['l'][1 + 4 * finger]
            self.assertLess(np.linalg.norm(tip - wrist), np.linalg.norm(hands['l'][4 + 4 * finger] - wrist) - 0.05, 'curled in')
            self.assertLess(tip[0], base[0], 'towards the palm (the left palm faces the body, -x)')
        self.assertLess(closed['l'][4][2] - hands['l'][4][2], 0, 'the thumb crosses in front of the palm')
        pointing = pose.params('pointing')
        _, pointed = pose.skeleton(pointing, 1.8, hands=True)
        wrist = pointed['r'][0]
        self.assertGreater(np.linalg.norm(pointed['r'][8] - wrist), np.linalg.norm(pointed['r'][12] - wrist) + 0.05,
                           'pointing: the index is out, the others are curled')

    def test_curl_handle(self):
        pose = self.pose
        rng = random.Random(23)
        worst = 0.0
        for _ in range(60):
            side = rng.choice('rl')
            finger = rng.choice(pose.FINGERS)
            index = pose.FINGERS.index(finger)
            base = pose.clean_angles(dict(pose.params(rng.choice(['standing', 'pointing', 'arms raised'])),
                                          **{f'{side}_hand': tuple(rng.uniform(0, 100) for _ in range(5))
                                             + (rng.uniform(0, 30), rng.uniform(-60, 70), rng.uniform(-20, 30))}))
            wanted = rng.uniform(0, 100)
            values = list(base[f'{side}_hand'])
            values[index] = wanted
            goal = dict(base, **{f'{side}_hand': tuple(values)})
            solved = pose.curl(self.item, base, f'{side}_{finger}', self.tip(goal, side, finger))
            worst = max(worst, float(np.linalg.norm(self.tip(solved, side, finger) - self.tip(goal, side, finger))))
            others = [v for i, v in enumerate(solved[f'{side}_hand']) if i != index]
            self.assertEqual(others, [v for i, v in enumerate(base[f'{side}_hand']) if i != index], 'one finger only')
            self.assertEqual(solved[f'{"l" if side == "r" else "r"}_hand'], base[f'{"l" if side == "r" else "r"}_hand'])
        self.assertLess(worst, 1e-3)
        with self.assertRaises(ValueError):
            pose.curl(self.item, pose.params('standing'), 'r_wrist', [0, 1, 0])

    def test_saved_poses_and_limits(self):
        pose = self.pose
        old = {k: v for k, v in pose.params('standing').items() if not k.endswith('_hand')}
        self.assertEqual(pose.clean_angles(old)['r_hand'], pose.REST['r_hand'])
        bounded = pose.clean_angles(dict(old, r_hand=(150, -5, 50, 50, 50, 90)))['r_hand']
        self.assertEqual(bounded, (100.0, 0.0, 50.0, 50.0, 50.0, 30.0, 0.0, 0.0), 'six values: the wrist is straight')
        with self.assertRaises(ValueError):
            pose.clean_angles(dict(old, r_hand=(1, 2, 3)))
        mid = pose.blend(pose.params('standing'), pose.params('pointing'), 0.5)
        self.assertAlmostEqual(mid['r_hand'][2], (15 + 95) / 2)

    def test_openpose_and_mannequin_hands(self):
        pose = self.pose
        from storyboard import render3d
        item = dict(self.item, poseAngles=pose.params('pointing'))
        hand = pose.world_hands(item)['r']
        centre = hand.mean(axis=0)
        close = {'position': list(centre + [0, 0.05, 0.45]), 'target': list(centre), 'fov': 50}
        far = {'position': list(centre + [0, 0.5, 12.0]), 'target': list(centre), 'fov': 50}
        with_hands = pose.draw([(item, 0.0)], close, (320, 240), hands=True)
        without = pose.draw([(item, 0.0)], close, (320, 240), hands=False)
        self.assertGreater(int((with_hands.max(axis=2) > 0).sum()), int((without.max(axis=2) > 0).sum()) + 200)
        self.assertTrue((with_hands[..., 2] == 255).any(), 'blue OpenPose hand points')
        tiny = pose.draw([(item, 0.0)], far, (320, 240), hands=True)
        self.assertTrue(np.array_equal(tiny, pose.draw([(item, 0.0)], far, (320, 240), hands=False)),
                        'too small on screen: no hand drawn')
        joints, hands = pose.skeleton(pose.params('pointing'), 1.8, hands=True)
        bare = render3d._posed_mannequin(joints)[0]
        full = render3d._posed_mannequin(joints, hands)[0]
        self.assertGreater(len(full), len(bare))

    def test_wrist_bend(self):
        pose = self.pose
        standing = pose.params('standing')
        _, straight = pose.skeleton(standing, 1.8, hands=True)
        flexed = dict(standing, l_hand=pose.REST['l_hand'][:6] + (60.0, 0.0))
        _, bent = pose.skeleton(flexed, 1.8, hands=True)
        self.assertTrue(np.allclose(bent['l'][0], straight['l'][0]), 'the wrist itself does not move')
        self.assertLess(bent['l'][9][0], straight['l'][9][0] - 0.05, 'the left hand bends towards its palm (-x)')
        towards_thumb = dict(standing, r_hand=pose.REST['r_hand'][:6] + (0.0, 30.0))
        _, deviated = pose.skeleton(towards_thumb, 1.8, hands=True)
        self.assertGreater(deviated['r'][9][2], straight['r'][9][2] + 0.03, 'towards the thumb: to the front when hanging')
        rng = random.Random(29)
        worst = 0.0
        for _ in range(80):
            side = rng.choice('rl')
            base = dict(pose.params(rng.choice(['standing', 'pointing', 'sitting'])), twist=rng.uniform(-30, 30))
            base = pose.clean_angles(base)
            values = list(base[f'{side}_hand'])
            values[6], values[7] = rng.uniform(-65, 75), rng.uniform(-20, 30)
            goal = dict(base, **{f'{side}_hand': tuple(values)})
            target = pose.world_hands(dict(self.item, poseAngles=goal))[side][9]
            solved = pose.bend_wrist(self.item, base, f'{side}_palm', target)
            reached = pose.world_hands(dict(self.item, poseAngles=solved))[side][9]
            worst = max(worst, float(np.linalg.norm(reached - target)))
            self.assertEqual(solved[f'{side}_hand'][:6], base[f'{side}_hand'][:6], 'the fingers keep their curl')
        self.assertLess(worst, 1e-3)
        far = pose.bend_wrist(self.item, standing, 'r_palm', [50.0, 0.0, 0.0])
        for value, (low, high) in zip(far['r_hand'][6:], pose.LIMITS['hand'][6:]):
            self.assertTrue(low <= value <= high)
        with self.assertRaises(ValueError):
            pose.bend_wrist(self.item, standing, 'r_index', [0, 1, 0])



class FootTests(unittest.TestCase):
    def setUp(self):
        from storyboard import pose
        self.pose = pose
        self.item = {'shape': 'mannequin', 'role': 'character', 'position': [0.5, 0, -1], 'rotation': [0, 30, 0],
                     'scale': [1, 1.1, 1]}

    def test_flat_feet_and_the_ground(self):
        pose = self.pose
        for name in ('standing', 'walking', 'crouching'):
            angles = pose.params(name, 0.7)
            joints, soles = pose.skeleton(angles, 1.8, feet=True)
            self.assertAlmostEqual(min(float(sole[1:, 1].min()) for sole in soles.values()), 0.0, places=9,
                                   msg=f'{name}: a sole on the ground')
            for side, sole in soles.items():
                self.assertTrue(np.allclose(sole[0], joints[pose.JOINTS.index(f'{side}_ankle')]))
                self.assertTrue(np.allclose(sole[1:, 1], sole[0, 1] - pose.ANKLE_HEIGHT), f'{name}: flat foot')
        standing = pose.params('standing')
        _, soles = pose.skeleton(standing, 1.8, feet=True)
        for sole in soles.values():
            self.assertGreater(sole[3][2], sole[2][2], 'the toes point forwards')
            self.assertLess(sole[1][2], sole[0][2], 'the heel is behind the ankle')
        turned = dict(standing, l_leg=(0.0, 0.0, 0.0, 40.0))
        _, soles = pose.skeleton(turned, 1.8, feet=True)
        toes = soles['l'][3] - soles['l'][0]
        self.assertGreater(toes[0], 0.05, 'a leg turned outwards turns its foot out')

    def test_tiptoe_lifts_the_body(self):
        pose = self.pose
        standing = pose.params('standing')
        tiptoe = dict(standing, r_foot=(50.0, 50.0), l_foot=(50.0, 50.0))
        low, high = pose.skeleton(standing), pose.skeleton(tiptoe)
        self.assertGreater(high[1][1], low[1][1] + 0.06, 'on tiptoe the whole body rises (about 8 cm)')
        _, soles = pose.skeleton(tiptoe, 1.8, feet=True)
        self.assertAlmostEqual(float(soles['r'][2][1]), 0.0, places=9, msg='standing on the balls of the feet')
        self.assertGreater(soles['r'][1][1], 0.1, 'heels up')
        old = {k: v for k, v in standing.items() if not k.endswith('_foot')}
        self.assertEqual(pose.clean_angles(old)['r_foot'], (0.0, 0.0))
        with self.assertRaises(ValueError):
            pose.clean_angles(dict(old, r_foot=(1, 2, 3)))

    def test_toe_handle(self):
        pose = self.pose
        rng = random.Random(31)
        worst = 0.0
        for _ in range(60):
            side = rng.choice('rl')
            base = pose.clean_angles(dict(pose.params(rng.choice(['standing', 'sitting', 'crouching'])),
                                          **{f'{side}_foot': (rng.uniform(-25, 55), rng.uniform(-35, 65))}))
            goal = dict(base, **{f'{side}_foot': (base[f'{side}_foot'][0], rng.uniform(-35, 65))})
            target = pose.world_feet(dict(self.item, poseAngles=goal))[side][3]
            solved = pose.bend_toes(self.item, base, f'{side}_toes', target)
            self.assertEqual(solved[f'{side}_foot'][0], base[f'{side}_foot'][0], 'the foot pitch is kept')
            reached = pose.world_feet(dict(self.item, poseAngles=solved))[side][3]
            worst = max(worst, float(np.linalg.norm(reached - target)))
        self.assertLess(worst, 1e-3)
        with self.assertRaises(ValueError):
            pose.bend_toes(self.item, pose.params('standing'), 'r_ankle', [0, 0, 0])

    def test_openpose_feet(self):
        pose = self.pose
        item = {'shape': 'mannequin', 'role': 'character', 'position': [0, 0, 0], 'rotation': [0, 0, 0],
                'scale': [1, 1, 1], 'poseAngles': pose.params('standing')}
        _, soles = pose.skeleton(item['poseAngles'], 1.8, feet=True)
        for side, sign in (('r', -1), ('l', 1)):
            big, small = soles[side][4], soles[side][5]
            self.assertLess(abs(big[0]), abs(small[0]), f'{side}: the big toe is on the inner side')
            self.assertGreater(big[2], soles[side][0][2] + 0.1, 'the toes are in front of the ankle')
            self.assertAlmostEqual(float(big[1]), 0.0, places=9, msg='on the ground')
        camera = {'position': [0.6, 0.6, 2.2], 'target': [0, 0.2, 0], 'fov': 45}
        size = (320, 320)
        with_feet = pose.draw([(item, 0.0)], camera, size, hands=False, feet=True)
        without = pose.draw([(item, 0.0)], camera, size, hands=False, feet=False)
        added = (with_feet != without).any(axis=2)
        self.assertGreater(int(added.sum()), 100)
        colours = {tuple(c) for c in with_feet[added].reshape(-1, 3)}
        self.assertIn((0, 0, 255), colours, 'left foot points: BODY_25 blue')
        self.assertIn((0, 255, 255), colours, 'right foot points: BODY_25 cyan')
        self.assertGreater(float(np.argwhere(added)[:, 0].mean()), size[1] * 0.6, 'at the bottom of the figure')

    def test_mannequin_feet(self):
        from storyboard import render3d
        pose = self.pose
        joints, hands, soles = pose.skeleton(pose.params('standing'), 1.8, hands=True, feet=True)
        vertices = render3d._posed_mannequin(joints, hands, soles)[0]
        self.assertGreater(float(vertices[:, 1].min()), -0.01, 'nothing under the ground')
        self.assertLess(float(vertices[:, 1].min()), 0.01, 'the soles touch it')


if __name__ == '__main__':
    unittest.main()
