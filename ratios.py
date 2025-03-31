from collections import defaultdict
from fractions import Fraction
from math import log2
from sympy import factorint
from termcolor import colored
from typing import Dict, List, Optional, Sequence, Set

'''
# TODO - adapt this code for my use case

from rich import print
import colorsys

def generate_rich_colors(base_hue, n, hue_range=0.05):
    """Generate n colors within a small hue range around base_hue."""
    return [
        "#{:02x}{:02x}{:02x}".format(
            *[int(c * 255) for c in colorsys.hls_to_rgb(
                base_hue + ((i / (n - 1)) * 2 - 1) * hue_range,  # Vary within a narrow band
                0.5,  # Keep lightness constant
                1     # Keep saturation high
            )]
        ) 
        for i in range(n)
    ]

# Base hue for magenta (0.83 in HSL) and generate 5 variations within a small hue range
base_hue_magenta = 0.83
colors = generate_rich_colors(base_hue_magenta, 5, hue_range=0.02)  # Limit hue variation

# Example fractions
fractions = ["7/4", "7/12", "21/12", "49/36", "35/24"]

# Print each fraction with a slightly different magenta shade
for frac, color in zip(fractions, colors):
    print(f"[{color}]{frac}[/{color}]")  # Uses hex color in rich
'''

# Mapping from prime limits to their display colors.
LIMIT_COLORS = {
	2: "dark_grey",
	3: "cyan",
	5: "green",
	7: "magenta",
	11: "red",
	13: "yellow"
}


"""
Given a list of ratios representing pitch 
classes which fit inside an octave and comprise
a scale, calculate all intervals in between them
and pretty print them somehow.
"""
def get_prime_limit(ratio: Fraction) -> Optional[int]:
	primes = factorint(ratio.numerator * ratio.denominator)
	if len(primes) == 0:
		return None
	else:
		return max(primes.keys())


def color_code_ratio(ratio: Fraction):
	limit = get_prime_limit(ratio)
	return LIMIT_COLORS.get(limit, "white")


# TODO - Decide how to color code ratios having the same
# limit *similarly*, yet assign *distinct* colors to every
# equivalence class of ratio (where ratios are identified
# up to octave equivalence i.e. differing only by a power of 2)
def classify_intervals(intervals: Sequence[Fraction]):
	equivalence_classes: Dict[Fraction, Set[Fraction]] = defaultdict(set)
	for interval in intervals:
		match = None

		for delegate, _ in equivalence_classes.items():
			cross_ratio = interval / delegate
			cross_limit = get_prime_limit(cross_ratio)
			# if interval is octave-equivalent to the delegate,
			# then add it to the associated members
			if (cross_limit or 2) == 2:
				match = delegate
				break

		equivalence_classes[(match or interval)].add(interval)


	return equivalence_classes


def get_intervals(pitch_ratios: List[Fraction]) -> List[List[Fraction]]:
	result = []
	for pitch in pitch_ratios:
		ratios_over = [
			over_pitch / pitch for over_pitch in pitch_ratios
		]
		result.append(ratios_over)
	return result

def show_fraction(fraction: Fraction, show_padding: bool = True) -> str:
	frac_str = f"{fraction.numerator}/{fraction.denominator}"
	return (f"{frac_str:>12}" if show_padding else frac_str)

def color_fraction(fraction: Fraction) -> str:
	attrs = ["bold"] if fraction > 1 else ["dark"]
	return colored(show_fraction(fraction), color_code_ratio(fraction), attrs=attrs)

def print_interval_series(series: List[Fraction], apply_coloring: bool = False) -> List[str]:
	interval_strs = [
		(color_fraction(interval) if apply_coloring else show_fraction(interval))
		for interval in series
	]
	return interval_strs

def print_cross_intervals(pitch_ratios: List[Fraction]):
	interval_serieses = get_intervals(pitch_ratios)
	header = [f"{'':>12}"] + print_interval_series(pitch_ratios)
	print(' '.join(header))
	for idx, series in enumerate(interval_serieses):
		print(
			f"{show_fraction(pitch_ratios[idx]):>12}" + "|" + ' '.join(print_interval_series(series, apply_coloring=True))
		)

pairs = [(1,1), (88,81), (12,11), (9,8), (32,27), (11,9), (4,3), (11,8), (16,11), (3,2), (18,11), (27,16), (16,9), (11,6), (81,44)]
ratios = [Fraction(n,d) for n,d in pairs]
