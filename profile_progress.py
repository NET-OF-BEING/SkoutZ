"""Helpers for deciding when visible SKOUT profile batches are exhausted."""


def unseen_profile_labels(profile_labels, messaged_profiles):
    """Return non-empty visible labels that have not been recorded yet."""
    return [
        label
        for label in profile_labels
        if label and label not in messaged_profiles
    ]


def visible_profiles_are_exhausted(profile_labels, messaged_profiles):
    """True when every non-empty visible profile label is already recorded."""
    return not unseen_profile_labels(profile_labels, messaged_profiles)
