from collections import defaultdict
from fractions import Fraction
from math import log2
from sympy import factorint
from termcolor import colored
from typing import Dict, List, Optional, Sequence, Set

from rich import print
import colorsys

def generate_rich_colors(base_hue: Optional[float], n, hue_range=0.2):
	"""Generate n colors within a small hue range around base_hue."""
	if base_hue is not None:
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
	else:
		return [
			"#{:02x}{:02x}{:02x}".format(
				# same, unvarying dark grey
				*[int(c * 255) for c in colorsys.hls_to_rgb(0.0, 0.3, 0.0)]
			)
			for _ in range(n) 
		]
		
'''
TODO: Instead of hardcoding a color assignment from prime limits to
certain hues, identify the prime limits used in the scale, then perform
a runtime mapping from thosen primes to the first n colors listed below.
That way, the base hues are well spread out visually in color space (as
this list order was originally contrived to accomplish) without having
to change things around in the source code.
'''

# Mapping from prime limits to their display colors.
LIMIT_COLORS = {
	2: "dark_grey",
	3: "blue",
	5: "yellow",
	7: "green",
	11: "red",
	13: "cyan",
	17: "orange",
	19: "magenta"
}

# Approximate HSL hue value for certain colors. 
# Note that gray has no hue (because saturation = 0).
COLORS_TO_HUES: dict[str, Optional[float]] = {
	"dark_grey": None,
	"red": 0.0,
	"orange": 0.083,
	"yellow": 0.167,
	"green": 0.333,
	"cyan": 0.5,
	"blue": 0.667,
	"magenta": 0.833,
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

def classify_intervals(intervals: Sequence[Fraction]) -> Dict[Fraction, Set[Fraction]]:
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

def rich_format_fraction(fraction: Fraction, color_str: Optional[str] = None, show_padding: bool = True) -> str:
	shown_fraction = show_fraction(fraction, show_padding)

	styles = []
	if color_str is not None:
		styles.append(color_str)
		strength = "bold" if fraction > 1 else "dim"
		styles.append(strength)
	else:
		styles.append("default") # the default color for use in printing header and row labels

	style_str = " ".join(styles)
	return f"[{style_str}]{shown_fraction}[/{style_str}]" # if len(styles) != 0 else shown_fraction

def rich_format_interval_series(series: List[Fraction], color_map: Dict[Fraction, str]):
	return " ".join(
		rich_format_fraction(fraction, color_map[fraction]) for fraction in series
	)

def assign_colors(
	classified_intervals: Dict[Fraction, Set[Fraction]], 
	classified_delegates: Dict[int, Set[Fraction]]
) -> Dict[Fraction, str]:
	interval_colors = dict()

	for prime_limit, delegates in classified_delegates.items():
		delegate_count = len(delegates)
		prime_hue = COLORS_TO_HUES[LIMIT_COLORS[prime_limit]]
		prime_colors = generate_rich_colors(prime_hue, delegate_count)
		# debug
		print(f"For prime {prime_limit}, generated colors {prime_colors}")

		delegate_colors = zip(delegates, prime_colors)
		for delegate, color in delegate_colors:
			matches = classified_intervals[delegate]
			for match in matches:
				interval_colors[match] = color

	return interval_colors


def print_cross_intervals(pitch_ratios: List[Fraction]):
	interval_serieses = get_intervals(pitch_ratios)
	header = [f"{'':>12}"] + [rich_format_fraction(f) for f in pitch_ratios]
	
	# flatten in order to classify all intervals present between pitch classes, up to octave equivalence
	classified_intervals = classify_intervals([intv for series in interval_serieses for intv in series])
	
	# now we have to group the delegates by prime limit, to decide how to split up color space upon print
	classified_delegates = defaultdict(set)
	for delegate, _ in classified_intervals.items():
		delegate_prime_limit = get_prime_limit(delegate)
		classified_delegates[(delegate_prime_limit or 2)].add(delegate)

	# we have to assign a color per each delegate of an octave-equivalent interval class
	# so check how many delegates share the same color code, then divide color space accordingly
	color_assignments = assign_colors(classified_intervals, classified_delegates)

	# debug
	print(color_assignments)

	print(' '.join(header))
	for idx, series in enumerate(interval_serieses):
		print(
			rich_format_fraction(pitch_ratios[idx]) + "|" + rich_format_interval_series(series, color_assignments)
		)

pairs = [(1,1), (88,81), (12,11), (9,8), (32,27), (11,9), (4,3), (11,8), (16,11), (3,2), (18,11), (27,16), (16,9), (11,6), (81,44)]
ratios = [Fraction(n,d) for n,d in pairs]

sample_scale = [Fraction(n,d) for n,d in [(1,1), (9,8), (297,256), (11,9), (4,3), (3,2), (99,64), (18,11), (16,9)]]
