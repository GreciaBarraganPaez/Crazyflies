import math
import colorsys
import unittest
from simulation.core.continuous_trajectories import motion, PERIODS
from simulation.visualization.formation_colors import ColorAnimator, ColorFrame, infer_frame, frame_colors
from simulation.controllers.heart_animation_bridge import heart_targets
from simulation.core.static_shapes import COUNT, HOME, targets


class FormationColorTests(unittest.TestCase):
    def test_heart_color_tracks_size_and_stays_red(self):
        previous=-1
        for scale in (.8,.9,1.,1.1,1.2):
            frame=infer_frame(heart_targets(scale))
            self.assertEqual(frame.shape,'heart')
            self.assertAlmostEqual(frame.scale,scale)
            colors=frame_colors(frame)
            self.assertEqual(len(set(colors)),1)
            r,g,b=colors[0]
            self.assertGreater(r,max(g,b))
            self.assertGreater(r+g+b,previous)
            previous=r+g+b

    def test_sine_phase_and_bright_crest_follow_actual_positions(self):
        for step in range(64):
            t=PERIODS['sine']*step/64
            points=tuple(s[0] for s in motion('sine',t))
            frame=infer_frame(points)
            self.assertEqual(frame.shape,'sine')
            error=math.remainder(frame.phase-2*math.pi*step/64,2*math.pi)
            self.assertAlmostEqual(error,0.,places=10)
            colors=frame_colors(frame)
            crest=max(range(COUNT),key=lambda i:points[i][2])
            self.assertAlmostEqual(max(colors[crest]),max(max(c) for c in colors))

    def test_wave_contains_full_rainbow(self):
        colors=frame_colors(ColorFrame('sine',phase=.17))
        hues={round(colorsys.rgb_to_hsv(*c)[0],2) for c in colors}
        self.assertGreaterEqual(len(hues),8)
        self.assertEqual({max(range(3),key=lambda i:c[i]) for c in colors},{0,1,2})

    def test_color_pattern_travels_in_the_same_direction_as_wave(self):
        order=sorted(range(COUNT),key=lambda i:targets('sine')[i][0])
        a=frame_colors(ColorFrame('sine',phase=0))
        b=frame_colors(ColorFrame('sine',phase=2*math.pi*.6/5.4))
        for left,right in zip(order,order[1:]):
            for x,y in zip(a[left],b[right]):self.assertAlmostEqual(x,y)

    def test_entry_ramps_are_fitted_without_independent_color_timer(self):
        for shape in PERIODS:
            for fraction in (.05,.25,.5,.9):
                points=tuple(s[0] for s in motion(shape,PERIODS[shape]*fraction,entry=True))
                frame=infer_frame(points)
                self.assertEqual(frame.shape,shape)
                self.assertLess(frame.error,1e-9)
                self.assertTrue(all(0<=v<=1 for c in frame_colors(frame) for v in c))

    def test_spiral_colors_follow_rotating_and_scaling_outline(self):
        for step in range(64):
            frame=infer_frame(tuple(s[0] for s in motion('spiral',PERIODS['spiral']*step/64)))
            self.assertEqual(frame.shape,'spiral')
            self.assertLess(frame.error,1e-9)

    def test_spiral_gradient_moves_without_global_brightness_pulse(self):
        small=frame_colors(ColorFrame('spiral',scale=.88,phase=.4))
        big=frame_colors(ColorFrame('spiral',scale=1.12,phase=.4))
        moved=frame_colors(ColorFrame('spiral',scale=1.12,phase=1.4))
        self.assertGreater(len(set(big)),10)
        self.assertNotEqual(big,moved)
        self.assertTrue(any(c[0]>c[2] and c[1]>.4 for c in big))
        self.assertTrue(any(c[2]>c[0] for c in big))
        self.assertEqual(small,big)
        for a,b in zip(frame_colors(ColorFrame('spiral',phase=0)),
                       frame_colors(ColorFrame('spiral',phase=2*math.pi))):
            for x,y in zip(a,b):self.assertAlmostEqual(x,y)

    def test_palettes_crossfade_and_recover_from_clock_reset(self):
        animator=ColorAnimator()
        before=animator.colors
        self.assertEqual(animator.update(heart_targets(1.2),10.),before)
        wanted=frame_colors(infer_frame(heart_targets(1.2)))
        middle=animator.update(heart_targets(1.2),10.3)
        self.assertNotEqual(middle,before)
        self.assertNotEqual(middle,wanted)
        self.assertEqual(animator.update(heart_targets(1.2),10.7),wanted)
        animator.update(heart_targets(.8),.1)
        expected=frame_colors(infer_frame(heart_targets(.8)))
        self.assertEqual(animator.update(heart_targets(.8),.8),expected)

    def test_grid_spiral_missing_and_invalid_feedback(self):
        self.assertEqual(infer_frame(HOME).shape,'grid')
        self.assertEqual(infer_frame(targets('spiral')).shape,'spiral')
        self.assertEqual(infer_frame(None).shape,'neutral')
        bad=list(HOME);bad[0]=(float('nan'),0,0)
        self.assertEqual(infer_frame(bad).shape,'neutral')
        animator=ColorAnimator()
        for points in (None,bad,targets('spiral'),HOME):
            colors=animator.update(points,1.)
            self.assertEqual(len(colors),COUNT)
            self.assertTrue(all(math.isfinite(v) and 0<=v<=1 for c in colors for v in c))

    def test_moon_fit_tracks_half_full_shape_and_palette(self):
        for step in range(65):
            frame=infer_frame(tuple(s[0] for s in motion('moon',PERIODS['moon']*step/64)))
            self.assertEqual(frame.shape,'moon')
            self.assertAlmostEqual(frame.scale,(1+math.cos(2*math.pi*step/64))/2)
            self.assertLess(frame.error,1e-9)
        full=frame_colors(infer_frame(targets('moon')))
        half=frame_colors(infer_frame(tuple(s[0] for s in motion('moon',PERIODS['moon']/2))))
        self.assertNotEqual(full,half)


if __name__=='__main__':unittest.main()
