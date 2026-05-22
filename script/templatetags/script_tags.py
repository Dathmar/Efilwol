from django import template

register = template.Library()

# Maps damage_specialization value → Tailwind bg/text classes
TYPE_COLORS = {
    'physical':  'bg-stone-500 text-white',
    'lightning': 'bg-yellow-400 text-black',
    'fire':      'bg-orange-500 text-white',
    'ice':       'bg-cyan-400 text-black',
    'earth':     'bg-lime-600 text-white',
    'water':     'bg-blue-500 text-white',
    'poison':    'bg-purple-500 text-white',
    'necrotic':  'bg-gray-700 text-gray-200',
    'holy':      'bg-yellow-200 text-yellow-900',
    'dark':      'bg-indigo-900 text-indigo-200',
    'none':      'bg-base-300 text-base-content',
}


@register.filter
def type_color(damage_type):
    """Return Tailwind classes for a damage specialization type."""
    return TYPE_COLORS.get(damage_type, 'bg-base-300 text-base-content')
