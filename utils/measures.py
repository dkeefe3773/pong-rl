from pint import UnitRegistry

# any module using pint should use this unit registry.  If modules create their own unit registries,
# unit comparisons between quantities made from different modules will fail.
ureg = UnitRegistry()

seconds_per_min = 60 * ureg.sec / ureg.minute
