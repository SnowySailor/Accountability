"""
rename activity to description
"""

from yoyo import step

__depends__ = {'initial'}

steps = [
    step("ALTER TABLE activity RENAME activity TO description")
]
