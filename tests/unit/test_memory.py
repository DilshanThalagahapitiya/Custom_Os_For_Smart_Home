import unittest

from dilshan import memory

MEMINFO = """MemTotal:        2048000 kB
MemFree:          100000 kB
MemAvailable:     800000 kB
Buffers:           20000 kB
Cached:           500000 kB
SwapTotal:       1024000 kB
SwapFree:         900000 kB
"""


class MemoryTests(unittest.TestCase):
    def test_summary(self):
        s = memory.summarize(memory.parse_meminfo(MEMINFO))
        self.assertEqual(s.used, 1248000)
        self.assertEqual(s.cached, 520000)
        self.assertEqual(s.swap_used, 124000)

    def test_summary_without_swap(self):
        s = memory.summarize({"MemTotal": 100, "MemAvailable": 40})
        self.assertEqual(s.swap_used, 0)

    def test_pressure(self):
        text = ("some avg10=1.50 avg60=0.40 avg300=0.10 total=123\n"
                "full avg10=0.00 avg60=0.00 avg300=0.00 total=0\n")
        self.assertEqual(memory.parse_pressure(text)["some"]["avg10"], 1.5)

    def test_zram(self):
        z = memory.parse_zram_mm_stat("4096000 1024000 1100000 0 1100000 0 0 0")
        self.assertEqual(z.ratio, 4.0)
        self.assertEqual(z.memory_used, 1100000)

    def test_zram_empty_has_zero_ratio(self):
        self.assertEqual(memory.parse_zram_mm_stat("0 0 0 0 0 0 0 0").ratio, 0.0)

    def test_format_size(self):
        self.assertEqual(memory.format_size(512), "512.0 KiB")
        self.assertEqual(memory.format_size(2048), "2.0 MiB")


if __name__ == "__main__":
    unittest.main()
