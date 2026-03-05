"""
Pipeline signals module.

Reverse sync (sub-entity → pipeline auto-advance) has been removed.
Sub-entities now manage their own status independently. Pipeline transitions
are user-triggered and validated against sub-entity state.
"""
