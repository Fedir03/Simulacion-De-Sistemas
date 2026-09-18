"""Pruebas del formato y de los tiempos de una simulación por eventos."""
import tempfile
from pathlib import Path
import unittest
from contextlib import nullcontext
from unittest.mock import patch

from animate import render_animation

from simulation_io import parse_simulation

HEADER = 'format=tp3-v1 N=1 K=1 L=1.2 W=0.68 d=0.2\nobstacle 0.6 0.34 0.08\n'


def block(t, x, used=False):
    return (f't={t} events={int(t)} Ng={int(used)} Fu={float(used)}\n'
            f'1 {x} 0.2 1 0 0.0175 0.025 ' + ('255 0 0' if used else '0 0 255') + '\n')


class SimulationTests(unittest.TestCase):
    def parse(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'run.txt'
            path.write_text(text)
            return parse_simulation(path)

    def test_variable_times_and_color_at_event(self):
        data = self.parse(HEADER + block(0, 0.1) + block(2, 0.5, True) + block(3, 0.3, True))
        self.assertEqual([f.time for f in data.frames], [0, 2, 3])
        self.assertEqual([f.particles[0][1] for f in data.frames], [0.1, 0.5, 0.3])
        self.assertEqual([f.goals for f in data.frames], [0, 1, 1])

    def test_simultaneous_events_and_final_comment(self):
        data = self.parse(HEADER + block(0, 0.1) + block(0, 0.1, True) + block(1, 0.2, True)
                          + '# tf=1 t90=NaN\n')
        self.assertEqual([f.time for f in data.frames], [0, 0, 1])
        self.assertEqual([f.goals for f in data.frames], [0, 1, 1])

    def test_single_frame(self):
        data = self.parse(HEADER + block(0, 0.1))
        self.assertEqual(len(data.frames), 1)
        self.assertEqual(data.frames[0].particles[0][1:3], (0.1, 0.2))

    def test_render_uses_each_saved_state_once(self):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        trajectories = [
            HEADER + block(0, 0.1),
            HEADER + block(0, 0.1) + block(0.02, 0.5)
            + block(0.02, 0.5, True) + block(3, 0.3, True),
        ]
        for text in trajectories:
            data = self.parse(text)
            for suffix in ('.gif', '.mp4'):
                for speed in (0.5, 1, 2):
                    with self.subTest(frames=len(data.frames), suffix=suffix, speed=speed):
                        captured = []

                        def capture():
                            ax = plt.gcf().axes[0]
                            particle = ax.patches[-1]
                            captured.append((particle.center, particle.get_radius(),
                                             particle.get_facecolor()[:3], ax.get_title()))

                        with tempfile.TemporaryDirectory() as directory, \
                                patch('matplotlib.animation.PillowWriter') as gif, \
                                patch('matplotlib.animation.FFMpegWriter') as mp4:
                            writer = gif if suffix == '.gif' else mp4
                            writer.return_value.saving.return_value = nullcontext()
                            writer.return_value.grab_frame.side_effect = capture
                            render_animation(data, Path(directory) / ('animation' + suffix),
                                             fps=30, speed=speed)
                            self.assertEqual(writer.call_args.kwargs['fps'], 30 * speed)

                        self.assertEqual(len(captured), len(data.frames))
                        for actual, frame in zip(captured, data.frames):
                            particle = frame.particles[0]
                            self.assertEqual(actual[:3], (particle[1:3], particle[3], particle[4]))
                            self.assertIn(f't = {frame.time:.3f} s', actual[3])
                            self.assertIn(f'Goles: {frame.goals}/1', actual[3])
                            self.assertIn(f'Eventos: {frame.events}', actual[3])

    def test_invalid_files(self):
        for text in (HEADER, HEADER + 't=0 events=0 Ng=0 Fu=0\n',
                     HEADER + block(2, 0.1) + block(1, 0.2),
                     HEADER + block(0, 'NaN'),
                     HEADER + block(0, 0.1) + block(1, 0.2).replace('1 0.2', '2 0.2')):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.parse(text)


if __name__ == '__main__':
    unittest.main()
