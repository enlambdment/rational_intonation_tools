from enum import Enum
from dataclasses import dataclass
from fractions import Fraction
from math import ceil, floor, log2
from sortedcontainers.sortedset import SortedSet
from typing import Dict, List, Optional, Sequence, Set, Tuple # some will be unused

from ratios import show_fraction # TODO - factor out
'''
Helper functions for typical mathematical operations
on fractions.
'''
def normalize(f: Fraction) -> Fraction:
	flog2 = log2(f)
	if flog2 < 0:
		return f * (2 ** (ceil(flog2) + 1))
	elif flog2 > 1:
		return f / (2 ** (floor(flog2)))
	else:
		return f

def to_cents(f: Fraction) -> int:
	return int(1200 * log2(f))

'''
In rational intonation systems, both pitch classes
(labelling equivalence sets of pitches, up to octave
equivalence) and intervals (distances between pitches)
are Fraction's. Aliasing to keep these concepts straight
and (hopefully) the code more human-readable
'''
Ratio = Tuple[int, int] | Fraction # is this helpful?

PitchClass = Ratio
Interval = Ratio

def to_fraction(ratio: Ratio) -> Fraction:
	match ratio:
		case tuple():
			# discard negative factors
			return Fraction(abs(ratio[0]), abs(ratio[1]))
		case Fraction():
			return ratio
		case _:
			raise Exception(f"Unexpected type {type(ratio)} for input {ratio}")
'''
Simple data type to represent a tuning procedure
as a directed graph.
'''
class Direction(Enum):
	UP = 1
	DOWN = 2

class TuningEdge:
	def __init__(self, interval: Interval, direction: Direction):
		self.interval = to_fraction(interval)
		self.direction = direction

	def __str__(self):
		edge_base = f"---{show_fraction(self.interval)}---"
		if self.direction == Direction.UP:
			return f"{edge_base}>"
		else:
			return f"<{edge_base}"

	def get_target_pitch_class(self, starting_pitch_class: PitchClass) -> PitchClass:
		starting_fraction = to_fraction(starting_pitch_class)

		match self.direction:
			case Direction.UP:
				return normalize(starting_fraction * self.interval)
			case Direction.DOWN:
				return normalize(starting_fraction / self.interval)
			case _:
				raise Exception(f"Unrecognized interval direction: {self.direction}")

TuningProcedure = Dict[PitchClass, Tuple[TuningEdge, PitchClass]]

@dataclass
class TuningProcedure:
	recipe: TuningProcedure

	def __str__(self):
		show_recipe = {str(pc): map(lambda edge_pc: (str(edge_pc[0]), str(edge_pc[1])), edge_pcs) for pc, edge_pcs in self.recipe.items()}
		return str(show_recipe)

class PitchCents:
	def __init__(self, pitch: PitchClass):
		fraction = to_fraction(pitch)
		self.pitch = fraction
		# don't keep decimal places
		self.cents = int(round(to_cents(fraction)))

	# it's convenient to be able to store the same value
	# in two different representations, but we still need
	# to tell Python how to compare instances
	def __lt__(self, other):
		return self.pitch < other.pitch

	def __str__(self):
		return f"{show_fraction(self.pitch)} ({self.cents}¢)"

'''
Class to represent a tuning system, which is what
we will call the series of pitch classes induced by
a particular "tuning recipe" (the data stored in the
backing structure.)

As an individual interval to tune is chosen and
added to the backing graph, then the newly generated
pitch class should be calculated (including octave
normalization.) 

We should only add the edge if applying its interval 
constructs a new pitch class for the tuning system.

Also, every time that we construct a new pitch class,
calculate its value in cents, for ease of evaluating
step sizes and comparing pitch classes (too close 
together? too far apart?) while a human in the loop
decides what choices to make. To support this kind of
interaction, the class should make it easy to "take
back" choices that don't lead to a favorable new
pitch class.

TODO - Refactor so that recipe can be read easily
at a glance (i.e. has a sensible `str` instance) -
maybe even create json export format?
'''
class TuningSystem:
	def __init__(self):
		fundamental = Fraction(1, 1)
		self.recipe: TuningProcedure = {fundamental: []}
		# for convenience, maintain sorted sequence of pitch classes?
		self.scale: Set[PitchCents] = SortedSet([PitchCents(fundamental)])

	def __str__(self):
		return '\t'.join(str(x) for x in self.scale)

	# separate calculation of new pitch class from committing change
	# to the tuning system - that way we can assess a change before
	# deciding to use the newly tuned pitch.
	def tune_interval(
		self,
		start: PitchClass, 
		interval: Interval, 
		direction: Direction = Direction.UP,
		check_neighbors: bool = False
	):
		start = to_fraction(start)
		interval = to_fraction(interval)

		if start not in self.recipe:
			raise Exception(f"Base pitch of {start} is absent from current pitches: {list(self.recipe.keys())}")
		
		edge_tuned = TuningEdge(interval, direction)
		pitch_tuned = edge_tuned.get_target_pitch_class(start)
		with_cents = PitchCents(pitch_tuned)

		if pitch_tuned in self.recipe:
			print(f"Pitch tuned of {pitch_tuned} is already present in the system, skipping.")
		else:
			extended_scale = self.scale.copy()
			extended_scale.add(with_cents)

			if check_neighbors:
				tuned_index = extended_scale.index(with_cents)
				tuned_slice = extended_scale.islice(
					max(tuned_index-1, 0), min(tuned_index+2, len(extended_scale))
				)
				tuned_with_neighbors = list(tuned_slice)
				report_pitches = '\t'.join(show_fraction(x.pitch) for x in tuned_with_neighbors)
				report_cents = '\t'.join(f"{x.cents:>10}¢" for x in tuned_with_neighbors)
				print('\n'.join([report_pitches, report_cents]))

				accept_extension = input("Extend scale with new pitch? ('y' to accept) ")
				if accept_extension != "y":
					return

			# add labelled edge and new node
			self.recipe[start].append((edge_tuned, pitch_tuned))
			self.recipe[pitch_tuned] = []
			self.scale = extended_scale

# e.g.
# ptolemy = TuningSystem()
# ptolemy.tune_interval((1,1), (3,2))
# ptolemy.tune_interval((3,2), (4,3))
# ptolemy.tune_interval((1,1), (7,4), check_neighbors=True)










