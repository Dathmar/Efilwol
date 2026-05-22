"""
script/combat.py — Shared combat utilities for the script attack system.

Provides:
  - TYPE_MATCHUPS: elemental type matchup table (23 entries)
  - weighted_choice(entries): weighted random selection from (action_id, weight) tuples
  - calculate_damage(action, attacker_dict, defender_dict): damage formula with crits and type matchups
  - effective_cast_time_ms(action, attacker_speed): cast time after speed reduction
"""

import random

# ---------------------------------------------------------------------------
# Type matchup table
# Key: (attack_type, defender_damage_specialization) → multiplier
# 23 entries as specified in Requirement 4.3
# ---------------------------------------------------------------------------
TYPE_MATCHUPS = {
    ('fire',      'ice'):       2.0,
    ('fire',      'fire'):      0.5,
    ('fire',      'water'):     0.5,
    ('ice',       'fire'):      2.0,
    ('ice',       'ice'):       0.5,
    ('ice',       'earth'):     1.5,
    ('lightning', 'water'):     2.0,
    ('lightning', 'earth'):     0.5,
    ('lightning', 'lightning'): 0.5,
    ('water',     'fire'):      1.5,
    ('water',     'lightning'): 0.5,
    ('water',     'water'):     0.5,
    ('earth',     'lightning'): 1.5,
    ('earth',     'earth'):     0.5,
    ('poison',    'earth'):     1.5,
    ('poison',    'poison'):    0.5,
    ('holy',      'dark'):      2.0,
    ('holy',      'necrotic'):  2.0,
    ('holy',      'holy'):      0.5,
    ('dark',      'holy'):      2.0,
    ('dark',      'dark'):      0.5,
    ('necrotic',  'holy'):      1.5,
    ('physical',  'physical'):  1.0,
}


def weighted_choice(entries):
    """
    Select one action_id from a list of (action_id, weight) tuples using
    weighted random selection.

    Args:
        entries: list of (action_id, weight) tuples. Weights must be positive.

    Returns:
        The selected action_id.

    Raises:
        ValueError: if entries is empty.
    """
    if not entries:
        raise ValueError("weighted_choice requires at least one entry.")

    total = sum(w for _, w in entries)
    r = random.uniform(0, total)
    cumulative = 0
    for action_id, weight in entries:
        cumulative += weight
        if r <= cumulative:
            return action_id
    # Fallback: return last entry (handles floating-point edge cases)
    return entries[-1][0]


def calculate_damage(action, attacker_dict, defender_dict):
    """
    Compute combat damage for a single attack.

    Args:
        action: an Action model instance with fields:
                  type (str), base_power (numeric)
        attacker_dict: dict with keys 'attack' (numeric), 'luck' (numeric)
        defender_dict: dict with keys 'defence' (numeric), 'resistance' (numeric),
                       'damage_specialization' (str)

    Returns:
        (final_damage, is_crit, type_multiplier)
          - final_damage (int): damage dealt, always ≥ 1
          - is_crit (bool): whether a critical hit occurred
          - type_multiplier (float): elemental multiplier applied
    """
    # Mitigation: physical attacks are reduced by defence, all others by resistance
    if action.type == 'physical':
        mitigation = float(defender_dict.get('defence', 0))
    else:
        mitigation = float(defender_dict.get('resistance', 0))

    base_damage = max(1, action.base_power + float(attacker_dict.get('attack', 0)) - mitigation)

    # Type matchup multiplier (defaults to 1.0 if no entry exists)
    type_multiplier = TYPE_MATCHUPS.get(
        (action.type, defender_dict.get('damage_specialization', '')),
        1.0,
    )

    # Critical hit: crit_chance = luck / 100
    crit_chance = float(attacker_dict.get('luck', 0)) / 100
    is_crit = random.random() < crit_chance
    crit_multiplier = 1.5 if is_crit else 1.0

    final_damage = max(1, round(base_damage * type_multiplier * crit_multiplier))
    return final_damage, is_crit, type_multiplier


def effective_cast_time_ms(action, attacker_speed):
    """
    Compute the effective cast time in milliseconds after applying speed reduction.

    Instant actions (is_instant=True) always return 0.
    Speed reduction is capped at 20% (reached at speed=10).

    Formula: round(cast_time_ms * (1 - min(0.20, speed / 50)))

    Args:
        action: an Action model instance with fields is_instant (bool), cast_time (numeric)
        attacker_speed: numeric speed stat of the attacker

    Returns:
        int: effective cast time in milliseconds (0 for instant actions)
    """
    if action.is_instant:
        return 0

    raw_ms = int(action.cast_time * 1000)
    reduction = min(0.20, float(attacker_speed) / 50)
    return round(raw_ms * (1 - reduction))
