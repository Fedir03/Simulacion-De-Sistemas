"""Pruebas del formato y de los tiempos de una simulación por eventos."""
import math
import tempfile
from pathlib import Path
import unittest
from contextlib import nullcontext
from unittest.mock import patch

from animate import ARROW_REACH, render_animation

from simulation_io import parse_simulation

HEADER = 'format=tp3-v1 N=1 K=1 L=1.2 W=0.68 d=0.2\nobstacle 0.6 0.34 0.08\n'


def block(t, x, used=False, v=(1, 0)):
    return (f't={t} events={int(t)} Ng={int(used)} Fu={float(used)}\n'
            f'1 {x} 0.2 {v[0]} {v[1]} 0.0175 0.025 ' + ('255 0 0' if used else '0 0 255') + '\n')


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
                                             particle.get_facecolor()[:3], ax.get_title('left'),
                                             ax.get_title('right')))

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
                        for i, (actual, frame) in enumerate(zip(captured, data.frames)):
                            particle = frame.particles[0]
                            self.assertEqual(actual[:3], (particle[1:3], particle[3], particle[4]))
                            self.assertEqual(actual[3], f't = {frame.time:.3f} s · Partículas convertidas: {frame.goals}')
                            # Sin comentario final no hay t90: el último cuadro lo informa.
                            self.assertEqual(actual[4], 't90 no alcanzado' if i == len(data.frames) - 1 else '')

    def render_titles(self, data, **kwargs):
        """Títulos (izquierdo, derecho) de cada cuadro grabado en un GIF simulado."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        captured = []

        def capture():
            ax = plt.gcf().axes[0]
            captured.append((ax.get_title('left'), ax.get_title('right')))

        with tempfile.TemporaryDirectory() as directory, patch('matplotlib.animation.PillowWriter') as gif:
            gif.return_value.saving.return_value = nullcontext()
            gif.return_value.grab_frame.side_effect = capture
            render_animation(data, Path(directory) / 'animation.gif', progress=False, **kwargs)
        return captured

    def test_t90_is_read_from_final_comment(self):
        data = self.parse(HEADER + block(0, 0.1) + block(2, 0.5, True) + '# tf=2 outputEvery=1 events=2 Ng=1 t90=1.5 runtime=0.1\n')
        self.assertEqual(data.t90, 1.5)
        self.assertTrue(math.isnan(self.parse(HEADER + block(0, 0.1)).t90))

    def test_final_frame_holds_t90(self):
        data = self.parse(HEADER + block(0, 0.1) + block(2, 0.5, True) + block(3, 0.3, True) + '# tf=3 t90=1.5\n')
        titles = self.render_titles(data, fps=10, hold=0.5)
        # 3 cuadros más 0.5 s · 10 fps repeticiones del último; t90 solo en el último estado.
        self.assertEqual(len(titles), 3 + 5)
        self.assertEqual([right for _, right in titles[:2]], ['', ''])
        self.assertEqual(set(titles[2:]), {('t = 3.000 s · Partículas convertidas: 1', 't90 = 1.500 s')})

    def test_final_frame_without_t90(self):
        data = self.parse(HEADER + block(0, 0.1) + '# tf=0 t90=NaN\n')
        self.assertEqual(self.render_titles(data, fps=10, hold=0.2)[-1][1], 't90 no alcanzado')

    def test_parallel_render_holds_only_the_last_part(self):
        import animate

        data = self.parse(HEADER + block(0, 0.1) + block(1, 0.2) + block(2, 0.3) + block(3, 0.4) + '# tf=3 t90=2.5\n')
        calls = []

        class InlinePool:
            def __init__(self, jobs): pass
            def __enter__(self): return self
            def __exit__(self, *exc): return False
            def imap_unordered(self, function, tasks): return map(function, tasks)

        def fake_render(part, output, **kwargs):
            calls.append(([f.time for f in part.frames], part.t90, kwargs['hold'], kwargs['final']))

        with tempfile.TemporaryDirectory() as directory, \
                patch.object(animate, 'render_animation', side_effect=fake_render), \
                patch.object(animate.multiprocessing, 'get_context', return_value=type('Ctx', (), {'Pool': InlinePool})), \
                patch.object(animate.subprocess, 'run'):
            animate.render_parallel(data, Path(directory) / 'animation.mp4', jobs=2, hold=2.0)
        self.assertEqual(sorted(calls), [([0, 1], 2.5, 2.0, False), ([2, 3], 2.5, 2.0, True)])

    def test_velocity_is_parsed(self):
        data = self.parse(HEADER + block(0, 0.1, v=(0.6, -0.8)))
        self.assertEqual(data.frames[0].particles[0][5:7], (0.6, -0.8))

    def test_arrows_follow_particle_direction(self):
        # En cada cuadro el pico sale del centro, apunta según (vx, vy) y mide ARROW_REACH radios,
        # sin importar el módulo de la velocidad.
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        data = self.parse(HEADER + block(0, 0.1) + block(1, 0.5, v=(0, -2)) + block(2, 0.3, v=(-3, 4)))
        captured = []

        def capture():
            quiver = plt.gcf().axes[0].collections[-1]
            captured.append((tuple(quiver.get_offsets()[0]), float(quiver.U[0]), float(quiver.V[0])))

        with tempfile.TemporaryDirectory() as directory, patch('matplotlib.animation.PillowWriter') as gif:
            gif.return_value.saving.return_value = nullcontext()
            gif.return_value.grab_frame.side_effect = capture
            render_animation(data, Path(directory) / 'animation.gif', arrows=True, progress=False)

        reach = ARROW_REACH * 0.0175
        expected = [((0.1, 0.2), reach, 0), ((0.5, 0.2), 0, -reach), ((0.3, 0.2), -0.6 * reach, 0.8 * reach)]
        self.assertEqual(len(captured), len(expected))
        for (offset, u, v), (e_offset, e_u, e_v) in zip(captured, expected):
            for actual, wanted in zip((*offset, u, v), (*e_offset, e_u, e_v)):
                self.assertAlmostEqual(actual, wanted)

    def test_invalid_files(self):
        for text in (HEADER, HEADER + 't=0 events=0 Ng=0 Fu=0\n',
                     HEADER + block(2, 0.1) + block(1, 0.2),
                     HEADER + block(0, 'NaN'),
                     HEADER + block(0, 0.1) + block(1, 0.2).replace('1 0.2', '2 0.2')):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.parse(text)


if __name__ == '__main__':
    unittest.main()
