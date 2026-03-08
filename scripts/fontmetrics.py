"""Shared font metrics helper for merge scripts."""


def lock_metrics(font):
    """Set vertical metrics to match the em square and prevent FontForge
    from recalculating them from glyph bounding boxes on generate().

    The *_add = False flags tell FontForge to use absolute values.
    """
    font.hhea_ascent = font.ascent
    font.hhea_ascent_add = False
    font.hhea_descent = -font.descent
    font.hhea_descent_add = False
    font.hhea_linegap = 0
    font.os2_typoascent = font.ascent
    font.os2_typoascent_add = False
    font.os2_typodescent = -font.descent
    font.os2_typodescent_add = False
    font.os2_typolinegap = 0
    font.os2_winascent = font.ascent
    font.os2_winascent_add = False
    font.os2_windescent = font.descent
    font.os2_windescent_add = False
    font.os2_use_typo_metrics = 1
