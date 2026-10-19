"""The deployment must also accept LXC hosts with equal card/render group IDs."""

import pathlib
import yaml


def test_device_groups_do_not_duplicate_on_lxc():
    compose = pathlib.Path("compose.yaml").read_text()
    compose = compose.replace("${RENDER_GID:?Set RENDER_GID}", "65534")
    compose = compose.replace("${VIDEO_GID:?Set VIDEO_GID}", "65534")
    for service in yaml.safe_load(compose)["services"].values():
        groups = service.get("group_add", [])
        assert len(groups) == len(set(groups))
